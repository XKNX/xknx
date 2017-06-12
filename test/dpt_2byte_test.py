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
        self.assertEqual(DPTCurrent().value_max, 670760)
        self.assertEqual(DPTCurrent().unit, "mA")
        self.assertEqual(DPTCurrent().resolution, 1)

    def test_current_assert_min_exceeded(self):
        with self.assertRaises(ConversionError):
            DPTCurrent().to_knx(-1)

    def test_current_value_38(self):
        self.assertEqual(DPTCurrent().to_knx(38), (0x00, 0x26))
        self.assertEqual(DPTCurrent().from_knx((0x00, 0x26)), 38)

    def test_current_value_78(self):
        self.assertEqual(DPTCurrent().to_knx(78), (0x00, 0x4E))
        self.assertEqual(DPTCurrent().from_knx((0x00, 0x4E)), 78)

    def test_current_wrong_value_to_knx(self):
        with self.assertRaises(ConversionError):
            DPTCurrent().to_knx(9110105)

    def test_current_wrong_value_from_knx(self):
        with self.assertRaises(ConversionError):
            DPTCurrent().from_knx((0xFF, 0x4E))

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestDPT2byte)
unittest.TextTestRunner(verbosity=10).run(SUITE)
