import unittest

from xknx.knx import DPTTime, DPTWeekday, ConversionError

class TestDPTTime(unittest.TestCase):

    def test_from_knx(self):
        self.assertEqual(DPTTime().from_knx((0x4D, 0x17, 0x2A)),
                         {'day': DPTWeekday.TUESDAY,
                          'hours': 13,
                          'minutes': 23,
                          'seconds': 42})

    def test_from_knx_max(self):
        self.assertEqual(DPTTime().from_knx((0xF7, 0x3b, 0x3b)),
                         {'day': DPTWeekday.SUNDAY,
                          'hours': 23,
                          'minutes': 59,
                          'seconds': 59})

    def test_from_knx_min(self):
        self.assertEqual(DPTTime().from_knx((0x0, 0x0, 0x0)),
                         {'day': DPTWeekday.NONE,
                          'hours': 0,
                          'minutes': 0,
                          'seconds': 0})

    def test_to_knx(self):
        raw = DPTTime().to_knx(
            {'day': DPTWeekday.TUESDAY,
             'hours': 13,
             'minutes': 23,
             'seconds': 42})
        self.assertEqual(raw, (0x4D, 0x17, 0x2A))

    def test_to_knx_max(self):
        raw = DPTTime().to_knx(
            {'day': DPTWeekday.SUNDAY,
             'hours': 23,
             'minutes': 59,
             'seconds': 59})
        self.assertEqual(raw, (0xF7, 0x3b, 0x3b))

    def test_to_knx_min(self):
        raw = DPTTime().to_knx(
            {'day': DPTWeekday.NONE,
             'hours': 0,
             'minutes': 0,
             'seconds': 0})
        self.assertEqual(raw, (0x0, 0x0, 0x0))

    def test_to_knx_default(self):
        self.assertEqual(DPTTime().to_knx({}), (0x0, 0x0, 0x0))


    def test_from_knx_wrong_parameter(self):
        with self.assertRaises(ConversionError):
            DPTTime().from_knx((0xF8, 0x23))

    def test_from_knx_wrong_parameter2(self):
        with self.assertRaises(ConversionError):
            DPTTime().from_knx((0xF8, "0x23"))

    def test_to_knx_wrong_parameter(self):
        with self.assertRaises(ConversionError):
            DPTTime().to_knx("fnord")


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestDPTTime)
unittest.TextTestRunner(verbosity=2).run(SUITE)
