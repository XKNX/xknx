"""Unit test for KNX/IP ConnectionState Request/Response."""

from unittest.mock import patch

from xknx.io.request_response import ConnectionState
from xknx.io.transport import UDPTransport
from xknx.knxip import (
    HPAI,
    ConnectionStateRequest,
    ConnectionStateResponse,
    ErrorCode,
    KNXIPFrame,
)


class TestConnectionState:
    """Test class for xknx/io/ConnectionState objects."""

    async def test_connectionstate(self) -> None:
        """Test connectionstateing from KNX bus."""
        communication_channel_id = 23
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        local_hpai = HPAI(ip_addr="192.168.1.3", port=4321)
        connectionstate = ConnectionState(
            udp_transport, communication_channel_id, local_hpai=local_hpai
        )
        connectionstate.timeout_in_seconds = 0

        assert connectionstate.awaited_response_class == ConnectionStateResponse
        assert connectionstate.communication_channel_id == communication_channel_id

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame.init_from_body(
            ConnectionStateRequest(
                communication_channel_id=communication_channel_id,
                control_endpoint=local_hpai,
            )
        )
        with (
            patch("xknx.io.transport.UDPTransport.send") as mock_udp_send,
            patch("xknx.io.transport.UDPTransport.getsockname") as mock_udp_getsockname,
        ):
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            await connectionstate.start()
            mock_udp_send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame.init_from_body(ConnectionStateRequest())
        with patch("logging.Logger.warning") as mock_warning:
            connectionstate.response_rec_callback(wrong_knxipframe, HPAI(), None)
            mock_warning.assert_called_with("Could not understand knxipframe")

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame.init_from_body(
            ConnectionStateResponse(status_code=ErrorCode.E_CONNECTION_ID)
        )
        with patch("logging.Logger.debug") as mock_warning:
            connectionstate.response_rec_callback(err_knxipframe, HPAI(), None)
            mock_warning.assert_called_with(
                "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                type(connectionstate).__name__,
                type(err_knxipframe.body).__name__,
                ErrorCode.E_CONNECTION_ID,
            )

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame.init_from_body(ConnectionStateResponse())
        connectionstate.response_rec_callback(res_knxipframe, HPAI(), None)
        assert connectionstate.success

    async def test_connectionstate_route_back_true(self) -> None:
        """Test connectionstateing from KNX bus."""
        communication_channel_id = 23
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        local_hpai = HPAI()
        connectionstate = ConnectionState(
            udp_transport, communication_channel_id, local_hpai=local_hpai
        )
        connectionstate.timeout_in_seconds = 0

        assert connectionstate.awaited_response_class == ConnectionStateResponse
        assert connectionstate.communication_channel_id == communication_channel_id

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame.init_from_body(
            ConnectionStateRequest(
                communication_channel_id=communication_channel_id,
            )
        )
        with (
            patch("xknx.io.transport.UDPTransport.send") as mock_udp_send,
            patch("xknx.io.transport.UDPTransport.getsockname") as mock_udp_getsockname,
        ):
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            await connectionstate.start()
            mock_udp_send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame.init_from_body(ConnectionStateRequest())
        with patch("logging.Logger.warning") as mock_warning:
            connectionstate.response_rec_callback(wrong_knxipframe, HPAI(), None)
            mock_warning.assert_called_with("Could not understand knxipframe")

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame.init_from_body(
            ConnectionStateResponse(status_code=ErrorCode.E_CONNECTION_ID)
        )
        with patch("logging.Logger.debug") as mock_warning:
            connectionstate.response_rec_callback(err_knxipframe, HPAI(), None)
            mock_warning.assert_called_with(
                "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                type(connectionstate).__name__,
                type(err_knxipframe.body).__name__,
                ErrorCode.E_CONNECTION_ID,
            )

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame.init_from_body(ConnectionStateResponse())
        connectionstate.response_rec_callback(res_knxipframe, HPAI(), None)
        assert connectionstate.success
