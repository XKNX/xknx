"""Unit test for KNX/IP Connect Request/Response."""
from unittest.mock import patch

from xknx.io.request_response import Connect
from xknx.io.transport import UDPTransport
from xknx.knxip import (
    HPAI,
    ConnectionStateRequest,
    ConnectRequest,
    ConnectResponse,
    ConnectResponseData,
    ErrorCode,
    KNXIPFrame,
)
from xknx.telegram import IndividualAddress


class TestConnect:
    """Test class for xknx/io/Connect objects."""

    async def test_connect(self):
        """Test connecting from KNX bus."""
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        local_hpai = HPAI(ip_addr="192.168.1.3", port=4321)
        connect = Connect(udp_transport, local_hpai=local_hpai)
        connect.timeout_in_seconds = 0

        assert connect.awaited_response_class == ConnectResponse

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame.init_from_body(
            ConnectRequest(
                control_endpoint=local_hpai,
                data_endpoint=local_hpai,
            )
        )

        with patch("xknx.io.transport.UDPTransport.send") as mock_udp_send, patch(
            "xknx.io.transport.UDPTransport.getsockname"
        ) as mock_udp_getsockname:
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            await connect.start()
            mock_udp_send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame.init_from_body(ConnectionStateRequest())
        with patch("logging.Logger.warning") as mock_warning:
            connect.response_rec_callback(wrong_knxipframe, HPAI(), None)
            mock_warning.assert_called_with("Could not understand knxipframe")

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame.init_from_body(
            ConnectResponse(status_code=ErrorCode.E_CONNECTION_ID)
        )
        with patch("logging.Logger.debug") as mock_warning:
            connect.response_rec_callback(err_knxipframe, HPAI(), None)
            mock_warning.assert_called_with(
                "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                type(connect).__name__,
                type(err_knxipframe.body).__name__,
                ErrorCode.E_CONNECTION_ID,
            )

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame.init_from_body(
            ConnectResponse(
                communication_channel=23,
                crd=ConnectResponseData(individual_address=IndividualAddress(7)),
            )
        )
        connect.response_rec_callback(res_knxipframe, HPAI(), None)
        assert connect.success
        assert connect.communication_channel == 23
        assert connect.crd.individual_address.raw == 7

    async def test_connect_route_back_true(self):
        """Test connecting from KNX bus."""
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        local_hpai = HPAI()  # route_back: No IP address, no port, UDP
        connect = Connect(udp_transport, local_hpai=local_hpai)
        connect.timeout_in_seconds = 0

        assert connect.awaited_response_class == ConnectResponse

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame.init_from_body(ConnectRequest())
        with patch("xknx.io.transport.UDPTransport.send") as mock_udp_send, patch(
            "xknx.io.transport.UDPTransport.getsockname"
        ) as mock_udp_getsockname:
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            await connect.start()
            mock_udp_send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame.init_from_body(ConnectionStateRequest())
        with patch("logging.Logger.warning") as mock_warning:
            connect.response_rec_callback(wrong_knxipframe, HPAI(), None)
            mock_warning.assert_called_with("Could not understand knxipframe")

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame.init_from_body(
            ConnectResponse(status_code=ErrorCode.E_CONNECTION_ID)
        )
        with patch("logging.Logger.debug") as mock_warning:
            connect.response_rec_callback(err_knxipframe, HPAI(), None)
            mock_warning.assert_called_with(
                "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                type(connect).__name__,
                type(err_knxipframe.body).__name__,
                ErrorCode.E_CONNECTION_ID,
            )

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame.init_from_body(
            ConnectResponse(
                communication_channel=23,
                crd=ConnectResponseData(individual_address=IndividualAddress(7)),
            )
        )
        connect.response_rec_callback(res_knxipframe, HPAI(), None)
        assert connect.success
        assert connect.communication_channel == 23
        assert connect.crd.individual_address.raw == 7
