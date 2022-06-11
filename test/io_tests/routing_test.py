"""Tests for KNX/IP routing connections."""
import asyncio
from unittest.mock import AsyncMock, call, patch

from xknx import XKNX
from xknx.io import Routing
from xknx.knxip import CEMIFrame
from xknx.telegram import Telegram, TelegramDirection


class TestRouting:
    """Test class for xknx/io/Routing objects."""

    def setup_method(self):
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.xknx = XKNX()
        self.tg_received_mock = AsyncMock()
        self.routing = Routing(
            self.xknx,
            self.tg_received_mock,
            local_ip="192.168.1.1",
        )

    @patch("xknx.io.Routing.send_telegram")
    async def test_request_received_callback(self, send_telegram_mock):
        """Test Tunnel for responding to L_DATA.req with confirmation and indication."""
        # L_Data.ind T_Connect from 1.0.250 to 1.0.255 (xknx tunnel endpoint)
        # communication_channel_id: 0x02   sequence_counter: 0x81
        raw_ind = bytes.fromhex("0610 0530 0010 2900b06010fa10ff0080")

        _cemi = CEMIFrame()
        _cemi.from_knx(raw_ind[6:])
        test_telegram = _cemi.telegram
        test_telegram.direction = TelegramDirection.INCOMING

        response_telegram = Telegram(source_address=self.xknx.own_address)

        async def tg_received_mock(telegram):
            """Mock for telegram_received_callback."""
            assert telegram == test_telegram
            return [response_telegram]

        self.routing.telegram_received_callback = tg_received_mock
        self.routing.udp_transport.data_received_callback(
            raw_ind, ("192.168.1.2", 3671)
        )
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert send_telegram_mock.call_args_list == [
            call(response_telegram),
        ]
