"""Unit test for KNX/IP Tunnelling Request/Response."""
import asyncio
import unittest
from unittest.mock import patch

from xknx import XKNX
from xknx.dpt import DPTArray
from xknx.io import Tunnelling, UDPClient
from xknx.knxip import ErrorCode, KNXIPFrame, KNXIPServiceType, TunnellingAck
from xknx.telegram import GroupAddress, PhysicalAddress, Telegram


class TestTunnelling(unittest.TestCase):
    """Test class for xknx/io/Tunnelling objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_tunnelling(self):
        """Test tunnelling from KNX bus."""
        # pylint: disable=too-many-locals
        xknx = XKNX(loop=self.loop)
        communication_channel_id = 23
        udp_client = UDPClient(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTArray((0x1, 0x2, 0x3)))
        sequence_counter = 42
        src_address = PhysicalAddress('2.2.2')
        tunnelling = Tunnelling(xknx, udp_client, telegram, src_address, sequence_counter, communication_channel_id)
        tunnelling.timeout_in_seconds = 0

        self.assertEqual(tunnelling.awaited_response_class, TunnellingAck)
        self.assertEqual(tunnelling.communication_channel_id, communication_channel_id)

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame(xknx)
        exp_knxipframe.init(KNXIPServiceType.TUNNELLING_REQUEST)
        exp_knxipframe.body.cemi.telegram = telegram
        exp_knxipframe.body.cemi.src_addr = src_address
        exp_knxipframe.body.communication_channel_id = communication_channel_id
        exp_knxipframe.body.sequence_counter = sequence_counter
        exp_knxipframe.normalize()
        print(exp_knxipframe)
        with patch('xknx.io.UDPClient.send') as mock_udp_send, \
                patch('xknx.io.UDPClient.getsockname') as mock_udp_getsockname:
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            self.loop.run_until_complete(asyncio.Task(tunnelling.start()))
            mock_udp_send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame(xknx)
        wrong_knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_REQUEST)
        with patch('logging.Logger.warning') as mock_warning:
            tunnelling.response_rec_callback(wrong_knxipframe, None)
            mock_warning.assert_called_with('Cant understand knxipframe')

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame(xknx)
        err_knxipframe.init(KNXIPServiceType.TUNNELLING_ACK)
        err_knxipframe.body.status_code = ErrorCode.E_CONNECTION_ID
        with patch('logging.Logger.warning') as mock_warning:
            tunnelling.response_rec_callback(err_knxipframe, None)
            mock_warning.assert_called_with("Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                                            type(tunnelling).__name__,
                                            type(err_knxipframe.body).__name__, ErrorCode.E_CONNECTION_ID)

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame(xknx)
        res_knxipframe.init(KNXIPServiceType.TUNNELLING_ACK)
        with patch('logging.Logger.debug') as mock_debug:
            tunnelling.response_rec_callback(res_knxipframe, None)
            mock_debug.assert_called_with('Success: received correct answer from KNX bus: %s', ErrorCode.E_NO_ERROR)
            self.assertTrue(tunnelling.success)
