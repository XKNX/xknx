import unittest
from unittest.mock import Mock

from xknx.knx import Telegram, DPTTemperature, DPTArray, Address, \
    TelegramType
from xknx import XKNX, Thermostat

class TestThermostat(unittest.TestCase):

    #
    # SUPPORTS TEMPERATURE / SETPOINT
    #
    def test_support_temperature(self):
        xknx = XKNX()
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_temperature='1/2/3')

        self.assertTrue(thermostat.supports_temperature)
        self.assertFalse(thermostat.supports_setpoint)


    def test_support_setpoint(self):
        xknx = XKNX()
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_setpoint='1/2/4')

        self.assertFalse(thermostat.supports_temperature)
        self.assertTrue(thermostat.supports_setpoint)

    #
    # SYNC STATE
    #
    def test_sync_state(self):
        xknx = XKNX()
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')
        thermostat.sync_state()

        self.assertEqual(xknx.telegrams.qsize(), 2)

        telegram1 = xknx.telegrams.get()
        self.assertEqual(telegram1,
                         Telegram(Address('1/2/3'), TelegramType.GROUP_READ))

        telegram2 = xknx.telegrams.get()
        self.assertEqual(telegram2,
                         Telegram(Address('1/2/4'), TelegramType.GROUP_READ))

    #
    # TEST PROCESS
    #
    def test_process_temperature(self):
        xknx = XKNX()
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_temperature='1/2/3')

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        thermostat.process(telegram)

        self.assertEqual(thermostat.temperature, 21.34)


    def test_process_setpoint(self):
        xknx = XKNX()
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_setpoint='1/2/3')

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        thermostat.process(telegram)

        self.assertEqual(thermostat.setpoint, 21.34)


    def test_process_callback_temp(self):
        # pylint: disable=no-self-use
        xknx = XKNX()
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')

        after_update_callback = Mock()
        thermostat.after_update_callback = after_update_callback

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        thermostat.process(telegram)

        after_update_callback.assert_called_with(thermostat)


    def test_process_callback_setpoint(self):
        # pylint: disable=no-self-use
        xknx = XKNX()
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')

        after_update_callback = Mock()
        thermostat.after_update_callback = after_update_callback

        telegram = Telegram(Address('1/2/4'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        thermostat.process(telegram)

        after_update_callback.assert_called_with(thermostat)

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestThermostat)
unittest.TextTestRunner(verbosity=2).run(SUITE)
