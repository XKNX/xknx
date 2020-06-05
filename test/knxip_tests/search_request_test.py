"""Unit test for KNX/IP SearchRequest objects."""
import pytest
import asyncio

from xknx import XKNX
from xknx.knxip import HPAI, KNXIPFrame, KNXIPServiceType, SearchRequest

from xknx._test import Testcase

class Test_KNXIP_Discovery(Testcase):
    """Test class for KNX/IP SearchRequest objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    @pytest.mark.asyncio
    async def test_search_request(self):
        """Test parsing and streaming SearchRequest KNX/IP packet."""
        raw = ((0x06, 0x10, 0x02, 0x01, 0x00, 0x0e, 0x08, 0x01,
                0xe0, 0x00, 0x17, 0x0c, 0x0e, 0x57))
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, SearchRequest))
        self.assertEqual(
            knxipframe.body.discovery_endpoint,
            HPAI(ip_addr="224.0.23.12", port=3671))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.SEARCH_REQUEST)
        knxipframe2.body.discovery_endpoint = \
            HPAI(ip_addr="224.0.23.12", port=3671)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))
