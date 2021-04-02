"""Unit test for KNX/IP ConnectionState Request/Response."""
from unittest.mock import patch

import pytest
from xknx import XKNX
from xknx.io import ConnectionState, UDPClient
from xknx.knxip import (
    HPAI,
    ConnectionStateRequest,
    ConnectionStateResponse,
    ErrorCode,
    KNXIPFrame,
    KNXIPServiceType,
)


@pytest.mark.asyncio
class TestConnectionState:
    """Test class for xknx/io/ConnectionState objects."""

    async def test_connectionstate(self):
        """Test connectionstateing from KNX bus."""
        xknx = XKNX()
        communication_channel_id = 23
        udp_client = UDPClient(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        connectionstate = ConnectionState(
            xknx, udp_client, communication_channel_id, route_back=False
        )
        connectionstate.timeout_in_seconds = 0

        assert connectionstate.awaited_response_class == ConnectionStateResponse
        assert connectionstate.communication_channel_id == communication_channel_id

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame.init_from_body(
            ConnectionStateRequest(
                xknx,
                communication_channel_id=communication_channel_id,
                control_endpoint=HPAI(ip_addr="192.168.1.3", port=4321),
            )
        )
        with patch("xknx.io.UDPClient.send") as mock_udp_send, patch(
            "xknx.io.UDPClient.getsockname"
        ) as mock_udp_getsockname:
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            await connectionstate.start()
            mock_udp_send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame(xknx)
        wrong_knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_REQUEST)
        with patch("logging.Logger.warning") as mock_warning:
            connectionstate.response_rec_callback(wrong_knxipframe, None)
            mock_warning.assert_called_with("Could not understand knxipframe")

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame(xknx)
        err_knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_RESPONSE)
        err_knxipframe.body.status_code = ErrorCode.E_CONNECTION_ID
        with patch("logging.Logger.debug") as mock_warning:
            connectionstate.response_rec_callback(err_knxipframe, None)
            mock_warning.assert_called_with(
                "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                type(connectionstate).__name__,
                type(err_knxipframe.body).__name__,
                ErrorCode.E_CONNECTION_ID,
            )

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame(xknx)
        res_knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_RESPONSE)
        connectionstate.response_rec_callback(res_knxipframe, None)
        assert connectionstate.success

    async def test_connectionstate_route_back_true(self):
        """Test connectionstateing from KNX bus."""
        xknx = XKNX()
        communication_channel_id = 23
        udp_client = UDPClient(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        connectionstate = ConnectionState(
            xknx, udp_client, communication_channel_id, route_back=True
        )
        connectionstate.timeout_in_seconds = 0

        assert connectionstate.awaited_response_class == ConnectionStateResponse
        assert connectionstate.communication_channel_id == communication_channel_id

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame.init_from_body(
            ConnectionStateRequest(
                xknx,
                communication_channel_id=communication_channel_id,
            )
        )
        with patch("xknx.io.UDPClient.send") as mock_udp_send, patch(
            "xknx.io.UDPClient.getsockname"
        ) as mock_udp_getsockname:
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            await connectionstate.start()
            mock_udp_send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame(xknx)
        wrong_knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_REQUEST)
        with patch("logging.Logger.warning") as mock_warning:
            connectionstate.response_rec_callback(wrong_knxipframe, None)
            mock_warning.assert_called_with("Could not understand knxipframe")

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame(xknx)
        err_knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_RESPONSE)
        err_knxipframe.body.status_code = ErrorCode.E_CONNECTION_ID
        with patch("logging.Logger.debug") as mock_warning:
            connectionstate.response_rec_callback(err_knxipframe, None)
            mock_warning.assert_called_with(
                "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                type(connectionstate).__name__,
                type(err_knxipframe.body).__name__,
                ErrorCode.E_CONNECTION_ID,
            )

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame(xknx)
        res_knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_RESPONSE)
        connectionstate.response_rec_callback(res_knxipframe, None)
        assert connectionstate.success
