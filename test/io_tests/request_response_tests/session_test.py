"""Unit test for KNX/IP Session Request/Response."""
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.io.request_response import Session
from xknx.knxip import (
    HPAI,
    KNXIPFrame,
    KNXIPServiceType,
    SessionRequest,
    SessionResponse,
)


class TestSession:
    """Test class for xknx/io/Session objects."""

    async def test_session(self):
        """Test authenticating to secure KNX device."""
        xknx = XKNX()
        transport_mock = Mock()
        ecdh_public_key = bytes(16)
        session = Session(
            xknx,
            transport_mock,
            ecdh_client_public_key=ecdh_public_key,
        )
        session.timeout_in_seconds = 0

        assert session.awaited_response_class == SessionResponse

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame.init_from_body(
            SessionRequest(
                xknx,
                ecdh_client_public_key=ecdh_public_key,
            )
        )

        await session.start()
        transport_mock.send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame(xknx)
        wrong_knxipframe.init(KNXIPServiceType.SESSION_STATUS)
        with patch("logging.Logger.warning") as mock_warning:
            session.response_rec_callback(wrong_knxipframe, HPAI(), None)
            mock_warning.assert_called_with("Could not understand knxipframe")
            assert session.success is False

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame(xknx)
        res_knxipframe.init(KNXIPServiceType.SESSION_RESPONSE)
        res_knxipframe.body.secure_session_id = 5
        session.response_rec_callback(res_knxipframe, HPAI(), None)
        assert session.success is True
        assert session.response.secure_session_id == 5
