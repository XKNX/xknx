"""Unit test for KNX/IP SearchRequest objects."""
import unittest

from xknx.knxip import KNXIPFrame, KNXIPServiceType, SearchRequest, \
    HPAI


class Test_KNXIP_Discovery(unittest.TestCase):
    """Test class for KNX/IP SearchRequest objects."""
    # pylint: disable=too-many-public-methods,invalid-name

    def test_connect_request(self):
        """Test parsing and streaming SearchRequest KNX/IP packet."""
        raw = ((0x06, 0x10, 0x02, 0x01, 0x00, 0x0e, 0x08, 0x01,
                0xe0, 0x00, 0x17, 0x0c, 0x0e, 0x57))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, SearchRequest))
        self.assertEqual(
            knxipframe.body.discovery_endpoint,
            HPAI(ip_addr="224.0.23.12", port=3671))

        knxipframe2 = KNXIPFrame()
        knxipframe2.init(KNXIPServiceType.SEARCH_REQUEST)
        knxipframe2.body.discovery_endpoint = \
            HPAI(ip_addr="224.0.23.12", port=3671)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))


SUITE = unittest.TestLoader().loadTestsFromTestCase(Test_KNXIP_Discovery)
unittest.TextTestRunner(verbosity=2).run(SUITE)
