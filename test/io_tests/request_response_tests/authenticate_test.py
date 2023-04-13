"""Unit test for KNX/IP Authenticate Request/Response."""
from unittest.mock import Mock, patch

from xknx.io.request_response import Authenticate
from xknx.knxip import (
    HPAI,
    ConnectionStateRequest,
    KNXIPFrame,
    SessionAuthenticate,
    SessionStatus,
)
from xknx.knxip.knxip_enum import SecureSessionStatusCode


class TestAuthenticate:
    """Test class for xknx/io/Authenticate objects."""

    async def test_authenticate(self):
        """Test authenticating to secure KNX device."""
        transport_mock = Mock()
        user_id = 123
        mac = bytes(16)
        authenticate = Authenticate(
            transport_mock,
            user_id=user_id,
            message_authentication_code=mac,
        )
        authenticate.timeout_in_seconds = 0

        assert authenticate.awaited_response_class == SessionStatus

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame.init_from_body(
            SessionAuthenticate(
                user_id=user_id,
                message_authentication_code=mac,
            )
        )

        await authenticate.start()
        transport_mock.send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame.init_from_body(ConnectionStateRequest())
        with patch("logging.Logger.warning") as mock_warning:
            authenticate.response_rec_callback(wrong_knxipframe, HPAI(), None)
            mock_warning.assert_called_with("Could not understand knxipframe")
            assert authenticate.success is False

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame.init_from_body(SessionStatus())
        res_knxipframe.body.status = (
            SecureSessionStatusCode.STATUS_AUTHENTICATION_SUCCESS
        )
        authenticate.response_rec_callback(res_knxipframe, HPAI(), None)
        assert authenticate.success is True
        assert (
            authenticate.response.status
            == SecureSessionStatusCode.STATUS_AUTHENTICATION_SUCCESS
        )
