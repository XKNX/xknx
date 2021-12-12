"""Unit test for KNX/IP HPAI objects."""
import pytest
from xknx.exceptions import ConversionError, CouldNotParseKNXIP
from xknx.knxip import HPAI


class TestKNXIPHPAI:
    """Test class for KNX/IP HPAI objects."""

    def test_hpai(self):
        """Test parsing and streaming HPAI KNX/IP fragment."""
        raw = (0x08, 0x01, 0xC0, 0xA8, 0x2A, 0x01, 0x84, 0x95)

        hpai = HPAI()
        assert hpai.from_knx(raw) == 8
        assert hpai.ip_addr == "192.168.42.1"
        assert hpai.port == 33941
        assert not hpai.route_back

        hpai2 = HPAI(ip_addr="192.168.42.1", port=33941)
        assert hpai2.to_knx() == list(raw)
        assert not hpai2.route_back

    def test_from_knx_wrong_input1(self):
        """Test parsing of wrong HPAI KNX/IP packet (wrong length)."""
        raw = (0x08, 0x01, 0xC0, 0xA8, 0x2A)
        with pytest.raises(CouldNotParseKNXIP):
            HPAI().from_knx(raw)

    def test_from_knx_wrong_input2(self):
        """Test parsing of wrong HPAI KNX/IP packet (wrong length byte)."""
        raw = (0x09, 0x01, 0xC0, 0xA8, 0x2A, 0x01, 0x84, 0x95)
        with pytest.raises(CouldNotParseKNXIP):
            HPAI().from_knx(raw)

    def test_from_knx_wrong_input3(self):
        """Test parsing of wrong HPAI KNX/IP packet (wrong HPAI type)."""
        raw = (0x08, 0x02, 0xC0, 0xA8, 0x2A, 0x01, 0x84, 0x95)
        with pytest.raises(CouldNotParseKNXIP):
            HPAI().from_knx(raw)

    def test_to_knx_wrong_ip(self):
        """Test serializing HPAI to KNV/IP with wrong ip type."""
        hpai = HPAI(ip_addr=127001)
        with pytest.raises(ConversionError):
            hpai.to_knx()

    def test_route_back(self):
        """Test route_back property."""
        hpai = HPAI()
        assert hpai.ip_addr == "0.0.0.0"
        assert hpai.port == 0
        assert hpai.route_back
        hpai.ip_addr = "10.1.2.3"
        assert not hpai.route_back
