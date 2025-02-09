"""Unit test for KNX/IP SearchRequest Extended objects."""

from xknx.knxip import HPAI, KNXIPFrame, SearchRequestExtended
from xknx.knxip.srp import SRP


class TestKNXIPSearchRequestExtended:
    """Test class for KNX/IP SearchRequest Extended objects."""

    def test_search_request_extended(self) -> None:
        """Test parsing and streaming SearchRequest Extended KNX/IP packet."""
        raw = bytes.fromhex("06 10 02 0b 00 0e 08 01 e0 00 17 0C 0E 57")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, SearchRequestExtended)
        assert knxipframe.body.discovery_endpoint == HPAI(
            ip_addr="224.0.23.12", port=3671
        )

        knxipframe2 = KNXIPFrame.init_from_body(
            SearchRequestExtended(
                discovery_endpoint=HPAI(ip_addr="224.0.23.12", port=3671)
            )
        )

        assert knxipframe2.to_knx() == raw

    def test_search_request_extended_srp(self) -> None:
        """Test parsing and streaming SearchRequest Extended with SRPs KNX/IP packet."""
        raw = bytes.fromhex("06 10 02 0b 00 10 08 01 e0 00 17 0c 0e 57 02 81")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, SearchRequestExtended)
        assert knxipframe.body.discovery_endpoint == HPAI(
            ip_addr="224.0.23.12", port=3671
        )
        assert len(knxipframe.body.srps) == 1
        assert knxipframe.body.srps[0] == SRP.with_programming_mode()

        knxipframe2 = KNXIPFrame.init_from_body(
            SearchRequestExtended(
                discovery_endpoint=HPAI(ip_addr="224.0.23.12", port=3671),
                srps=[SRP.with_programming_mode()],
            )
        )

        assert knxipframe2.to_knx() == raw

    def test_search_request_extended_multiple_srp(self) -> None:
        """Test parsing and streaming SearchRequest Extended with SRPs KNX/IP packet."""
        raw = bytes.fromhex(
            "06 10 02 0b 00 18 08 01 e0 00 17 0c 0e 57 02 81 08 82 01 02 03 04 05 06"
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, SearchRequestExtended)
        assert knxipframe.body.discovery_endpoint == HPAI(
            ip_addr="224.0.23.12", port=3671
        )
        assert len(knxipframe.body.srps) == 2
        assert knxipframe.body.srps[0] == SRP.with_programming_mode()
        assert knxipframe.body.srps[1] == SRP.with_mac_address(
            bytes([1, 2, 3, 4, 5, 6])
        )

        knxipframe2 = KNXIPFrame.init_from_body(
            SearchRequestExtended(
                discovery_endpoint=HPAI(ip_addr="224.0.23.12", port=3671),
                srps=[
                    SRP.with_programming_mode(),
                    SRP.with_mac_address(bytes([1, 2, 3, 4, 5, 6])),
                ],
            )
        )

        assert knxipframe2.to_knx() == raw
