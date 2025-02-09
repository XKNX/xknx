"""Unit test for KNX/IP SearchResponseExtended objects."""

from xknx.knxip import (
    HPAI,
    DIBDeviceInformation,
    DIBServiceFamily,
    DIBSuppSVCFamilies,
    KNXIPFrame,
    SearchResponseExtended,
)


class TestKNXIPSearchResponseExtended:
    """Test class for KNX/IP SearchResponse Extended objects."""

    def test_search_response_extended(self) -> None:
        """Test parsing and streaming SearchResponse KNX/IP packet."""
        raw = bytes.fromhex(
            "06 10 02 0C 00 50 08 01 C0 A8 2A 0A 0E 57 36 01"
            "02 00 11 00 00 00 11 22 33 44 55 66 E0 00 17 0C"
            "01 02 03 04 05 06 47 69 72 61 20 4B 4E 58 2F 49"
            "50 2D 52 6F 75 74 65 72 00 00 00 00 00 00 00 00"
            "00 00 00 00 0C 02 02 01 03 02 04 01 05 01 07 01"
        )
        knxipframe, rest = KNXIPFrame.from_knx(raw)
        assert knxipframe.header.total_length == 80
        assert not rest
        assert knxipframe.to_knx() == raw

        assert isinstance(knxipframe.body, SearchResponseExtended)
        assert knxipframe.body.control_endpoint == HPAI("192.168.42.10", 3671)
        assert len(knxipframe.body.dibs) == 2
        # Specific testing of parsing and serializing of
        # DIBDeviceInformation and DIBSuppSVCFamilies is
        # done within knxip_dib_test.py
        assert isinstance(knxipframe.body.dibs[0], DIBDeviceInformation)
        assert isinstance(knxipframe.body.dibs[1], DIBSuppSVCFamilies)
        assert knxipframe.body.device_name == "Gira KNX/IP-Router"
        assert knxipframe.body.dibs[1].supports(DIBServiceFamily.ROUTING)
        assert knxipframe.body.dibs[1].supports(DIBServiceFamily.TUNNELING)
        assert not knxipframe.body.dibs[1].supports(DIBServiceFamily.OBJECT_SERVER)

        search_response = SearchResponseExtended(
            control_endpoint=HPAI(ip_addr="192.168.42.10", port=3671)
        )
        search_response.dibs.append(knxipframe.body.dibs[0])
        search_response.dibs.append(knxipframe.body.dibs[1])
        knxipframe2 = KNXIPFrame.init_from_body(search_response)

        assert knxipframe2.to_knx() == raw

    def test_unknown_device_name(self) -> None:
        """Test device_name if no DIBDeviceInformation is present."""
        search_response = SearchResponseExtended()
        assert search_response.device_name == "UNKNOWN"
