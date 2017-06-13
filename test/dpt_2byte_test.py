import unittest

from xknx.knx import DPTCurrent, \
    ConversionError

class TestDPT2byte(unittest.TestCase):
    # pylint: disable=too-many-public-methods,invalid-name

    #
    # DPTCurrent
    #
    def test_current_settings(self):
        self.assertEqual(DPTCurrent().value_min, 0)
        self.assertEqual(DPTCurrent().value_max, 65535)
        self.assertEqual(DPTCurrent().unit, "mA")
        self.assertEqual(DPTCurrent().resolution, 1)

    def test_current_assert_min_exceeded(self):
        with self.assertRaises(ConversionError):
            DPTCurrent().to_knx(-1)

    def test_current_to_knx_exceed_limits(self):
        with self.assertRaises(ConversionError):
            DPTCurrent().to_knx(65536)

    def test_current_value_large_value(self):
        self.assertEqual(DPTCurrent().to_knx(65535), (0x2F, 0xFF))

    def test_current_value_38(self):
        self.assertEqual(DPTCurrent().to_knx(38), (0x00, 0x26))
        self.assertEqual(DPTCurrent().from_knx((0x00, 0x26)), 38)

    def test_current_value_78(self):
        self.assertEqual(DPTCurrent().to_knx(78), (0x00, 0x4E))
        self.assertEqual(DPTCurrent().from_knx((0x00, 0x4E)), 78)


    def test_current_wrong_value_from_knx(self):
        with self.assertRaises(ConversionError):
            DPTCurrent().from_knx((0xFF, 0x4E))

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestDPT2byte)
unittest.TextTestRunner(verbosity=2).run(SUITE)
