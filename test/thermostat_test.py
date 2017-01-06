import unittest

from xknx import XKNX, Thermostat, Telegram, DPTTemperature, DPTArray

class TestThermostat(unittest.TestCase):


    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX()
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            {'group_address':'1/2/3'})

        telegram = Telegram()
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        thermostat.process(telegram)

        self.assertEqual(thermostat.temperature, 21.34)




SUITE = unittest.TestLoader().loadTestsFromTestCase(TestThermostat)
unittest.TextTestRunner(verbosity=2).run(SUITE)
