import unittest

from xknx.knx import DPTScaling, ConversionError

class TestDPTScaling(unittest.TestCase):
    # pylint: disable=too-many-public-methods,invalid-name

    def test_value_50(self):
        self.assertEqual(DPTScaling().to_knx(50), (0x80,))
        self.assertEqual(DPTScaling().from_knx((0x80,)), 50)


    def test_value_75(self):
        self.assertEqual(DPTScaling().to_knx(75), (0xC0,))
        self.assertEqual(DPTScaling().from_knx((0xC0,)), 75)


    def test_value_25(self):
        self.assertEqual(DPTScaling().to_knx(25), (0x40,))
        self.assertEqual(DPTScaling().from_knx((0x40,)), 25)


    def test_value_zero(self):
        self.assertEqual(DPTScaling().to_knx(0), (0x00,))
        self.assertEqual(DPTScaling().from_knx((0x00,)), 0)


    def test_value_100(self):
        self.assertEqual(DPTScaling().to_knx(100), (0xFF,))
        self.assertEqual(DPTScaling().from_knx((0xFF,)), 100)


    def test_max(self):
        self.assertEqual(DPTScaling().to_knx(DPTScaling.value_max), (0xFF,))
        self.assertEqual(DPTScaling().from_knx((0xFF,)), DPTScaling.value_max)


    def test_min(self):
        self.assertEqual(DPTScaling().to_knx(DPTScaling.value_min), (0x00,))
        self.assertEqual(DPTScaling().from_knx((0x00,)), DPTScaling.value_min)


    def test_to_knx_min_exceeded(self):
        with self.assertRaises(ConversionError):
            DPTScaling().to_knx(DPTScaling.value_min - 1)


    def test_to_knx_max_exceeded(self):
        with self.assertRaises(ConversionError):
            DPTScaling().to_knx(DPTScaling.value_max + 1)


    def test_to_knx_wrong_parameter(self):
        with self.assertRaises(ConversionError):
            DPTScaling().to_knx("fnord")


    def test_from_knx_wrong_parameter(self):
        with self.assertRaises(ConversionError):
            DPTScaling().from_knx((0xF8, 0x01, 0x23))


    def test_from_knx_wrong_parameter2(self):
        with self.assertRaises(ConversionError):
            DPTScaling().from_knx(("0x23"))


    def test_value_float(self):
        self.assertEqual(DPTScaling().to_knx(50.00), (0x80,))


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestDPTScaling)
unittest.TextTestRunner(verbosity=2).run(SUITE)
