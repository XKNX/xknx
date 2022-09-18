"""Tests for KNX/IP routing connections."""
import asyncio
from unittest.mock import AsyncMock, Mock, call, patch

from xknx import XKNX
from xknx.io import Routing
from xknx.io.routing import ROUTING_INDICATION_WAIT_TIME, _RoutingFlowControl
from xknx.knxip import CEMIFrame, KNXIPFrame, RoutingIndication
from xknx.telegram import Telegram, TelegramDirection, tpci


class TestRouting:
    """Test class for xknx/io/Routing objects."""

    def setup_method(self):
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.xknx = XKNX()
        self.tg_received_mock = AsyncMock()

    @patch("xknx.io.Routing._send_knxipframe")
    async def test_request_received_callback(self, send_knxipframe_mock):
        """Test Routing for responding to a transport layer connection."""
        routing = Routing(
            self.xknx,
            self.tg_received_mock,
            local_ip="192.168.1.1",
        )
        # L_Data.ind T_Connect from 1.0.250 to 1.0.255 (xknx tunnel endpoint)
        # communication_channel_id: 0x02   sequence_counter: 0x81
        raw_ind = bytes.fromhex("0610 0530 0010 2900b06010fa10ff0080")

        _cemi = CEMIFrame()
        _cemi.from_knx(raw_ind[6:])
        test_telegram = _cemi.telegram
        test_telegram.direction = TelegramDirection.INCOMING

        response_telegram = Telegram(tpci=tpci.TDisconnect())
        response_frame = KNXIPFrame.init_from_body(
            RoutingIndication(
                cemi=CEMIFrame.init_from_telegram(
                    telegram=response_telegram, src_addr=self.xknx.own_address
                )
            )
        )

        async def tg_received_mock(telegram):
            """Mock for telegram_received_callback."""
            assert telegram == test_telegram
            return [response_telegram]

        routing.telegram_received_callback = tg_received_mock
        routing.udp_transport.data_received_callback(raw_ind, ("192.168.1.2", 3671))
        await asyncio.sleep(0)
        assert send_knxipframe_mock.call_args_list == [
            call(response_frame),
        ]


class TestFlowControl:
    """Test class for KNXnet/IP routing flow control."""

    async def test_basic_throttling(self, time_travel):
        """Test throttling outgoing frames."""
        flow_control = _RoutingFlowControl()
        mock = Mock()

        async def test_send():
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
