import unittest

from xknx import XKNX,Thermostat,Address,Telegram,TelegramType,DPT_Temperature,DPT_Array

class TestThermostat(unittest.TestCase):


    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX()
        thermostat = Thermostat(xknx, 'TestThermostat', {'group_address':'1/2/3'})

        telegram = Telegram()
        telegram.payload = DPT_Array( DPT_Temperature().to_knx(21.34) )
        thermostat.process( telegram )

        self.assertEqual( thermostat.temperature, 21.34 )




suite = unittest.TestLoader().loadTestsFromTestCase(TestThermostat)
unittest.TextTestRunner(verbosity=2).run(suite)
