"""Unit test for KNX/IP DescriptionRequest objects."""

from xknx.knxip import HPAI, DescriptionRequest, KNXIPFrame


class TestKNXIPDescriptionRequest:
    """Test class for KNX/IP DescriptionRequest objects."""

    def test_description_request(self) -> None:
        """Test parsing and streaming DescriptionRequest KNX/IP packet."""
        raw = bytes.fromhex("06 10 02 03 00 0E 08 01 7F 00 00 02 0E 57")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, DescriptionRequest)
        assert knxipframe.body.control_endpoint == HPAI(ip_addr="127.0.0.2", port=3671)

        knxipframe2 = KNXIPFrame.init_from_body(
            DescriptionRequest(control_endpoint=HPAI(ip_addr="127.0.0.2", port=3671))
        )

        assert knxipframe2.to_knx() == raw
