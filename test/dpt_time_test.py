import unittest

from xknx import DPT_Time,DPT_Weekday,ConversionError

class TestDPT_Time(unittest.TestCase):

    def test_from_knx(self):
        self.assertEqual( DPT_Time().from_knx((0x4D, 0x17, 0x2A)), 
            {'day': DPT_Weekday.TUESDAY, 'hours': 13, 'minutes': 23, 'seconds': 42} )

    def test_from_knx_max(self):
        self.assertEqual( DPT_Time().from_knx((0xF7, 0x3b, 0x3b)),
            {'day': DPT_Weekday.SUNDAY, 'hours': 23, 'minutes': 59, 'seconds': 59} )

    def test_from_knx_min(self):
        self.assertEqual( DPT_Time().from_knx((0x0, 0x0, 0x0)),
            {'day': DPT_Weekday.NONE, 'hours': 0, 'minutes': 0, 'seconds': 0} )

    def test_to_knx(self):
        self.assertEqual( DPT_Time().to_knx(
            {'day': DPT_Weekday.TUESDAY, 'hours': 13, 'minutes': 23, 'seconds': 42}),
            (0x4D, 0x17, 0x2A))

    def test_to_knx_max(self):
        self.assertEqual( DPT_Time().to_knx(
            {'day': DPT_Weekday.SUNDAY, 'hours': 23, 'minutes': 59, 'seconds': 59}),
            (0xF7, 0x3b, 0x3b))

    def test_to_knx_min(self):
        self.assertEqual( DPT_Time().to_knx(
            {'day': DPT_Weekday.NONE, 'hours': 0, 'minutes': 0, 'seconds': 0}),
            (0x0, 0x0, 0x0))

    def test_to_knx_default(self):
            self.assertEqual( DPT_Time().to_knx({}),(0x0, 0x0, 0x0))


    def test_from_knx_wrong_parameter(self):
        with self.assertRaises(ConversionError):
            DPT_Time().from_knx((0xF8, 0x23 ))

    def test_from_knx_wrong_parameter2(self):
        with self.assertRaises(ConversionError):
            DPT_Time().from_knx((0xF8, "0x23" ))

    def test_to_knx_wrong_parameter(self):
        with self.assertRaises(ConversionError):
            DPT_Time().to_knx("fnord")


suite = unittest.TestLoader().loadTestsFromTestCase(TestDPT_Time)
unittest.TextTestRunner(verbosity=2).run(suite)
