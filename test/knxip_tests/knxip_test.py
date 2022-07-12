"""Unit test for KNX/IP base class."""
import pytest

from xknx.exceptions import CouldNotParseKNXIP, IncompleteKNXIPFrame
from xknx.knxip import KNXIPFrame
from xknx.knxip.knxip_enum import KNXIPServiceType


class TestKNXIPFrame:
    """Test class for KNX/IP base class."""

    def test_wrong_init(self):
        """Testing init method with wrong service_type_ident."""
        knxipframe = KNXIPFrame()
        with pytest.raises(AttributeError):
            knxipframe.init(23)

        with pytest.raises(CouldNotParseKNXIP):
            # this is not yet implemented in xknx
            knxipframe.init(KNXIPServiceType.REMOTE_DIAG_RESPONSE)

    def test_double_frame(self):
        """Test parsing KNX/IP frame from streaming data containing two frames."""
        knxipframe = KNXIPFrame()
        raw = bytes.fromhex(
            "06 10 04 20 00 15 04 02 51 00 29 00 bc e0 10 fa"
            "09 2d 01 00 80"
            "06 10 04 20 00 15 04 02 52 00 29 00 bc e0 10 1f"
            "08 2d 01 00 80"
        )  # both frames have lenght 21
        assert knxipframe.from_knx(raw) == 21
        assert knxipframe.from_knx(raw[21:]) == 21

    def test_parsing_too_short_knxip(self):
        """Test parsing and streaming connection state request KNX/IP packet."""
        raw = bytes.fromhex("06 10 02 07 00 10 15 00 08 01 C0 A8 C8 0C C3")
        knxipframe = KNXIPFrame()
        with pytest.raises(IncompleteKNXIPFrame):
            knxipframe.from_knx(raw)

    def test_to_knx_no_body(self):
        """Test to_knx method without body raises exception."""
        knxipframe = KNXIPFrame()
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.to_knx()
