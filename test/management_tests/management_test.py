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
from xknx.management.management import (
    MANAGEMENT_ACK_TIMEOUT,
    MANAGEMENT_CONNECTION_TIMEOUT,
)
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


async def test_incoming_unnumbered_telegram_from_connected_device() -> None:
    """Test unnumbered telegrams are not handled by an open connection to their sender."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("4.0.10")
    # the device answering the broadcast is one we hold a connection with
    connection = await xknx.management.connect(individual_address)
    xknx.cemi_handler.send_telegram.reset_mock()

    address_response = Telegram(
        source_address=individual_address,
        destination_address=GroupAddress("0/0/0"),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataBroadcast(),
        payload=apci.IndividualAddressResponse(),
    )
    async with xknx.management.broadcast.context() as bc_context:
        xknx.management.process(address_response)
        await asyncio.sleep(0)
        assert bc_context.queue.get_nowait() == address_response
    # not acknowledged - it is not part of the point-to-point connection - and
    # not mistaken for its response either
    xknx.cemi_handler.send_telegram.assert_not_called()
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


_PROPERTY_WRITE = apci.PropertyValueWrite(
    object_index=1, property_id=5, count=1, start_index=1, data=bytes(10)
)
_PROPERTY_RESPONSE = apci.PropertyValueResponse(
    object_index=1, property_id=5, count=1, start_index=1, data=b"\x02"
)
# a second response to a memory read that was sent again after a lost ACK
_LATE_MEMORY_RESPONSE = apci.MemoryResponse(address=0x4003, data=bytes(10))


def _connected_telegram(
    source: IndividualAddress, control: tpci.TPCI, payload: apci.APCI | None = None
) -> Telegram:
    """Build an incoming telegram of a point-to-point connection."""
    return Telegram(
        source_address=source,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=control,
        payload=payload,
    )


async def test_p2p_request_skips_a_response_to_another_request() -> None:
    """Test that a request returns the response naming its Property, not a late one."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    conn = await xknx.management.connect(ia, rate_limit=0)

    task = asyncio.create_task(conn.request(_PROPERTY_WRITE))
    await asyncio.sleep(0)
    xknx.management.process(_connected_telegram(ia, tpci.TAck(0)))
    xknx.management.process(
        _connected_telegram(ia, tpci.TDataConnected(0), _LATE_MEMORY_RESPONSE)
    )
    await asyncio.sleep(0)
    # a response about another Property of the same object
    xknx.management.process(
        _connected_telegram(
            ia,
            tpci.TDataConnected(1),
            apci.PropertyValueResponse(object_index=1, property_id=6, start_index=1),
        )
    )
    await asyncio.sleep(0)
    assert not task.done()
    xknx.management.process(
        _connected_telegram(ia, tpci.TDataConnected(2), _PROPERTY_RESPONSE)
    )
    assert (await task).payload == _PROPERTY_RESPONSE


async def test_p2p_request_drops_a_response_received_before_it() -> None:
    """Test that a response that arrived while no request waited answers none."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    conn = await xknx.management.connect(ia, rate_limit=0)
    stale = apci.PropertyValueResponse(
        object_index=1, property_id=5, count=1, start_index=1, data=b"\x01"
    )
    xknx.management.process(_connected_telegram(ia, tpci.TDataConnected(0), stale))

    task = asyncio.create_task(conn.request(_PROPERTY_WRITE))
    await asyncio.sleep(0)
    xknx.management.process(_connected_telegram(ia, tpci.TAck(0)))
    await asyncio.sleep(0)
    assert not task.done()
    xknx.management.process(
        _connected_telegram(ia, tpci.TDataConnected(1), _PROPERTY_RESPONSE)
    )
    assert (await task).payload == _PROPERTY_RESPONSE


async def test_p2p_request_after_back_to_back_responses() -> None:
    """Test that a response right behind a skipped one is not lost."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    conn = await xknx.management.connect(ia, rate_limit=0)

    task = asyncio.create_task(conn.request(_PROPERTY_WRITE))
    await asyncio.sleep(0)
    xknx.management.process(_connected_telegram(ia, tpci.TAck(0)))
    # e.g. two frames of one TCP segment, handled before the request runs again
    xknx.management.process(
        _connected_telegram(ia, tpci.TDataConnected(0), _LATE_MEMORY_RESPONSE)
    )
    xknx.management.process(
        _connected_telegram(ia, tpci.TDataConnected(1), _PROPERTY_RESPONSE)
    )
    assert (await task).payload == _PROPERTY_RESPONSE
    assert not conn._response_waiter.done()


