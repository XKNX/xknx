"""Unit test for KNX/IP base class."""
import pytest
from xknx import XKNX
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import KNXIPFrame
from xknx.knxip.knxip_enum import KNXIPServiceType


class TestKNXIPFrame:
    """Test class for KNX/IP base class."""

    def test_wrong_init(self):
        """Testing init method with wrong service_type_ident."""
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(AttributeError):
            knxipframe.init(23)

        with pytest.raises(CouldNotParseKNXIP):
            # this is not yet implemented in xknx
            knxipframe.init(KNXIPServiceType.SEARCH_REQUEST_EXTENDED)

    def test_parsing_too_long_knxip(self):
        """Test parsing and streaming connection state request KNX/IP packet."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x07,
            0x00,
            0x10,
            0x15,
            0x00,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0xC8,
            0x0C,
            0xC3,
            0xB4,
            0x00,
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)
