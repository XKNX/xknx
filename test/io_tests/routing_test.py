"""Tests for KNX/IP routing connections."""

import asyncio
from itertools import pairwise
from unittest.mock import AsyncMock, Mock, call, patch

from xknx import XKNX
from xknx.cemi import CEMIFrame, CEMILData, CEMIMessageCode
from xknx.io import Routing
from xknx.io.routing import (
    BUSY_DECREMENT_TIME,
    BUSY_INCREMENT_COOLDOWN,
    BUSY_RANDOM_TIME_FACTOR,
    BUSY_SLOWDURATION_TIME_FACTOR,
    ROUTING_INDICATION_WAIT_TIME,
    _RoutingFlowControl,
)
from xknx.knxip import KNXIPFrame, RoutingBusy, RoutingIndication
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, tpci

from ..conftest import EventLoopClockAdvancer


class TestRouting:
    """Test class for xknx/io/Routing objects."""

    def setup_method(self) -> None:
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.xknx = XKNX()
        self.cemi_received_mock = AsyncMock()

    @patch("xknx.io.Routing._send_knxipframe")
    async def test_request_received_callback(self, send_knxipframe_mock: Mock) -> None:
        """Test Routing for responding to a transport layer connection."""
        routing = Routing(
            self.xknx,
            individual_address=None,
            cemi_received_callback=self.xknx.knxip_interface.cemi_received,
            local_ip="192.168.1.1",
        )
        self.xknx.knxip_interface._interface = routing
        # set current address so management telegram is processed
        self.xknx.current_address = IndividualAddress("1.0.255")
        # L_Data.ind T_Connect from 1.0.250 to 1.0.255 (xknx tunnel endpoint)
        # communication_channel_id: 0x02   sequence_counter: 0x81
        raw_ind = bytes.fromhex("0610 0530 0010 2900b06010fa10ff0080")
        _cemi = CEMIFrame.from_knx(raw_ind[6:])
        test_telegram = _cemi.data.telegram()
        test_telegram.direction = TelegramDirection.INCOMING

        response_telegram = Telegram(
            destination_address=IndividualAddress(test_telegram.source_address),
            tpci=tpci.TDisconnect(),
        )
        response_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(
                telegram=response_telegram,
                src_addr=IndividualAddress("1.0.255"),
            ),
        )
        response_frame = KNXIPFrame.init_from_body(
            RoutingIndication(raw_cemi=response_cemi.to_knx())
        )

        routing.transport.data_received_callback(raw_ind, ("192.168.1.2", 3671))
        await asyncio.sleep(0)
        assert send_knxipframe_mock.call_args_list == [
            call(response_frame),
        ]
        await asyncio.sleep(0)  # await local L_Data.con

    @patch("logging.Logger.warning")
    async def test_routing_lost_message(self, logging_mock: Mock) -> None:
        """Test class for received RoutingLostMessage frames."""
        routing = Routing(
            self.xknx,
            individual_address=None,
            cemi_received_callback=AsyncMock(),
            local_ip="192.168.1.1",
        )
        raw = bytes((0x06, 0x10, 0x05, 0x31, 0x00, 0x0A, 0x04, 0x00, 0x00, 0x05))
        routing.transport.data_received_callback(raw, ("192.168.1.2", 3671))
        logging_mock.assert_called_once_with(
            "RoutingLostMessage received from %s - %s lost messages.",
            "192.168.1.2",
            5,
        )