async def test_p2p_request_drops_all_responses_received_before_it() -> None:
    """Test that every response received while no request waited is dropped."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    conn = await xknx.management.connect(ia, rate_limit=0)
    xknx.management.process(
        _connected_telegram(ia, tpci.TDataConnected(0), _LATE_MEMORY_RESPONSE)
    )
    xknx.management.process(
        _connected_telegram(ia, tpci.TDataConnected(1), _PROPERTY_RESPONSE)
    )

    task = asyncio.create_task(conn.request(_PROPERTY_WRITE))
    await asyncio.sleep(0)
    xknx.management.process(_connected_telegram(ia, tpci.TAck(0)))
    await asyncio.sleep(0)
    assert not task.done()
    answer = apci.PropertyValueResponse(
        object_index=1, property_id=5, count=1, start_index=1, data=b"\x03"
    )
    xknx.management.process(_connected_telegram(ia, tpci.TDataConnected(2), answer))
    assert (await task).payload == answer


async def test_p2p_request_takes_a_response_during_the_ack_wait() -> None:
    """Test that a response arriving before the ACK of the request answers it."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    conn = await xknx.management.connect(ia, rate_limit=0)

    task = asyncio.create_task(conn.request(_PROPERTY_WRITE))
    await asyncio.sleep(0)
    xknx.management.process(
        _connected_telegram(ia, tpci.TDataConnected(0), _PROPERTY_RESPONSE)
    )
    xknx.management.process(_connected_telegram(ia, tpci.TAck(0)))
    assert (await task).payload == _PROPERTY_RESPONSE


async def test_p2p_request_times_out_without_its_response(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test that only other telegrams end the request with a timeout."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    conn = await xknx.management.connect(ia, rate_limit=0)

    task = asyncio.create_task(conn.request(_PROPERTY_WRITE))
    await asyncio.sleep(0)
    xknx.management.process(_connected_telegram(ia, tpci.TAck(0)))
    xknx.management.process(
        _connected_telegram(ia, tpci.TDataConnected(0), _LATE_MEMORY_RESPONSE)
    )
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)
    with pytest.raises(ManagementConnectionTimeout, match="PropertyValueResponse"):
        await task


async def test_p2p_request_without_response_type_returns_next_telegram() -> None:
    """Test that a payload without response type returns the next telegram."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    conn = await xknx.management.connect(ia, rate_limit=0)
    echo = apci.MemoryResponse(address=0x4000, data=b"\x01")

    task = asyncio.create_task(
        conn.request(apci.MemoryWrite(address=0x4000, data=b"\x01"))
    )
    await asyncio.sleep(0)
    xknx.management.process(_connected_telegram(ia, tpci.TAck(0)))
    xknx.management.process(_connected_telegram(ia, tpci.TDataConnected(0), echo))
    assert (await task).payload == echo


def _individual_telegram(
    payload: apci.APCI, source: IndividualAddress, destination: IndividualAddress
) -> Telegram:
    """Build an incoming T_Data_Individual telegram."""
    return Telegram(
        source_address=source,
        destination_address=destination,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataIndividual(),
        payload=payload,
    )


def _descriptor_response(
    xknx: XKNX, source: IndividualAddress, value: int = 0x07B0
) -> Telegram:
    """Build an incoming connectionless A_DeviceDescriptor_Response."""
    return _individual_telegram(
        apci.DeviceDescriptorResponse(descriptor=0, value=value),
        source,
        xknx.current_address,
    )


async def test_connectionless_request() -> None:
    """Test a connectionless request and its response."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    response = _descriptor_response(xknx, ia)

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        task = asyncio.create_task(
            connectionless.request(apci.DeviceDescriptorRead(descriptor=0))
        )
        await asyncio.sleep(0)
        assert xknx.cemi_handler.send_telegram.call_args_list == [
            call(
                Telegram(
                    source_address=xknx.current_address,
                    destination_address=ia,
                    tpci=tpci.TDataIndividual(),
                    payload=apci.DeviceDescriptorRead(descriptor=0),
                )
            )
        ]
        xknx.management.process(response)
        assert await task == response
    assert not xknx.management._connectionless


