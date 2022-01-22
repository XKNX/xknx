"""Unit test for KNX/IP DescriptionRequest objects."""
from xknx import XKNX
from xknx.knxip import HPAI, DescriptionRequest, KNXIPFrame


class TestKNXIPDescriptionRequest:
    """Test class for KNX/IP DescriptionRequest objects."""

    def test_description_request(self):
        """Test parsing and streaming DescriptionRequest KNX/IP packet."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x03,
            0x00,
            0x0E,
            0x08,
            0x01,
            0x7F,
            0x00,
            0x00,
            0x02,
            0x0E,
            0x57,
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        assert isinstance(knxipframe.body, DescriptionRequest)
        assert knxipframe.body.control_endpoint == HPAI(ip_addr="127.0.0.2", port=3671)

        knxipframe2 = KNXIPFrame.init_from_body(
            DescriptionRequest(
                xknx, control_endpoint=HPAI(ip_addr="127.0.0.2", port=3671)
            )
        )

        assert knxipframe2.to_knx() == list(raw)
