"""Unit test for KNX/IP Tunnelling Request/Response."""
import asyncio
import unittest
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.io import Tunnel
from xknx.knxip import CEMIFrame
from xknx.telegram import TelegramDirection


class TestTunnelling(unittest.TestCase):
    """Test class for xknx/io/Tunnelling objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.xknx = XKNX()
        self.tg_received_mock = Mock()
        self.tunnel = Tunnel(
            self.xknx,
            local_ip="192.168.1.1",
            gateway_ip="192.168.1.2",
            gateway_port=3671,
            telegram_received_callback=self.tg_received_mock,
            auto_reconnect=False,
            auto_reconnect_wait=3,
        )

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    @patch("xknx.io.Tunnel._send_tunnelling_ack")
    def test_tunnel_request_received(self, send_ack_mock):
        """Test Tunnel for calling send_ack on normal frames."""
        # LDataInd GroupValueWrite from 1.1.22 to to 5/1/22 with DPT9 payload 0C 3F
        # communication_channel_id: 0x02   sequence_counter: 0x21
        raw = bytes.fromhex("0610 0420 0017 04 02 21 00 2900bcd011162916030080 0c 3f")
        _cemi = CEMIFrame(self.xknx)
        _cemi.from_knx(raw[10:])
        telegram = _cemi.telegram
        telegram.direction = TelegramDirection.INCOMING

        self.tunnel.udp_client.data_received_callback(raw)
        self.tg_received_mock.assert_called_once_with(telegram)
        send_ack_mock.assert_called_once_with(0x02, 0x21)

    @patch("xknx.io.Tunnel._send_tunnelling_ack")
    def test_tunnel_request_received_unsupported_frames(self, send_ack_mock):
        """Test Tunnel sending ACK for unsupported frames."""
        # LDataInd APciPhysAddrRead from 0.0.1 to 0/0/0 broadcast - ETS scan for devices in programming mode
        # <UnsupportedCEMIMessage description="APCI not supported: 0b0100000000 in CEMI: 2900b0d000010000010100" />
        # communication_channel_id: 0x02   sequence_counter: 0x4f
        raw = bytes.fromhex("0610 0420 0015 04 02 4f 00 2900b0d000010000010100")

        self.tunnel.udp_client.data_received_callback(raw)
        self.tg_received_mock.assert_not_called()
        send_ack_mock.assert_called_once_with(0x02, 0x4F)
        send_ack_mock.reset_mock()

        # LDataInd T_Connect from 1.0.250 to 1.0.255 (xknx tunnel endpoint) - ETS Line-Scan
        # <UnsupportedCEMIMessage description="CEMI too small. Length: 10; CEMI: 2900b06010fa10ff0080" />
        # communication_channel_id: 0x02   sequence_counter: 0x81
        raw = bytes.fromhex("0610 0420 0014 04 02 81 00 2900b06010fa10ff0080")

        self.tunnel.udp_client.data_received_callback(raw)
        self.tg_received_mock.assert_not_called()
        send_ack_mock.assert_called_once_with(0x02, 0x81)