async def test_connectionless_request_skips_unrelated_telegrams() -> None:
    """Test that a request only returns the response it waits for."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    response = _descriptor_response(xknx, ia)

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        task = asyncio.create_task(
            connectionless.request(apci.DeviceDescriptorRead(descriptor=0))
        )
        await asyncio.sleep(0)
        # another service from the device
        xknx.management.process(
            _individual_telegram(apci.Restart(), ia, xknx.current_address)
        )
        # the expected service from another device
        xknx.management.process(_descriptor_response(xknx, IndividualAddress("4.0.2")))
        # a connected telegram from the device belongs to a connection
        xknx.management.process(
            Telegram(
                source_address=ia,
                destination_address=xknx.current_address,
                direction=TelegramDirection.INCOMING,
                tpci=tpci.TDataConnected(0),
                payload=response.payload,
            )
        )
        await asyncio.sleep(0)
        assert not task.done()
        xknx.management.process(response)
        assert await task == response


async def test_connectionless_request_skips_a_response_to_another_request() -> None:
    """Test that a response of the right service naming another Property is skipped."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    response = _individual_telegram(_PROPERTY_RESPONSE, ia, xknx.current_address)

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        task = asyncio.create_task(connectionless.request(_PROPERTY_WRITE))
        await asyncio.sleep(0)
        xknx.management.process(
            _individual_telegram(
                apci.PropertyValueResponse(
                    object_index=2, property_id=5, start_index=1
                ),
                ia,
                xknx.current_address,
            )
        )
        await asyncio.sleep(0)
        assert not task.done()
        xknx.management.process(response)
        assert await task == response


async def test_connectionless_request_without_response_type() -> None:
    """Test that a payload without response type returns the next telegram."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    response = _individual_telegram(apci.Restart(), ia, xknx.current_address)

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        task = asyncio.create_task(connectionless.request(apci.Restart()))
        await asyncio.sleep(0)
        xknx.management.process(response)
        assert await task == response


async def test_connectionless_request_discards_earlier_telegrams() -> None:
    """Test that a late response to an earlier request is not returned."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    response = _descriptor_response(xknx, ia)

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        xknx.management.process(_descriptor_response(xknx, ia, value=0x0010))
        task = asyncio.create_task(
            connectionless.request(apci.DeviceDescriptorRead(descriptor=0))
        )
        await asyncio.sleep(0)
        xknx.management.process(response)
        assert await task == response


async def test_connectionless_request_timeout(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test that a request without response times out."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        task = asyncio.create_task(
            connectionless.request(apci.DeviceDescriptorRead(descriptor=0))
        )
        await asyncio.sleep(0)
        await time_travel(MANAGEMENT_CONNECTION_TIMEOUT - 1)
        assert not task.done()
        await time_travel(1)
        with pytest.raises(ManagementConnectionTimeout):
            await task


async def test_connectionless_request_timeout_keyword(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test that a request waits for the given timeout."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        task = asyncio.create_task(
            connectionless.request(apci.DeviceDescriptorRead(descriptor=0), timeout=1)
        )
        await asyncio.sleep(0)
        await time_travel(0.9)
        assert not task.done()
        await time_travel(0.1)
        with pytest.raises(ManagementConnectionTimeout):
            await task


async def test_connectionless_receive(time_travel: EventLoopClockAdvancer) -> None:
    """Test that receive yields every expected response until the timeout."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    response_1 = _descriptor_response(xknx, ia, value=0x0001)
    response_2 = _descriptor_response(xknx, ia, value=0x0002)

    async def receive_all() -> list[Telegram]:
        return [
            telegram
            async for telegram in connectionless.receive(
                apci.DeviceDescriptorResponse, timeout=1
            )
        ]

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        await connectionless.send(apci.DeviceDescriptorRead(descriptor=0))
        task = asyncio.create_task(receive_all())
        await asyncio.sleep(0)
        xknx.management.process(response_1)
        xknx.management.process(
            _individual_telegram(apci.Restart(), ia, xknx.current_address)
        )
        xknx.management.process(response_2)
        await time_travel(0.9)
        assert not task.done()
        await time_travel(0.1)
        assert await task == [response_1, response_2]


async def test_connectionless_receive_any_telegram() -> None:
    """Test that receive without an APCI class yields any telegram of the device."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    restart = _individual_telegram(apci.Restart(), ia, xknx.current_address)

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        xknx.management.process(restart)
        async for telegram in connectionless.receive():
            assert telegram == restart
            break


