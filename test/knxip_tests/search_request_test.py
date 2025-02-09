"""Unit test for KNX/IP SearchRequest objects."""

from xknx.knxip import HPAI, KNXIPFrame, SearchRequest


class TestKNXIPSearchRequest:
    """Test class for KNX/IP SearchRequest objects."""

    def test_search_request(self) -> None:
        """Test parsing and streaming SearchRequest KNX/IP packet."""
        raw = bytes.fromhex("06 10 02 01 00 0E 08 01 E0 00 17 0C 0E 57")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, SearchRequest)
        assert knxipframe.body.discovery_endpoint == HPAI(
            ip_addr="224.0.23.12", port=3671
        )

        knxipframe2 = KNXIPFrame.init_from_body(
            SearchRequest(discovery_endpoint=HPAI(ip_addr="224.0.23.12", port=3671))
        )

        assert knxipframe2.to_knx() == raw
