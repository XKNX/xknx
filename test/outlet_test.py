import unittest

from xknx import XKNX,Outlet,Address,Telegram,TelegramType,DPT_Binary

class TestOutlet(unittest.TestCase):

    #
    # SYNC STATE
    #
    def test_sync_state(self):

        xknx = XKNX()
        outlet = Outlet(xknx, "TestOutlet", {'group_address':'1/2/3'})
        outlet.sync_state()

        self.assertEqual( xknx.telegrams.qsize(), 1 )

        telegram = xknx.telegrams.get()
        self.assertEqual( telegram, Telegram(Address('1/2/3'), TelegramType.GROUP_READ) )


    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX()
        outlet = Outlet(xknx, 'TestOutlet', {'group_address':'1/2/3'})

        self.assertEqual( outlet.state, False )

        telegram_on = Telegram()
        telegram_on.payload = DPT_Binary(1)
        outlet.process( telegram_on )

        self.assertEqual( outlet.state, True )

        telegram_off = Telegram()
        telegram_off.payload = DPT_Binary(0)
        outlet.process( telegram_off )

        self.assertEqual( outlet.state, False )

    #
    # TEST SET ON
    #
    def test_set_on(self):
        xknx = XKNX()
        outlet = Outlet(xknx, 'TestOutlet', {'group_address':'1/2/3'})
        outlet.set_on()
        self.assertEqual( xknx.telegrams.qsize(), 1 )
        telegram = xknx.telegrams.get()
        self.assertEqual( telegram, Telegram(Address('1/2/3'),  payload=DPT_Binary(1) ) )

    #
    # TEST SET OFF
    #
    def test_set_off(self):
        xknx = XKNX()
        outlet = Outlet(xknx, 'TestOutlet', {'group_address':'1/2/3'})
        outlet.set_off()
        self.assertEqual( xknx.telegrams.qsize(), 1 )
        telegram = xknx.telegrams.get()
        self.assertEqual( telegram, Telegram(Address('1/2/3'),  payload=DPT_Binary(0) ) )



suite = unittest.TestLoader().loadTestsFromTestCase(TestOutlet)
unittest.TextTestRunner(verbosity=2).run(suite)
