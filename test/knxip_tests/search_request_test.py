"""Unit test for KNX/IP SearchRequest objects."""
from xknx import XKNX
from xknx.knxip import HPAI, KNXIPFrame, SearchRequest


class Test_KNXIP_Discovery:
    """Test class for KNX/IP SearchRequest objects."""

    def test_search_request(self):
        """Test parsing and streaming SearchRequest KNX/IP packet."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x01,
            0x00,
            0x0E,
            0x08,
            0x01,
            0xE0,
            0x00,
            0x17,
            0x0C,
            0x0E,
            0x57,
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        assert isinstance(knxipframe.body, SearchRequest)
        assert knxipframe.body.discovery_endpoint == HPAI(
            ip_addr="224.0.23.12", port=3671
        )

        knxipframe2 = KNXIPFrame.init_from_body(
            SearchRequest(
                xknx, discovery_endpoint=HPAI(ip_addr="224.0.23.12", port=3671)
            )
        )

        assert knxipframe2.to_knx() == list(raw)
