import unittest

from xknx import XKNX,Shutter,Telegram,Address,TelegramType,DPT_Binary,DPT_Array

class TestShutter(unittest.TestCase):

    #
    # REQUEST STATE
    #
    def test_request_state(self):
        xknx = XKNX()
        shutter = Shutter(xknx, 'TestShutter', {'group_address_long':'1/2/1','group_address_short':'1/2/2','group_address_position':'1/2/3','group_address_position_feedback':'1/2/4'})
        shutter.request_state()
        self.assertEqual( xknx.telegrams.qsize(), 1 )
        telegram1 = xknx.telegrams.get()
        self.assertEqual( telegram1, Telegram(Address('1/2/4'), TelegramType.GROUP_READ) )


    #
    # TEST SET UP
    #
    def test_set_up(self):
        xknx = XKNX()
        shutter = Shutter(xknx, 'TestShutter', {'group_address_long':'1/2/1','group_address_short':'1/2/2','group_address_position':'1/2/3','group_address_position_feedback':'1/2/4'})
        shutter.set_up()
        self.assertEqual( xknx.telegrams.qsize(), 1 )
        telegram = xknx.telegrams.get()
        self.assertEqual( telegram, Telegram(Address('1/2/1'),  payload=DPT_Binary(0) ) )


    #
    # TEST SET DOWN 
    #
    def test_set_short_down(self):
        xknx = XKNX()
        shutter = Shutter(xknx, 'TestShutter', {'group_address_long':'1/2/1','group_address_short':'1/2/2','group_address_position':'1/2/3','group_address_position_feedback':'1/2/4'})
        shutter.set_down()
        self.assertEqual( xknx.telegrams.qsize(), 1 )
        telegram = xknx.telegrams.get()
        self.assertEqual( telegram, Telegram(Address('1/2/1'),  payload=DPT_Binary(1) ) )


    #
    # TEST SET SHORT UP
    #
    def test_set_short_up(self):
        xknx = XKNX()
        shutter = Shutter(xknx, 'TestShutter', {'group_address_long':'1/2/1','group_address_short':'1/2/2','group_address_position':'1/2/3','group_address_position_feedback':'1/2/4'})
        shutter.set_short_up()
        self.assertEqual( xknx.telegrams.qsize(), 1 )
        telegram = xknx.telegrams.get()
        self.assertEqual( telegram, Telegram(Address('1/2/2'),  payload=DPT_Binary(0) ) )


    #
    # TEST SET SHORT DOWN 
    #
    def test_set_down(self):
        xknx = XKNX()
        shutter = Shutter(xknx, 'TestShutter', {'group_address_long':'1/2/1','group_address_short':'1/2/2','group_address_position':'1/2/3','group_address_position_feedback':'1/2/4'})
        shutter.set_short_down()
        self.assertEqual( xknx.telegrams.qsize(), 1 )
        telegram = xknx.telegrams.get()
        self.assertEqual( telegram, Telegram(Address('1/2/2'),  payload=DPT_Binary(1) ) )


    #
    # TEST STOP
    #
    def test_stop(self):
        xknx = XKNX()
        shutter = Shutter(xknx, 'TestShutter', {'group_address_long':'1/2/1','group_address_short':'1/2/2','group_address_position':'1/2/3','group_address_position_feedback':'1/2/4'})
        shutter.stop()
        self.assertEqual( xknx.telegrams.qsize(), 1 )
        telegram = xknx.telegrams.get()
        self.assertEqual( telegram, Telegram(Address('1/2/2'),  payload=DPT_Binary(1) ) )


    #
    # TEST POSITION
    #
    def test_position(self):
        xknx = XKNX()
        shutter = Shutter(xknx, 'TestShutter', {'group_address_long':'1/2/1','group_address_short':'1/2/2','group_address_position':'1/2/3','group_address_position_feedback':'1/2/4'})
        shutter.set_position(50) 
        self.assertEqual( xknx.telegrams.qsize(), 1 )
        telegram = xknx.telegrams.get()
        self.assertEqual( telegram, Telegram(Address('1/2/3'),  payload=DPT_Array(50) ) )


    def test_position_without_position_address_up(self):
        xknx = XKNX()
        shutter = Shutter(xknx, 'TestShutter', {'group_address_long':'1/2/1','group_address_short':'1/2/2','group_address_position_feedback':'1/2/4'})
        shutter.travelcalculator.set_position(40)
        shutter.set_position(50)
        self.assertEqual( xknx.telegrams.qsize(), 1 )
        telegram = xknx.telegrams.get()
        self.assertEqual( telegram, Telegram(Address('1/2/1'),  payload=DPT_Binary(1) ) )


    def test_position_without_position_address_down(self):
        xknx = XKNX()
        shutter = Shutter(xknx, 'TestShutter', {'group_address_long':'1/2/1','group_address_short':'1/2/2','group_address_position_feedback':'1/2/4'})
        shutter.travelcalculator.set_position(100)
        shutter.set_position(50)
        self.assertEqual( xknx.telegrams.qsize(), 1 )
        telegram = xknx.telegrams.get()
        self.assertEqual( telegram, Telegram(Address('1/2/1'),  payload=DPT_Binary(0) ) )


    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX()
        shutter = Shutter(xknx, 'TestShutter', {'group_address_long':'1/2/1','group_address_short':'1/2/2','group_address_position':'1/2/3','group_address_position_feedback':'1/2/4'})

        telegram = Telegram(Address('1/2/4'), payload = DPT_Array(42))
        shutter.process( telegram )

        self.assertEqual( shutter.current_position(), 42 )


suite = unittest.TestLoader().loadTestsFromTestCase(TestShutter)
unittest.TextTestRunner(verbosity=2).run(suite)
