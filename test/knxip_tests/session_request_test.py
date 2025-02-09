"""Unit test for KNX/IP SessionRequest objects."""

from xknx.knxip import HPAI, KNXIPFrame, SessionRequest
from xknx.knxip.knxip_enum import HostProtocol


class TestKNXIPSessionRequest:
    """Test class for KNX/IP SessionRequest objects."""

    def test_session_request(self) -> None:
        """Test parsing and streaming session request KNX/IP packet."""
        public_key = bytes.fromhex(
            "0a a2 27 b4 fd 7a 32 31"  # Diffie-Hellman Client Public Value X
            "9b a9 96 0a c0 36 ce 0e"
            "5c 45 07 b5 ae 55 16 1f"
            "10 78 b1 dc fb 3c b6 31"
        )
        raw = (
            bytes.fromhex(
                "06 10 09 51 00 2e"  # KNXnet/IP header
                "08 02 00 00 00 00 00 00"  # HPAI TCPv4
            )
            + public_key
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, SessionRequest)
        assert knxipframe.body.control_endpoint == HPAI(protocol=HostProtocol.IPV4_TCP)
        assert knxipframe.body.ecdh_client_public_key == public_key

        assert knxipframe.to_knx() == raw

        session_request = SessionRequest(ecdh_client_public_key=public_key)
        knxipframe2 = KNXIPFrame.init_from_body(session_request)

        assert knxipframe2.to_knx() == raw
