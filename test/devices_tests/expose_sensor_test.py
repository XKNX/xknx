"""Unit test for Sensor objects."""
import asyncio
import unittest
from unittest.mock import Mock

from xknx import XKNX
from xknx.devices import ExposeSensor
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import GroupAddress, Telegram, TelegramType


class TestExposeSensor(unittest.TestCase):
    """Test class for Sensor objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # STR FUNCTIONS
    #
    def test_str_binary(self):
        """Test resolve state with binary sensor."""
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            group_address='1/2/3',
            value_type="binary")
        expose_sensor.sensor_value.payload = DPTBinary(1)

        self.assertEqual(expose_sensor.resolve_state(), True)
        self.assertEqual(expose_sensor.unit_of_measurement(), None)

    def test_str_percent(self):
        """Test resolve state with percent sensor."""
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            group_address='1/2/3',
            value_type="percent")
        expose_sensor.sensor_value.payload = DPTArray((0x40,))

        self.assertEqual(expose_sensor.resolve_state(), 25)
        self.assertEqual(expose_sensor.unit_of_measurement(), "%")

    def test_str_temperature(self):
        """Test resolve state with temperature sensor."""
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            group_address='1/2/3',
            value_type="temperature")
        expose_sensor.sensor_value.payload = DPTArray((0x0c, 0x1a))

        self.assertEqual(expose_sensor.resolve_state(), 21.0)
        self.assertEqual(expose_sensor.unit_of_measurement(), "°C")

    #
    # TEST SET
    #
    def test_set_binary(self):
        """Test set with binary sensor."""
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            group_address='1/2/3',
            value_type="binary")
        self.loop.run_until_complete(asyncio.Task(expose_sensor.set(False)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                TelegramType.GROUP_WRITE,
                payload=DPTBinary(0)))

    def test_set_percent(self):
        """Test set with percent sensor."""
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            group_address='1/2/3',
            value_type="percent")
        self.loop.run_until_complete(asyncio.Task(expose_sensor.set(75)))
        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                TelegramType.GROUP_WRITE,
                payload=DPTArray((0xBF,))))

    def test_set_temperature(self):
        """Test set with temperature sensor."""
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            group_address='1/2/3',
            value_type="temperature")
        self.loop.run_until_complete(asyncio.Task(expose_sensor.set(21.0)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                TelegramType.GROUP_WRITE,
                payload=DPTArray((0x0c, 0x1a))))

    #
    # TEST PROCESS (GROUP READ)
    #
    def test_process_binary(self):
        """Test reading binary expose sensor from bus."""
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            value_type='binary',
            group_address='1/2/3')
        expose_sensor.sensor_value.payload = DPTArray(1)

        telegram = Telegram(GroupAddress('1/2/3'))
        telegram.telegramtype = TelegramType.GROUP_READ
        self.loop.run_until_complete(asyncio.Task(expose_sensor.process(telegram)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                TelegramType.GROUP_RESPONSE,
                payload=DPTArray(True)))

    def test_process_percent(self):
        """Test reading percent expose sensor from bus."""
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            value_type='percent',
            group_address='1/2/3')
        expose_sensor.sensor_value.payload = DPTArray((0x40,))

        telegram = Telegram(GroupAddress('1/2/3'))
        telegram.telegramtype = TelegramType.GROUP_READ
        self.loop.run_until_complete(asyncio.Task(expose_sensor.process(telegram)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                TelegramType.GROUP_RESPONSE,
                payload=DPTArray((0x40, ))))

    def test_process_temperature(self):
        """Test reading temperature expose sensor from bus."""
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            value_type='temperature',
            group_address='1/2/3')
        expose_sensor.sensor_value.payload = DPTArray((0x0c, 0x1a))

        telegram = Telegram(GroupAddress('1/2/3'))
        telegram.telegramtype = TelegramType.GROUP_READ
        self.loop.run_until_complete(asyncio.Task(expose_sensor.process(telegram)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                TelegramType.GROUP_RESPONSE,
                payload=DPTArray((0x0c, 0x1a))))

    #
    # HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test expose sensor has group address."""
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            value_type='temperature',
            group_address='1/2/3')
        self.assertTrue(expose_sensor.has_group_address(GroupAddress('1/2/3')))
        self.assertFalse(expose_sensor.has_group_address(GroupAddress('1/2/4')))

    #
    # STATE ADDRESSES
    #
    def test_state_addresses(self):
        """Test expose sensor returns empty list as state addresses."""
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            value_type='temperature',
            group_address='1/2/3')
        self.assertEqual(expose_sensor.state_addresses(), [])

    #
    # PROCESS CALLBACK
    #
    def test_process_callback(self):
        """Test setting value. Test if callback is called."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        expose_sensor = ExposeSensor(
            xknx,
            'TestSensor',
            group_address='1/2/3',
            value_type="temperature")

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        expose_sensor.register_device_updated_cb(async_after_update_callback)

        self.loop.run_until_complete(asyncio.Task(expose_sensor.set(21.0)))
        after_update_callback.assert_called_with(expose_sensor)
