"""Unit test for KNX/IP TunnellingAck objects."""

import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import DisconnectRequest, KNXIPHeader, KNXIPServiceType


class TestKNXIPHeader:
    """Test class for KNX/IP Header objects."""

    def test_from_knx(self) -> None:
        """Test parsing and streaming wrong Header (wrong length byte)."""
        raw = bytes((0x06, 0x10, 0x04, 0x21, 0x00, 0x0A))
        header = KNXIPHeader()
        assert header.from_knx(raw) == 6
        assert header.HEADERLENGTH == 6
        assert header.PROTOCOLVERSION == 16
        assert header.service_type_ident == KNXIPServiceType.TUNNELLING_ACK
        assert header.total_length == 10
        assert header.to_knx() == raw

    def test_set_length(self) -> None:
        """Test setting length."""
        header = KNXIPHeader()
        header.set_length(DisconnectRequest())
        # 6 (header) + 2 + 8 (HPAI length)
        assert header.total_length == 16

    def test_set_length_error(self) -> None:
        """Test setting length with wrong type."""
        header = KNXIPHeader()
        with pytest.raises(TypeError):
            header.set_length(2)

    def test_from_knx_wrong_header(self) -> None:
        """Test parsing and streaming wrong Header (wrong length)."""
        raw = bytes((0x06, 0x10, 0x04, 0x21, 0x00))
        header = KNXIPHeader()
        with pytest.raises(CouldNotParseKNXIP):
            header.from_knx(raw)

    def test_from_knx_wrong_header2(self) -> None:
        """Test parsing and streaming wrong Header (wrong length byte)."""
        raw = bytes((0x05, 0x10, 0x04, 0x21, 0x00, 0x0A))
        header = KNXIPHeader()
        with pytest.raises(CouldNotParseKNXIP):
            header.from_knx(raw)

    def test_from_knx_wrong_header3(self) -> None:
        """Test parsing and streaming wrong Header (wrong protocol version)."""
        raw = bytes((0x06, 0x11, 0x04, 0x21, 0x00, 0x0A))
        header = KNXIPHeader()
        with pytest.raises(CouldNotParseKNXIP):
            header.from_knx(raw)

    def test_from_knx_wrong_header4(self) -> None:
        """Test parsing and streaming wrong Header (unsupported service type)."""
        # 0x0000 as service type
        raw = bytes((0x06, 0x10, 0x00, 0x00, 0x00, 0x0A))
        header = KNXIPHeader()
        with pytest.raises(CouldNotParseKNXIP):
            header.from_knx(raw)

    @pytest.mark.parametrize("total_length", [0, 1, 5])
    def test_from_knx_total_length_too_small(self, total_length: int) -> None:
        """Test parsing Header with a total length smaller than the header itself."""
        raw = bytes((0x06, 0x10, 0x04, 0x21, 0x00, total_length))
        header = KNXIPHeader()
        with pytest.raises(CouldNotParseKNXIP):
            header.from_knx(raw)
        # total_length is set anyway - the TCP transport uses it to skip the frame
        assert header.total_length == total_length

    def test_from_knx_unknown_service_type_sets_total_length(self) -> None:
        """Test total length is set before raising for an unknown service type."""
        raw = bytes((0x06, 0x10, 0x0F, 0x00, 0x00, 0x0A))
        header = KNXIPHeader()
        with pytest.raises(CouldNotParseKNXIP):
            header.from_knx(raw)
        assert header.total_length == 10
