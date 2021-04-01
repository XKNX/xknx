"""Unit test for KNX/IP TunnellingAck objects."""
import pytest
from xknx import XKNX
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import DisconnectRequest, KNXIPHeader, KNXIPServiceType


class Test_KNXIP_Header:
    """Test class for KNX/IP TunnellingAck objects."""

    def test_from_knx(self):
        """Test parsing and streaming wrong Header (wrong length byte)."""
        raw = (0x06, 0x10, 0x04, 0x21, 0x00, 0x0A)
        header = KNXIPHeader()
        assert header.from_knx(raw) == 6
        assert header.header_length == 6
        assert header.protocol_version == 16
        assert header.service_type_ident == KNXIPServiceType.TUNNELLING_ACK
        assert header.b4_reserve == 0
        assert header.total_length == 10
        assert header.to_knx() == list(raw)

    def test_set_length(self):
        """Test setting length."""
        xknx = XKNX()
        header = KNXIPHeader()
        header.set_length(DisconnectRequest(xknx))
        # 6 (header) + 2 + 8 (HPAI length)
        assert header.total_length == 16

    def test_set_length_error(self):
        """Test setting length with wrong type."""
        header = KNXIPHeader()
        with pytest.raises(TypeError):
            header.set_length(2)

    def test_from_knx_wrong_header(self):
        """Test parsing and streaming wrong Header (wrong length)."""
        raw = (0x06, 0x10, 0x04, 0x21, 0x00)
        header = KNXIPHeader()
        with pytest.raises(CouldNotParseKNXIP):
            header.from_knx(raw)

    def test_from_knx_wrong_header2(self):
        """Test parsing and streaming wrong Header (wrong length byte)."""
        raw = (0x05, 0x10, 0x04, 0x21, 0x00, 0x0A)
        header = KNXIPHeader()
        with pytest.raises(CouldNotParseKNXIP):
            header.from_knx(raw)

    def test_from_knx_wrong_header3(self):
        """Test parsing and streaming wrong Header (wrong protocol version)."""
        raw = (0x06, 0x11, 0x04, 0x21, 0x00, 0x0A)
        header = KNXIPHeader()
        with pytest.raises(CouldNotParseKNXIP):
            header.from_knx(raw)

    def test_from_knx_wrong_header4(self):
        """Test parsing and streaming wrong Header (unsupported service type)."""
        # 0x0000 as service type
        raw = (0x06, 0x10, 0x00, 0x00, 0x00, 0x0A)
        header = KNXIPHeader()
        with pytest.raises(CouldNotParseKNXIP):
            header.from_knx(raw)
