import unittest
from unittest.mock import Mock
import asyncio
from xknx.knx import Telegram, DPTTemperature, DPTArray, Address, \
    TelegramType
from xknx import XKNX, Climate

class TestClimate(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    #
    # SUPPORTS TEMPERATURE / SETPOINT
    #
    def test_support_temperature(self):
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3')

        self.assertTrue(climate.supports_temperature)
        self.assertFalse(climate.supports_setpoint)


    def test_support_setpoint(self):
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_setpoint='1/2/4')

        self.assertFalse(climate.supports_temperature)
        self.assertTrue(climate.supports_setpoint)

    #
    # SYNC
    #
    @asyncio.coroutine
    def test_synce(self):
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')
        self.loop.run_until_complete(asyncio.Task(climate.sync(False)))

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
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3')

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        climate.process(telegram)

        self.assertEqual(climate.temperature, 21.34)


    def test_process_setpoint(self):
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_setpoint='1/2/3')

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        climate.process(telegram)

        self.assertEqual(climate.setpoint, 21.34)


    def test_process_callback_temp(self):
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')

        after_update_callback = Mock()
        climate.register_device_updated_cb(after_update_callback)

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        climate.process(telegram)

        after_update_callback.assert_called_with(climate)


    def test_process_callback_setpoint(self):
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')

        after_update_callback = Mock()
        climate.register_device_updated_cb(after_update_callback)

        telegram = Telegram(Address('1/2/4'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        climate.process(telegram)

        after_update_callback.assert_called_with(climate)

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestClimate)
unittest.TextTestRunner(verbosity=2).run(SUITE)