class TestFlowControl:
    """Test class for KNXnet/IP routing flow control."""

    async def test_basic_throttling(self, time_travel: EventLoopClockAdvancer) -> None:
        """Test throttling outgoing frames."""
        flow_control = _RoutingFlowControl()
        mock = Mock()

        async def test_send() -> None:
            async with flow_control.throttle():
                mock()

        # first send is called immediately
        task = asyncio.create_task(test_send())
        await asyncio.sleep(0)
        assert mock.call_count == 1
        assert task.done()
        mock.reset_mock()

        # second send is throttled
        task = asyncio.create_task(test_send())
        await asyncio.sleep(0)
        assert mock.call_count == 0
        await time_travel(ROUTING_INDICATION_WAIT_TIME / 4)
        assert not task.done()
        await time_travel(ROUTING_INDICATION_WAIT_TIME / 4 * 3)
        assert task.done()
        assert mock.call_count == 1
        mock.reset_mock()

        # later send is called immediately
        await time_travel(ROUTING_INDICATION_WAIT_TIME)
        task = asyncio.create_task(test_send())
        await asyncio.sleep(0)
        assert mock.call_count == 1
        assert task.done()
        mock.reset_mock()

    async def test_throttling_serializes_concurrent_senders(
        self, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test concurrent senders are sent one after the other with the pause in between."""
        flow_control = _RoutingFlowControl()
        send_times: list[float] = []

        async def test_send() -> None:
            async with flow_control.throttle():
                send_times.append(flow_control._loop.time())

        # a frame was just sent
        await test_send()
        send_times.clear()
        # concurrent senders - eg. TelegramQueue and Management
        tasks = [asyncio.create_task(test_send()) for _ in range(3)]
        await asyncio.sleep(0)
        assert not send_times
        await time_travel(ROUTING_INDICATION_WAIT_TIME)
        assert len(send_times) == 1
        await time_travel(ROUTING_INDICATION_WAIT_TIME)
        assert len(send_times) == 2
        await time_travel(ROUTING_INDICATION_WAIT_TIME)
        assert len(send_times) == 3
        assert all(task.done() for task in tasks)
        assert all(
            later - earlier >= ROUTING_INDICATION_WAIT_TIME
            for earlier, later in pairwise(send_times)
        )

    @patch("random.random")
    async def test_routing_busy_no_burst(
        self, random_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test senders waiting for RoutingBusy don't send all at once afterwards."""
        flow_control = _RoutingFlowControl()
        mock = Mock()
        random_mock.return_value = 0.5

        async def test_send() -> None:
            async with flow_control.throttle():
                mock()

        flow_control.handle_routing_busy(RoutingBusy(wait_time=100))
        tasks = [asyncio.create_task(test_send()) for _ in range(2)]
        await asyncio.sleep(0)
        assert mock.call_count == 0
        # wait time and random extension for the first RoutingBusy frame
        await time_travel(0.1 + BUSY_RANDOM_TIME_FACTOR * random_mock())
        assert mock.call_count == 1
        await time_travel(ROUTING_INDICATION_WAIT_TIME)
        assert mock.call_count == 2
        assert all(task.done() for task in tasks)
        flow_control.cancel()

    @patch("random.random")
    async def test_routing_busy(
        self, random_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test throttling on received RoutingBusy frame."""
        flow_control = _RoutingFlowControl()
        mock = Mock()
        test_wait_time_ms = 100
        random_mock.return_value = 0.5

        async def test_send() -> None:
            async with flow_control.throttle():
                mock()

        test_busy = RoutingBusy(wait_time=test_wait_time_ms)

        # the first RoutingBusy frame counts
        flow_control.handle_routing_busy(test_busy)
        assert flow_control._received_busy_frames == 1
        task = asyncio.create_task(test_send())
        await asyncio.sleep(0)
        assert mock.call_count == 0
        await time_travel(test_wait_time_ms / 1000)
        assert mock.call_count == 0  # not yet resolved, wait for additional random time
        await time_travel(1 * BUSY_RANDOM_TIME_FACTOR * random_mock())
        assert mock.call_count == 1
        assert task.done()
        # slowduration for 1 RoutingBusy and decrement
        assert not flow_control._timer_task.done()
        await time_travel(1 * BUSY_SLOWDURATION_TIME_FACTOR)
        assert flow_control._received_busy_frames == 1
        await time_travel(BUSY_DECREMENT_TIME)
        assert flow_control._received_busy_frames == 0
        assert flow_control._timer_task.done()
        mock.reset_mock()

        # multiple RoutingBusy frames
        flow_control.handle_routing_busy(test_busy)
        assert flow_control._received_busy_frames == 1
        assert flow_control._wait_time_ms == test_wait_time_ms
        # doesn't count in same 10 ms window but updates wait time
        flow_control.handle_routing_busy(RoutingBusy(wait_time=test_wait_time_ms * 2))
        assert flow_control._received_busy_frames == 1
        assert flow_control._wait_time_ms == test_wait_time_ms * 2
        # counts after cooldown - lower wait time than remaining doesn't update wait time
        await time_travel(BUSY_INCREMENT_COOLDOWN)
        flow_control.handle_routing_busy(RoutingBusy(wait_time=test_wait_time_ms // 2))
        assert flow_control._received_busy_frames == 2
        assert flow_control._wait_time_ms == test_wait_time_ms * 2
        # counts after cooldown - higher wait time than remaining updates wait time
        await time_travel(BUSY_INCREMENT_COOLDOWN)
        flow_control.handle_routing_busy(RoutingBusy(wait_time=test_wait_time_ms * 3))
        assert flow_control._received_busy_frames == 3
        assert flow_control._wait_time_ms == test_wait_time_ms * 3

        task = asyncio.create_task(test_send())
        await asyncio.sleep(0)
        assert mock.call_count == 0
        await time_travel(test_wait_time_ms * 3 / 1000)
        assert mock.call_count == 0  # not yet resolved, wait for additional random time
        await time_travel(3 * BUSY_RANDOM_TIME_FACTOR * random_mock())
        assert mock.call_count == 1
        assert task.done()
        # slowduration
        assert not flow_control._timer_task.done()
        await time_travel(3 * BUSY_SLOWDURATION_TIME_FACTOR)
        assert flow_control._received_busy_frames == 3
        for remaining in (2, 1, 0):
            assert not flow_control._timer_task.done()
            await time_travel(BUSY_DECREMENT_TIME)
            assert flow_control._received_busy_frames == remaining
        assert flow_control._timer_task.done()
