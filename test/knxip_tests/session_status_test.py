"""Unit test for KNX/IP SessionStatus objects."""

from xknx.knxip import KNXIPFrame, SessionStatus
from xknx.knxip.knxip_enum import SecureSessionStatusCode


class TestKNXIPSessionStatus:
    """Test class for KNX/IP SessionStatus objects."""

    def test_session_status(self) -> None:
        """Test parsing and streaming session status KNX/IP packet."""
        raw = bytes.fromhex(
            "06 10 09 54 00 08"  # KNXnet/IP header
            "00"  # status code 00h STATUS_AUTHENTICATION_SUCCESS
            "00"  # reserved
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, SessionStatus)
        assert (
            knxipframe.body.status
            == SecureSessionStatusCode.STATUS_AUTHENTICATION_SUCCESS
        )

        assert knxipframe.to_knx() == raw

        session_status = SessionStatus(
            status=SecureSessionStatusCode.STATUS_AUTHENTICATION_SUCCESS
        )
        knxipframe2 = KNXIPFrame.init_from_body(session_status)

        assert knxipframe2.to_knx() == raw
