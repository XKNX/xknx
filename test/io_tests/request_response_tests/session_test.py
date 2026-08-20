"""Unit test for KNX/IP Session Request/Response."""

from unittest.mock import Mock, patch

import pytest

from xknx.exceptions import RequestResponseError
from xknx.io.request_response import Session
from xknx.knxip import HPAI, KNXIPFrame, SessionRequest, SessionResponse, SessionStatus


class TestSession:
    """Test class for xknx/io/Session objects."""

    async def test_session(self) -> None:
        """Test authenticating to secure KNX device."""
        transport_mock = Mock()
        ecdh_public_key = bytes(16)
        session = Session(
            transport_mock,
            ecdh_client_public_key=ecdh_public_key,
        )
        session.timeout_in_seconds = 0

        assert session.AWAITED_RESPONSE_CLASS is SessionResponse

        # Expected KNX/IP-Frame:
        exp_knxipframe = KNXIPFrame.init_from_body(
            SessionRequest(ecdh_client_public_key=ecdh_public_key)
        )

        with pytest.raises(RequestResponseError):
            await session.request()
        transport_mock.send.assert_called_with(exp_knxipframe)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame.init_from_body(SessionStatus())
        with patch("logging.Logger.warning") as mock_warning:
            session._response_rec_callback(wrong_knxipframe, HPAI(), None)
            mock_warning.assert_called_with(
                "Could not understand knxipframe for %s: %s",
                type(session).__name__,
                wrong_knxipframe,
            )
            assert session._response is None

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame.init_from_body(SessionResponse(secure_session_id=5))
        session._response_rec_callback(res_knxipframe, HPAI(), None)
        assert session._response is not None
        assert session._response.secure_session_id == 5
