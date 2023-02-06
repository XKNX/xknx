"""Unit test for KNX/IP base class."""
import pytest

from xknx.exceptions import CouldNotParseKNXIP, IncompleteKNXIPFrame
from xknx.knxip import KNXIPFrame, KNXIPHeader
from xknx.knxip.knxip_enum import KNXIPServiceType


class TestKNXIPFrame:
    """Test class for KNX/IP base class."""

    def test_wrong_init(self):
        """Testing init method with wrong service_type_ident."""
        header = KNXIPHeader()
        header.service_type_ident = KNXIPServiceType.REMOTE_DIAG_RESPONSE
        with pytest.raises(CouldNotParseKNXIP):
            # this is not yet implemented in xknx
            KNXIPFrame.from_knx(header.to_knx())

    def test_double_frame(self):
        """Test parsing KNX/IP frame from streaming data containing two frames."""
        raw = bytes.fromhex(
            "06 10 04 20 00 15 04 02 51 00 29 00 bc e0 10 fa"
            "09 2d 01 00 80"
            "06 10 04 20 00 15 04 02 52 00 29 00 bc e0 10 1f"
            "08 2d 01 00 80"
        )  # both frames have length 21
        frame_1, rest_1 = KNXIPFrame.from_knx(raw)
        frame_2, rest_2 = KNXIPFrame.from_knx(rest_1)
        assert frame_1.header.total_length == 21
        assert frame_2.header.total_length == 21

    def test_parsing_too_short_knxip(self):
        """Test parsing and streaming connection state request KNX/IP packet."""
        raw = bytes.fromhex("06 10 02 07 00 10 15 00 08 01 C0 A8 C8 0C C3")
        with pytest.raises(IncompleteKNXIPFrame):
            KNXIPFrame.from_knx(raw)
