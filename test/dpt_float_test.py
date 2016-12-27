import unittest

from xknx import DPT_Float,ConversionError

class TestDPT_Float(unittest.TestCase):

    def test_value_from_documentation(self):
        self.assertEqual( DPT_Float().to_knx(-30.00),(0x8a, 0x24 ))
        self.assertEqual( DPT_Float().from_knx((0x8a, 0x24 )), -30.00 )

    def test_value_taken_from_live_thermostat(self):
        self.assertEqual( DPT_Float().to_knx( 16.96),(0x06, 0xa0 ))
        self.assertEqual( DPT_Float().from_knx((0x06, 0xa0 )),  16.96 )

    def test_zero_value(self):
        self.assertEqual( DPT_Float().to_knx(  0.00),(0x00, 0x00 ))
        self.assertEqual( DPT_Float().from_knx((0x00, 0x00 )),   0.00 )

    def test_room_temperature(self):
        self.assertEqual( DPT_Float().to_knx( 21.00),(0x0c, 0x1a ))
        self.assertEqual( DPT_Float().from_knx((0x0c, 0x1a )),  21.00 )

    def test_high_temperature(self):
        self.assertEqual( DPT_Float().to_knx( 500.00),( 0x2E, 0x1A ))
        self.assertAlmostEqual( DPT_Float().from_knx((0x2E, 0x1A )),  499.84 )
        self.assertAlmostEqual( DPT_Float().from_knx((0x2E, 0x1B )),  500.16 )
        self.assertEqual( DPT_Float().to_knx( 499.84),( 0x2E, 0x1A ))
        self.assertEqual( DPT_Float().to_knx( 500.16),( 0x2E, 0x1B ))

    def test_minor_negative_temperature(self):
        self.assertEqual( DPT_Float().to_knx( -10.00),(0x84, 0x18))
        self.assertEqual( DPT_Float().from_knx((0x84, 0x18 )),   -10.00 )

    def test_very_cold_temperature(self):
        self.assertEqual( DPT_Float().to_knx( -1000.00),(0xB1,0xE6))
        self.assertEqual( DPT_Float().from_knx((0xB1, 0xE6 )),  -999.68 )
        self.assertEqual( DPT_Float().from_knx((0xB1, 0xE5 )),  -1000.32 )
        self.assertEqual( DPT_Float().to_knx( -999.68),(0xB1,0xE6))
        self.assertEqual( DPT_Float().to_knx( -1000.32),(0xB1,0xE5))

    def test_max(self):
        self.assertEqual( DPT_Float().to_knx( DPT_Float.value_max ), (0x7F, 0xFF) )
        self.assertEqual( DPT_Float().from_knx((0x7F, 0xFF)), DPT_Float.value_max )

    def test_min(self):
        self.assertEqual( DPT_Float().to_knx( DPT_Float.value_min ), (0xF8, 0x00) )
        self.assertEqual( DPT_Float().from_knx((0xF8, 0x00)), DPT_Float.value_min )

    def test_close_to_max(self):
        self.assertEqual( DPT_Float().to_knx( 670433.28 ), (0x7F, 0xFE) )
        self.assertEqual( DPT_Float().from_knx((0x7F, 0xFE)), 670433.28 )

    def test_close_to_min(self):
        self.assertEqual( DPT_Float().to_knx( -670760.96 ), (0xF8, 0x01))
        self.assertEqual( DPT_Float().from_knx((0xF8, 0x01)), -670760.96 )

    def test_to_knx_min_exceeded(self):
        with self.assertRaises(ConversionError):
            DPT_Float().to_knx( DPT_Float.value_min - 1 )

    def test_to_knx_max_exceeded(self):
        with self.assertRaises(ConversionError):
            DPT_Float().to_knx( DPT_Float.value_max + 1 )

    def test_to_knx_wrong_parameter(self):
        with self.assertRaises(ConversionError):
            DPT_Float().to_knx( "fnord" )

    def test_from_knx_wrong_parameter(self):
        with self.assertRaises(ConversionError):
            DPT_Float().from_knx((0xF8, 0x01, 0x23 ))

    def test_from_knx_wrong_parameter2(self):
        with self.assertRaises(ConversionError):
            DPT_Float().from_knx((0xF8, "0x23" ))

suite = unittest.TestLoader().loadTestsFromTestCase(TestDPT_Float)
unittest.TextTestRunner(verbosity=2).run(suite)
