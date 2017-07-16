import unittest
from unittest.mock import Mock
import asyncio
from xknx.knx import Telegram, DPTTemperature, DPTArray, Address, \
    TelegramType
from xknx import XKNX, Thermostat

class TestThermostat(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    #
    # SUPPORTS TEMPERATURE / SETPOINT
    #
    def test_support_temperature(self):
        xknx = XKNX(loop=self.loop, start=False)
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_temperature='1/2/3')

        self.assertTrue(thermostat.supports_temperature)
        self.assertFalse(thermostat.supports_setpoint)


    def test_support_setpoint(self):
        xknx = XKNX(loop=self.loop, start=False)
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_setpoint='1/2/4')

        self.assertFalse(thermostat.supports_temperature)
        self.assertTrue(thermostat.supports_setpoint)

    #
    # SYNC
    #
    @asyncio.coroutine
    def test_synce(self):
        xknx = XKNX(loop=self.loop, start=False)
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')
        self.loop.run_until_complete(asyncio.Task(thermostat.sync(False)))

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
        xknx = XKNX(loop=self.loop, start=False)
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_temperature='1/2/3')

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        thermostat.process(telegram)

        self.assertEqual(thermostat.temperature, 21.34)


    def test_process_setpoint(self):
        xknx = XKNX(loop=self.loop, start=False)
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
        xknx = XKNX(loop=self.loop, start=False)
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')

        after_update_callback = Mock()
        thermostat.register_device_updated_cb(after_update_callback)

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        thermostat.process(telegram)

        after_update_callback.assert_called_with(thermostat)


    def test_process_callback_setpoint(self):
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop, start=False)
        thermostat = Thermostat(
            xknx,
            'TestThermostat',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')

        after_update_callback = Mock()
        thermostat.register_device_updated_cb(after_update_callback)

        telegram = Telegram(Address('1/2/4'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        thermostat.process(telegram)

        after_update_callback.assert_called_with(thermostat)

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestThermostat)
unittest.TextTestRunner(verbosity=2).run(SUITE)