async def test_connectionless_send_discards_earlier_telegrams() -> None:
    """Test that receive after send does not yield telegrams queued before."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    response = _descriptor_response(xknx, ia)

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        xknx.management.process(_descriptor_response(xknx, ia, value=0x0010))
        await connectionless.send(apci.DeviceDescriptorRead(descriptor=0))
        xknx.management.process(response)
        async for telegram in connectionless.receive(apci.DeviceDescriptorResponse):
            assert telegram == response
            break


async def test_connectionless_concurrent_requests() -> None:
    """Test that concurrent requests are sent one after the other."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    response_1 = _descriptor_response(xknx, ia, value=0x0001)
    response_2 = _descriptor_response(xknx, ia, value=0x0002)

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        task_1 = asyncio.create_task(
            connectionless.request(apci.DeviceDescriptorRead(descriptor=0))
        )
        task_2 = asyncio.create_task(
            connectionless.request(apci.DeviceDescriptorRead(descriptor=0))
        )
        await asyncio.sleep(0)
        # the second request waits for the response to the first one
        assert len(xknx.cemi_handler.send_telegram.call_args_list) == 1
        xknx.management.process(response_1)
        assert await task_1 == response_1
        await asyncio.sleep(0)
        assert len(xknx.cemi_handler.send_telegram.call_args_list) == 2
        assert not task_2.done()
        xknx.management.process(response_2)
        assert await task_2 == response_2


async def test_connectionless_alongside_connection() -> None:
    """Test a connectionless context and a connection to the same device."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    response = _descriptor_response(xknx, ia)
    connected_response = Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorResponse(descriptor=0, value=0x0010),
    )

    conn = await xknx.management.connect(ia)
    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        task = asyncio.create_task(
            connectionless.request(apci.DeviceDescriptorRead(descriptor=0))
        )
        await asyncio.sleep(0)
        xknx.management.process(connected_response)
        await asyncio.sleep(0)
        assert not task.done()
        assert conn._response_waiter.result() == connected_response
        xknx.management.process(response)
        assert await task == response
    await conn.disconnect()


async def test_connectionless_send_errors() -> None:
    """Test that send errors are raised as ManagementConnectionError."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")

    async with xknx.management.connectionless(ia) as connectionless:
        xknx.cemi_handler.send_telegram.side_effect = ConfirmationError("")
        with pytest.raises(ManagementConnectionError):
            await connectionless.send(apci.Restart())
        xknx.cemi_handler.send_telegram.side_effect = CommunicationError("")
        with pytest.raises(ManagementConnectionError):
            await connectionless.send(apci.Restart())


async def test_connectionless_one_context_per_device() -> None:
    """Test that a second context for the same device is refused."""
    xknx = XKNX()
    ia = IndividualAddress("4.0.1")

    async with xknx.management.connectionless(ia):
        with pytest.raises(ManagementConnectionError):
            async with xknx.management.connectionless(ia):
                pass
        async with xknx.management.connectionless(IndividualAddress("4.0.2")):
            assert len(xknx.management._connectionless) == 2
    assert not xknx.management._connectionless


async def test_connectionless_telegram_without_context_is_ignored() -> None:
    """Test that T_Data_Individual telegrams without an open context are dropped."""
    xknx = XKNX()
    ia = IndividualAddress("4.0.1")

    with patch("xknx.cemi.CEMIHandler.send_telegram") as send_telegram:
        xknx.cemi_handler.telegram_received(
            _individual_telegram(apci.Restart(), ia, xknx.current_address)
        )
        await asyncio.sleep(0)
        send_telegram.assert_not_called()


@pytest.mark.parametrize("rate_limit", [0, 1])
async def test_connectionless_rate_limit(
    time_travel: EventLoopClockAdvancer, rate_limit: int
) -> None:
    """Test rate limit for connectionless requests."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.1")
    response = _descriptor_response(xknx, ia)

    async with xknx.management.connectionless(ia, rate_limit) as connectionless:
        task = asyncio.create_task(
            connectionless.request(apci.DeviceDescriptorRead(descriptor=0))
        )
        await asyncio.sleep(0)
        xknx.management.process(response)
        await task
        xknx.cemi_handler.reset_mock()

        task = asyncio.create_task(
            connectionless.request(apci.DeviceDescriptorRead(descriptor=0))
        )
        await asyncio.sleep(0)
        if rate_limit:
            await time_travel(0.5 / rate_limit)
            # the request is still queued
            assert not xknx.cemi_handler.send_telegram.call_args_list
            await time_travel(0.5 / rate_limit)
        assert len(xknx.cemi_handler.send_telegram.call_args_list) == 1
        xknx.management.process(response)
        await task
