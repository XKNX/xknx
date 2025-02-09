"""Unit test for KNX/IP HPAI objects."""

import pytest

from xknx.exceptions import ConversionError, CouldNotParseKNXIP
from xknx.knxip import HPAI, HostProtocol


class TestKNXIPHPAI:
    """Test class for KNX/IP HPAI objects."""

    def test_hpai_udp(self) -> None:
        """Test parsing and streaming HPAI KNX/IP fragment."""
        raw = bytes((0x08, 0x01, 0xC0, 0xA8, 0x2A, 0x01, 0x84, 0x95))

        hpai = HPAI()
        assert hpai.from_knx(raw) == 8
        assert hpai.ip_addr == "192.168.42.1"
        assert hpai.port == 33941
        assert hpai.protocol == HostProtocol.IPV4_UDP
        assert not hpai.route_back

        hpai2 = HPAI(ip_addr="192.168.42.1", port=33941)
        assert hpai2.to_knx() == raw
        assert not hpai2.route_back

    def test_hpai_tcp(self) -> None:
        """Test parsing and streaming HPAI KNX/IP fragment."""
        raw = bytes((0x08, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00))

        hpai = HPAI()
        assert hpai.from_knx(raw) == 8
        assert hpai.ip_addr == "0.0.0.0"
        assert hpai.port == 0
        assert hpai.protocol == HostProtocol.IPV4_TCP
        assert hpai.route_back

        hpai2 = HPAI(ip_addr="0.0.0.0", port=0, protocol=HostProtocol.IPV4_TCP)
        assert hpai2.to_knx() == raw

    def test_from_knx_wrong_input1(self) -> None:
        """Test parsing of wrong HPAI KNX/IP packet (wrong length)."""
        raw = bytes((0x08, 0x01, 0xC0, 0xA8, 0x2A))
        with pytest.raises(CouldNotParseKNXIP):
            HPAI().from_knx(raw)

    def test_from_knx_wrong_input2(self) -> None:
        """Test parsing of wrong HPAI KNX/IP packet (wrong length byte)."""
        raw = bytes((0x09, 0x01, 0xC0, 0xA8, 0x2A, 0x01, 0x84, 0x95))
        with pytest.raises(CouldNotParseKNXIP):
            HPAI().from_knx(raw)

    def test_from_knx_wrong_input3(self) -> None:
        """Test parsing of wrong HPAI KNX/IP packet (wrong HPAI type)."""
        raw = bytes((0x08, 0x03, 0xC0, 0xA8, 0x2A, 0x01, 0x84, 0x95))
        with pytest.raises(CouldNotParseKNXIP):
            HPAI().from_knx(raw)

    def test_to_knx_wrong_ip(self) -> None:
        """Test serializing HPAI to KNV/IP with wrong ip type."""
        hpai = HPAI(ip_addr=127001)
        with pytest.raises(ConversionError):
            hpai.to_knx()

    def test_route_back(self) -> None:
        """Test route_back property."""
        hpai = HPAI()
        assert hpai.ip_addr == "0.0.0.0"
        assert hpai.port == 0
        assert hpai.route_back
        hpai.ip_addr = "10.1.2.3"
        assert not hpai.route_back
