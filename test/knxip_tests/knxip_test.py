"""Unit test for KNX/IP base class."""
import pytest

from xknx import XKNX
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import KNXIPFrame

from xknx._test import Testcase

class Test_KNXIP(Testcase):
    """Test class for KNX/IP base class."""

    # pylint: disable=too-many-public-methods,invalid-name

    @pytest.mark.anyio
    async def test_wrong_init(self):
        """Testing init method with wrong service_type_ident."""
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with self.assertRaises(TypeError):
            knxipframe.init(23)

    @pytest.mark.anyio
    async def test_parsing_too_long_knxip(self):
        """Test parsing and streaming connection state request KNX/IP packet."""
        raw = ((0x06, 0x10, 0x02, 0x07, 0x00, 0x10, 0x15, 0x00,
                0x08, 0x01, 0xC0, 0xA8, 0xC8, 0x0C, 0xC3, 0xB4, 0x00))
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with self.assertRaises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)
