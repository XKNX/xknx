"""Unit test for KNX/IP SessionAuthenticate objects."""

from xknx.knxip import KNXIPFrame, SessionAuthenticate


class TestKNXIPSessionAuthenticate:
    """Test class for KNX/IP SessionAuthenticate objects."""

    def test_session_authenticate(self):
        """Test parsing and streaming session authenticate KNX/IP packet."""
        message_authentication_code = bytes.fromhex(
            "1f 1d 59 ea 9f 12 a1 52"  # Message Authentication Code
            "e5 d9 72 7f 08 46 2c de"
        )
        raw = (
            bytes.fromhex(
                "06 10 09 53 00 18"  # KNXnet/IP header
                "00 01"  # User ID
            )
            + message_authentication_code
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, SessionAuthenticate)
        assert knxipframe.body.user_id == 1
        assert (
            knxipframe.body.message_authentication_code == message_authentication_code
        )

        assert knxipframe.to_knx() == raw

        session_authenticate = SessionAuthenticate(
            user_id=1,
            message_authentication_code=message_authentication_code,
        )
        knxipframe2 = KNXIPFrame.init_from_body(session_authenticate)

        assert knxipframe2.to_knx() == raw
