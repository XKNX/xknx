"""Unit test for Climate objects."""
import unittest
from unittest.mock import Mock
import asyncio
from xknx.knx import Telegram, DPTTemperature, DPTArray, Address, \
    TelegramType
from xknx import XKNX
from xknx.devices import Climate

class TestClimate(unittest.TestCase):
    """Test class for Climate objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # SUPPORTS TEMPERATURE / SETPOINT
    #
    def test_support_temperature(self):
        """Test supports_temperature flag."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3')

        self.assertTrue(climate.supports_temperature)
        self.assertFalse(climate.supports_setpoint)


    def test_support_setpoint(self):
        """Test supports_setpoint flag."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_setpoint='1/2/4')

        self.assertFalse(climate.supports_temperature)
        self.assertTrue(climate.supports_setpoint)

    #
    # TEST CALLBACK
    #
    def test_process_callback(self):
        """Test if after_update_callback is called after update of Climate object."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_setpoint='1/2/4')

        after_update_callback = Mock()
        @asyncio.coroutine
        def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        climate.register_device_updated_cb(async_after_update_callback)

        self.loop.run_until_complete(asyncio.Task(climate.set_setpoint(23)))
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

        self.loop.run_until_complete(asyncio.Task(climate.set_setpoint(24)))
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

        self.loop.run_until_complete(asyncio.Task(climate.set_setpoint(24)))
        after_update_callback.assert_not_called()


    # TEST SET SETPOINT
    #
    def test_set_setpoint(self):
        """Test set_setpoint."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')
        self.loop.run_until_complete(asyncio.Task(climate.set_setpoint(23)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/4'), payload=DPTArray(23)))

    def test_set_setpoint_no_setpoint(self):
        """Test set_sepoint with no setpoint defined."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3')
        self.loop.run_until_complete(asyncio.Task(climate.set_setpoint(23)))
        self.assertEqual(xknx.telegrams.qsize(), 0)

    @asyncio.coroutine
    def test_synce(self):
        """Test sync function / sending group reads to KNX bus."""
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
        """Test process / reading telegrams from telegram queue. Test if temperature is processed correctly."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3')

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))

        self.assertEqual(climate.temperature, 21.34)


    def test_process_setpoint(self):
        """Test process / reading telegrams from telegram queue. Test if setpoint is processed correctly."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_setpoint='1/2/3')

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))

        self.assertEqual(climate.setpoint, 21.34)


    def test_process_callback_temp(self):
        """Test process / reading telegrams from telegram queue. Test if callback is executed when receiving temperature."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')

        after_update_callback = Mock()
        @asyncio.coroutine
        def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        climate.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))

        after_update_callback.assert_called_with(climate)


    def test_process_callback_setpoint(self):
        """Test process / reading telegrams from telegram queue. Test if callback is executed when receiving setpoint."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3',
            group_address_setpoint='1/2/4')

        after_update_callback = Mock()
        @asyncio.coroutine
        def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        climate.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(Address('1/2/4'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))

        after_update_callback.assert_called_with(climate)

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestClimate)
unittest.TextTestRunner(verbosity=2).run(SUITE)
