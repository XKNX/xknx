"""Unit test for KNX/IP SessionResponse objects."""

from xknx.knxip import KNXIPFrame, SessionResponse


class TestKNXIPSessionResponse:
    """Test class for KNX/IP SessionResponse objects."""

    def test_session_response(self) -> None:
        """Test parsing and streaming session response KNX/IP packet."""
        public_key = bytes.fromhex(
            "bd f0 99 90 99 23 14 3e"  # Diffie-Hellman Server Public Value Y
            "f0 a5 de 0b 3b e3 68 7b"
            "c5 bd 3c f5 f9 e6 f9 01"
            "69 9c d8 70 ec 1f f8 24"
        )
        message_authentication_code = bytes.fromhex(
            "a9 22 50 5a aa 43 61 63"  # Message Authentication Code
            "57 0b d5 49 4c 2d f2 a3"
        )
        raw = (
            bytes.fromhex(
                "06 10 09 52 00 38"  # KNXnet/IP header
                "00 01"  # Secure Session Identifier
            )
            + public_key
            + message_authentication_code
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, SessionResponse)
        assert knxipframe.body.secure_session_id == 1
        assert knxipframe.body.ecdh_server_public_key == public_key
        assert (
            knxipframe.body.message_authentication_code == message_authentication_code
        )

        assert knxipframe.to_knx() == raw

        session_response = SessionResponse(
            secure_session_id=1,
            ecdh_server_public_key=public_key,
            message_authentication_code=message_authentication_code,
        )
        knxipframe2 = KNXIPFrame.init_from_body(session_response)

        assert knxipframe2.to_knx() == raw
