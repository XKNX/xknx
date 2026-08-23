"""Test management handling."""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, call, patch

import pytest

from xknx import XKNX
from xknx.exceptions import (
    CommunicationError,
    ConfirmationError,
    ManagementConnectionError,
    ManagementConnectionRefused,
    ManagementConnectionTimeout,
)
from xknx.management.management import MANAGEMENT_ACK_TIMEOUT
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDirection,
    apci,
    tpci,
)

from ..conftest import EventLoopClockAdvancer


async def test_connect() -> None:
    """Test establishing connections."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia_1 = IndividualAddress("4.0.1")
    ia_2 = IndividualAddress("4.0.2")

    def tg_connect(ia: IndividualAddress) -> Telegram:
        return Telegram(
            source_address=xknx.current_address,
            destination_address=ia,
            direction=TelegramDirection.OUTGOING,
            tpci=tpci.TConnect(),
        )

    def tg_disconnect(ia: IndividualAddress) -> Telegram:
        return Telegram(
            source_address=xknx.current_address,
            destination_address=ia,
            direction=TelegramDirection.OUTGOING,
            tpci=tpci.TDisconnect(),
        )

    await xknx.management.connect(ia_1)
    conn_2 = await xknx.management.connect(ia_2)

    with pytest.raises(ManagementConnectionError):
        # no 2 connections to the same IA
        await xknx.management.connect(ia_1)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(tg_connect(ia_1)),
        call(tg_connect(ia_2)),
    ]
    xknx.cemi_handler.send_telegram.reset_mock()

    await xknx.management.disconnect(ia_1)
    await conn_2.disconnect()

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(tg_disconnect(ia_1)),
        call(tg_disconnect(ia_2)),
    ]

    # connect again doesn't raise
    await xknx.management.connect(ia_1)


async def test_ack_timeout(time_travel: EventLoopClockAdvancer) -> None:
    """Test ACK timeout handling."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    _ia = IndividualAddress("4.0.1")

    conn = await xknx.management.connect(_ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    device_desc_read = Telegram(
        destination_address=_ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    task = asyncio.create_task(
        conn.request(payload=apci.DeviceDescriptorRead(descriptor=0))
    )
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(device_desc_read),
    ]
    await time_travel(MANAGEMENT_ACK_TIMEOUT)
    # telegram repeated
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(device_desc_read),
        call(device_desc_read),
    ]
    await time_travel(MANAGEMENT_ACK_TIMEOUT)
    with pytest.raises(ManagementConnectionTimeout):
        # still no ACK -> timeout
        await task

    await conn.disconnect()


async def test_failed_connect_disconnect() -> None:
    """Test failing connections."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia_1 = IndividualAddress("4.0.1")

    xknx.cemi_handler.send_telegram.side_effect = ConfirmationError("")
    with pytest.raises(ManagementConnectionError):
        await xknx.management.connect(ia_1)

    xknx.cemi_handler.send_telegram.side_effect = CommunicationError("")
    with pytest.raises(ManagementConnectionError):
        await xknx.management.connect(ia_1)

    xknx.cemi_handler.send_telegram.side_effect = None
    conn_1 = await xknx.management.connect(ia_1)
    xknx.cemi_handler.send_telegram.side_effect = ConfirmationError("")
    with pytest.raises(ManagementConnectionError):
        await xknx.management.disconnect(ia_1)

    xknx.cemi_handler.send_telegram.side_effect = None
    conn_1 = await xknx.management.connect(ia_1)
    xknx.cemi_handler.send_telegram.side_effect = CommunicationError("")
    with pytest.raises(ManagementConnectionError):
        await conn_1.disconnect()


async def test_send_on_disconnected_connection() -> None:
    """Test send_data and request raise once the connection is closed."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")

    conn = await xknx.management.connect(ia)
    await conn.disconnect()

    with pytest.raises(ManagementConnectionRefused):
        await conn.send_data(apci.Restart(), wait_for_ack=False)

    with pytest.raises(ManagementConnectionRefused):
        await conn.send_data(apci.Restart())

    with pytest.raises(ManagementConnectionRefused):
        await conn.request(payload=apci.DeviceDescriptorRead(descriptor=0))


async def test_reject_incoming_connection() -> None:
    """Test rejecting incoming transport connections."""
    # Note: incoming L_DATA.ind indication connection requests are rejected
    # L_DATA.req frames received from a tunnelling client are not yet supported
    xknx = XKNX()
    individual_address = IndividualAddress("4.0.10")

    connect = Telegram(
        source_address=individual_address,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TConnect(),
    )
    disconnect = Telegram(
        source_address=xknx.current_address,
        destination_address=individual_address,
        tpci=tpci.TDisconnect(),
    )
    with patch("xknx.cemi.CEMIHandler.send_telegram") as send_telegram:
        xknx.cemi_handler.telegram_received(connect)
        await asyncio.sleep(0)
        assert send_telegram.call_args_list == [call(disconnect)]


