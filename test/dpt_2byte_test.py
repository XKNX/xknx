import unittest

from xknx.knx import DPTUElCurrentmA, \
    ConversionError

class TestDPT2byte(unittest.TestCase):
    # pylint: disable=too-many-public-methods,invalid-name

    #
    # DPTUElCurrentmA
    #
    def test_current_settings(self):
        self.assertEqual(DPTUElCurrentmA().value_min, 0)
        self.assertEqual(DPTUElCurrentmA().value_max, 65535)
        self.assertEqual(DPTUElCurrentmA().unit, "mA")
        self.assertEqual(DPTUElCurrentmA().resolution, 1)

    def test_current_assert_min_exceeded(self):
        with self.assertRaises(ConversionError):
            DPTUElCurrentmA().to_knx(-1)

    def test_current_to_knx_exceed_limits(self):
        with self.assertRaises(ConversionError):
            DPTUElCurrentmA().to_knx(65536)

    def test_current_to_knx_exceed_limits2(self):
        with self.assertRaises(ConversionError):
            DPTUElCurrentmA().to_knx(-1)

    def test_current_value_max_value(self):
        self.assertEqual(DPTUElCurrentmA().to_knx(65535), (0xFF, 0xFF))
        self.assertEqual(DPTUElCurrentmA().from_knx((0xFF, 0xFF)), 65535)

    def test_current_value_min_value(self):
        self.assertEqual(DPTUElCurrentmA().to_knx(0), (0x00, 0x00))
        self.assertEqual(DPTUElCurrentmA().from_knx((0x00, 0x00)), 0)

    def test_current_value_38(self):
        self.assertEqual(DPTUElCurrentmA().to_knx(38), (0x00, 0x26))
        self.assertEqual(DPTUElCurrentmA().from_knx((0x00, 0x26)), 38)

    def test_current_value_78(self):
        self.assertEqual(DPTUElCurrentmA().to_knx(78), (0x00, 0x4E))
        self.assertEqual(DPTUElCurrentmA().from_knx((0x00, 0x4E)), 78)

    def test_current_value_1234(self):
        self.assertEqual(DPTUElCurrentmA().to_knx(4660), (0x12, 0x34))
        self.assertEqual(DPTUElCurrentmA().from_knx((0x12, 0x34)), 4660)

    def test_current_wrong_value_from_knx(self):
        with self.assertRaises(ConversionError):
            DPTUElCurrentmA().from_knx((0xFF, 0x4E, 0x12))

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestDPT2byte)
unittest.TextTestRunner(verbosity=2).run(SUITE)
