"""Unit test for KNX/IP Disconnect Request/Response."""
import asyncio
import unittest
from unittest.mock import patch

from xknx import XKNX
from xknx.io import Disconnect, UDPClient
from xknx.knxip import (
    HPAI, DisconnectResponse, ErrorCode, KNXIPFrame, KNXIPServiceType)


class TestDisconnect(unittest.TestCase):
    """Test class for xknx/io/Disconnect objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_disconnect(self):
        """Test disconnecting from KNX bus."""
        xknx = XKNX(loop=self.loop)
        communication_channel_id = 23
        udp_client = UDPClient(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        disconnect = Disconnect(xknx, udp_client, communication_channel_id)
        disconnect.timeout_in_seconds = 0

        self.assertEqual(disconnect.awaited_response_class, DisconnectResponse)
        self.assertEqual(disconnect.communication_channel_id, communication_channel_id)

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame(xknx)
        exp_knxipframe.init(KNXIPServiceType.DISCONNECT_REQUEST)
        exp_knxipframe.body.communication_channel_id = communication_channel_id
        exp_knxipframe.body.control_endpoint = HPAI(
            ip_addr='192.168.1.3', port=4321)
        exp_knxipframe.normalize()
        with patch('xknx.io.UDPClient.send') as mock_udp_send, \
                patch('xknx.io.UDPClient.getsockname') as mock_udp_getsockname:
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            self.loop.run_until_complete(asyncio.Task(disconnect.start()))
            mock_udp_send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame(xknx)
        wrong_knxipframe.init(KNXIPServiceType.DISCONNECT_REQUEST)
        with patch('logging.Logger.warning') as mock_warning:
            disconnect.response_rec_callback(wrong_knxipframe, None)
            mock_warning.assert_called_with('Cant understand knxipframe')

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame(xknx)
        err_knxipframe.init(KNXIPServiceType.DISCONNECT_RESPONSE)
        err_knxipframe.body.status_code = ErrorCode.E_CONNECTION_ID
        with patch('logging.Logger.warning') as mock_warning:
            disconnect.response_rec_callback(err_knxipframe, None)
            mock_warning.assert_called_with("Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                                            type(disconnect).__name__,
                                            type(err_knxipframe.body).__name__, ErrorCode.E_CONNECTION_ID)

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame(xknx)
        res_knxipframe.init(KNXIPServiceType.DISCONNECT_RESPONSE)
        with patch('logging.Logger.debug') as mock_debug:
            disconnect.response_rec_callback(res_knxipframe, None)
            mock_debug.assert_called_with('Success: received correct answer from KNX bus: %s', ErrorCode.E_NO_ERROR)
            self.assertTrue(disconnect.success)