async def test_incoming_numbered_telegram_without_connection_is_ignored() -> None:
    """Test connected telegrams from devices we have no connection with are ignored."""
    xknx = XKNX()
    individual_address = IndividualAddress("4.0.10")

    device_desc_read = Telegram(
        source_address=individual_address,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    with patch("xknx.cemi.CEMIHandler.send_telegram") as send_telegram:
        xknx.cemi_handler.telegram_received(device_desc_read)
        await asyncio.sleep(0)
        # KNX v01.02.03 - Transport Layer 03.03.04 - §5.4: acknowledging is A2/A3,
        # neither of which the CLOSED state has - the telegram is not ours to ack
        send_telegram.assert_not_called()


async def test_incoming_sequence_numbers() -> None:
    """Test acknowledgement of in-sequence, repeated and out-of-window telegrams."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("4.0.10")
    connection = await xknx.management.connect(individual_address)
    xknx.cemi_handler.send_telegram.reset_mock()

    def incoming(sequence_number: int) -> Telegram:
        return Telegram(
            source_address=individual_address,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(sequence_number),
            payload=apci.DeviceDescriptorResponse(),
        )

    def outgoing(control: tpci.TPCI) -> Telegram:
        return Telegram(
            source_address=xknx.current_address,
            destination_address=individual_address,
            tpci=control,
        )

    # in sequence - acknowledged and handed to whoever waits for it
    xknx.management.process(incoming(0))
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(outgoing(tpci.TAck(0)))
    ]
    assert connection._response_waiter.done()

    # a repetition of it - acknowledged again, but not processed a second time
    connection._response_waiter = asyncio.get_event_loop().create_future()
    xknx.management.process(incoming(0))
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list[-1] == call(
        outgoing(tpci.TAck(0))
    )
    assert not connection._response_waiter.done()

    # neither the expected nor the previous one - not acknowledged
    xknx.management.process(incoming(7))
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list[-1] == call(
        outgoing(tpci.TNak(7))
    )
    assert not connection._response_waiter.done()


async def test_incoming_wrong_address() -> None:
    """Test incoming telegrams addressed to different devices."""
    xknx = XKNX()
    individual_address = IndividualAddress("4.0.10")
    other_address = IndividualAddress("4.0.11")
    assert xknx.current_address != other_address

    connect = Telegram(
        source_address=individual_address,
        destination_address=other_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TConnect(),
    )
    ack = Telegram(
        source_address=individual_address,
        destination_address=other_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    disconnect = Telegram(
        source_address=individual_address,
        destination_address=other_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDisconnect(),
    )
    with patch("xknx.cemi.CEMIHandler.send_telegram") as send_telegram:
        xknx.cemi_handler.telegram_received(connect)
        xknx.cemi_handler.telegram_received(ack)
        xknx.cemi_handler.telegram_received(disconnect)
        await asyncio.sleep(0)
        send_telegram.assert_not_called()


async def test_broadcast_message() -> None:
    """Test broadcast message sending."""
    xknx = XKNX()

    test_telegram = Telegram(
        source_address=IndividualAddress("0.0.0"),
        destination_address=GroupAddress("0/0/0"),
        direction=TelegramDirection.OUTGOING,
        tpci=tpci.TDataBroadcast(),
        payload=apci.IndividualAddressRead(),
    )
    with patch("xknx.cemi.CEMIHandler.send_telegram") as send_telegram:
        await xknx.management.broadcast.send(apci.IndividualAddressRead())
        assert send_telegram.call_args_list == [call(test_telegram)]


def _broadcast_telegram(payload: apci.APCI, source: str) -> Telegram:
    """Build an incoming broadcast telegram."""
    return Telegram(
        source_address=IndividualAddress(source),
        destination_address=GroupAddress("0/0/0"),
        tpci=tpci.TDataBroadcast(),
        payload=payload,
    )


def _mixed_broadcast_traffic() -> tuple[Telegram, tuple[Telegram, ...]]:
    """Return one IndividualAddressResponse and unrelated traffic around it."""
    expected = _broadcast_telegram(apci.IndividualAddressResponse(), "1.1.4")
    return expected, (
        # another service, from another device answering a different broadcast
        _broadcast_telegram(
            apci.IndividualAddressSerialResponse(
                serial=b"\x00" * 6, address=IndividualAddress("1.1.5")
            ),
            "1.1.5",
        ),
        # a request from a third party, not a response at all
        _broadcast_telegram(apci.IndividualAddressRead(), "1.1.6"),
        expected,
    )


async def test_broadcast_receive_filters_by_expected_apci(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test that receive() yields only telegrams carrying the expected APCI."""
    xknx = XKNX()
    _timeout = 2
    expected, traffic = _mixed_broadcast_traffic()

    async def collect() -> list[Telegram]:
        async with xknx.management.broadcast.context() as bc_context:
            return [
                telegram
                async for telegram in bc_context.receive(
                    apci.IndividualAddressResponse, timeout=_timeout
                )
            ]

    task = asyncio.create_task(collect())
    await asyncio.sleep(0)
    for telegram in traffic:
        xknx.management.process(telegram)
    await time_travel(_timeout)
    assert await task == [expected]


async def test_request_broadcast(time_travel: EventLoopClockAdvancer) -> None:
    """Test that Broadcast.request() manages the broadcast context itself."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    _timeout = 2
    expected, traffic = _mixed_broadcast_traffic()

    async def collect() -> list[Telegram]:
        return [
            telegram
            async for telegram in xknx.management.broadcast.request(
                apci.IndividualAddressRead(), timeout=_timeout
            )
        ]

    task = asyncio.create_task(collect())
    await asyncio.sleep(0)
    assert len(xknx.management.broadcast._contexts) == 1
    for telegram in traffic:
        xknx.management.process(telegram)
    await time_travel(_timeout)
    assert await task == [expected]
    assert not xknx.management.broadcast._contexts


async def test_request_broadcast_releases_context_on_early_exit() -> None:
    """Test that leaving the iteration early still closes the broadcast context."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    expected, _ = _mixed_broadcast_traffic()

    async def first_response() -> IndividualAddress | None:
        async for telegram in xknx.management.broadcast.request(
            apci.IndividualAddressRead(), timeout=None
        ):
            return telegram.source_address
        return None

    task = asyncio.create_task(first_response())
    await asyncio.sleep(0)
    assert len(xknx.management.broadcast._contexts) == 1
    xknx.management.process(expected)
    assert await task == expected.source_address
    await asyncio.sleep(0)
    assert not xknx.management.broadcast._contexts


async def test_broadcast_receive_unfiltered(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test that receive() without an APCI class yields the whole channel."""
    xknx = XKNX()
    _timeout = 2
    _, traffic = _mixed_broadcast_traffic()

    async def collect() -> list[Telegram]:
        async with xknx.management.broadcast.context() as bc_context:
            return [telegram async for telegram in bc_context.receive(timeout=_timeout)]

    task = asyncio.create_task(collect())
    await asyncio.sleep(0)
    for telegram in traffic:
        xknx.management.process(telegram)
    await time_travel(_timeout)
    assert await task == list(traffic)


async def test_request_broadcast_releases_context_when_cancelled() -> None:
    """Test that cancelling the consumer closes the broadcast context."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()

    async def consume() -> None:
        async for _ in xknx.management.broadcast.request(
            apci.IndividualAddressRead(), timeout=None
        ):
            pass

    task = asyncio.create_task(consume())
    await asyncio.sleep(0)
    assert len(xknx.management.broadcast._contexts) == 1
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    await asyncio.sleep(0)
    assert not xknx.management.broadcast._contexts


async def test_broadcast_timeout_does_not_outlive_the_loop(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test that leaving the loop early does not cancel the caller later on."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    _timeout = 2
    expected, _ = _mixed_broadcast_traffic()
    retained: list[AsyncGenerator[Telegram, None]] = []

    async def take_one_then_keep_working() -> str:
        generator = xknx.management.broadcast.request(
            apci.IndividualAddressRead(), timeout=_timeout
        )
        # retained, so leaving the loop does not finalize it right away - an
        # armed timeout would outlive the iteration and cancel this task
        retained.append(generator)
        async for _ in generator:
            break
        await asyncio.sleep(_timeout * 2)
        return "still running"

    task = asyncio.create_task(take_one_then_keep_working())
    await asyncio.sleep(0)
    xknx.management.process(expected)
    await time_travel(_timeout * 2)
    assert await task == "still running"


@pytest.mark.parametrize("rate_limit", [0, 1])
async def test_p2p_rate_limit(
    time_travel: EventLoopClockAdvancer, rate_limit: int
) -> None:
    """Test rate limit for P2P management connections."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")

    def send_responses(index: int) -> None:
        ack = Telegram(
            source_address=ia,
            destination_address=IndividualAddress(0),
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(index),
        )
        device_desc_resp = Telegram(
            source_address=ia,
            destination_address=IndividualAddress(0),
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(index),
            payload=apci.DeviceDescriptorResponse(),
        )

        xknx.management.process(ack)
        xknx.management.process(device_desc_resp)

    conn = await xknx.management.connect(ia, rate_limit)

    # create task and request data
    task = asyncio.create_task(
        conn.request(payload=apci.DeviceDescriptorRead(descriptor=0))
    )

    await asyncio.sleep(0)
    send_responses(0)

    await task

    xknx.cemi_handler.reset_mock()

    # create second task
    task = asyncio.create_task(
        conn.request(payload=apci.DeviceDescriptorRead(descriptor=0))
    )
    await asyncio.sleep(0)

    if rate_limit:
        await time_travel(0.5 / rate_limit)

        # the request is still queued
        assert not xknx.cemi_handler.send_telegram.call_args_list

        await time_travel(0.5 / rate_limit)

        # the requests should be sent now, the behaviour should match no rate limit

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(
            Telegram(
                destination_address=ia,
                tpci=tpci.TDataConnected(1),
                payload=apci.DeviceDescriptorRead(descriptor=0),
            )
        ),
    ]

    send_responses(1)

    await task
