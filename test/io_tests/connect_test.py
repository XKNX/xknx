"""Unit test for KNX/IP Connect Request/Response."""
import asyncio
import unittest
from unittest.mock import patch

from xknx import XKNX
from xknx.io import Connect, UDPClient
from xknx.knxip import (
    HPAI, ConnectRequestType, ConnectResponse, ErrorCode, KNXIPFrame,
    KNXIPServiceType)


class TestConnect(unittest.TestCase):
    """Test class for xknx/io/Connect objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_connect(self):
        """Test connecting from KNX bus."""
        xknx = XKNX(loop=self.loop)
        udp_client = UDPClient(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        connect = Connect(xknx, udp_client)
        connect.timeout_in_seconds = 0

        self.assertEqual(connect.awaited_response_class, ConnectResponse)

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame(xknx)
        exp_knxipframe.init(KNXIPServiceType.CONNECT_REQUEST)
        exp_knxipframe.body.control_endpoint = HPAI(
            ip_addr='192.168.1.3', port=4321)
        exp_knxipframe.body.data_endpoint = HPAI(
            ip_addr='192.168.1.3', port=4321)
        exp_knxipframe.body.request_type = ConnectRequestType.TUNNEL_CONNECTION
        exp_knxipframe.normalize()
        with patch('xknx.io.UDPClient.send') as mock_udp_send, \
                patch('xknx.io.UDPClient.getsockname') as mock_udp_getsockname:
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            self.loop.run_until_complete(asyncio.Task(connect.start()))
            mock_udp_send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame(xknx)
        wrong_knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_REQUEST)
        with patch('logging.Logger.warning') as mock_warning:
            connect.response_rec_callback(wrong_knxipframe, None)
            mock_warning.assert_called_with('Cant understand knxipframe')

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame(xknx)
        err_knxipframe.init(KNXIPServiceType.CONNECT_RESPONSE)
        err_knxipframe.body.status_code = ErrorCode.E_CONNECTION_ID
        with patch('logging.Logger.warning') as mock_warning:
            connect.response_rec_callback(err_knxipframe, None)
            mock_warning.assert_called_with("Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                                            type(connect).__name__,
                                            type(err_knxipframe.body).__name__, ErrorCode.E_CONNECTION_ID)

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame(xknx)
        res_knxipframe.init(KNXIPServiceType.CONNECT_RESPONSE)
        res_knxipframe.body.communication_channel = 23
        res_knxipframe.body.identifier = 7
        connect.response_rec_callback(res_knxipframe, None)
        self.assertTrue(connect.success)
        self.assertEqual(connect.communication_channel, 23)
        self.assertEqual(connect.identifier, 7)
