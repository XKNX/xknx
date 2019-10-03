"""Unit test for Sensor objects."""
import asyncio
import unittest
from unittest.mock import Mock

from xknx import XKNX
from xknx.devices import Sensor
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram, TelegramType


class TestSensor(unittest.TestCase):
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
    def test_str_scaling(self):
        """Test resolve state with percent sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="percent")
        sensor.sensor_value.payload = DPTArray((0x40,))

        self.assertEqual(sensor.resolve_state(), 25)
        self.assertEqual(sensor.unit_of_measurement(), "%")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_speed_ms(self):
        """Test resolve state with speed_ms sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="speed_ms")
        sensor.sensor_value.payload = DPTArray((0x00, 0x1b,))

        self.assertEqual(sensor.resolve_state(), 0.27)
        self.assertEqual(sensor.unit_of_measurement(), "m/s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_temp(self):
        """Test resolve state with temperature sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="temperature")
        sensor.sensor_value.payload = DPTArray((0x0c, 0x1a))

        self.assertEqual(sensor.resolve_state(), 21.00)
        self.assertEqual(sensor.unit_of_measurement(), "°C")
        self.assertEqual(sensor.ha_device_class(), "temperature")

    def test_str_humidity(self):
        """Test resolve state with humidity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="humidity")
        sensor.sensor_value.payload = DPTArray((0x0e, 0x73))

        self.assertEqual(sensor.resolve_state(), 33.02)
        self.assertEqual(sensor.unit_of_measurement(), "%")
        self.assertEqual(sensor.ha_device_class(), "humidity")

    def test_str_power(self):
        """Test resolve state with power sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="power")
        sensor.sensor_value.payload = DPTArray((0x43, 0xC6, 0x80, 00))

        self.assertEqual(sensor.resolve_state(), 397)
        self.assertEqual(sensor.unit_of_measurement(), "W")
        self.assertEqual(sensor.ha_device_class(), "power")

    def test_str_electric_potential(self):
        """Test resolve state with voltage sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_potential")
        sensor.sensor_value.payload = DPTArray((0x43, 0x65, 0xE3, 0xD7))

        self.assertEqual(round(sensor.resolve_state(), 2), 229.89)
        self.assertEqual(sensor.unit_of_measurement(), "V")

    #
    # SYNC
    #
    def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            value_type="temperature",
            group_address_state='1/2/3')

        self.loop.run_until_complete(asyncio.Task(sensor.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ))

    def test_sync_passive(self):
        """Test sync function / not sending group reads to KNX bus."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            value_type="temperature",
            group_address_state='1/2/3',
            sync_state=False)

        self.loop.run_until_complete(asyncio.Task(sensor.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 0)

        with self.assertRaises(asyncio.queues.QueueEmpty):
            xknx.telegrams.get_nowait()

    #
    # HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test sensor has group address."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            value_type='temperature',
            group_address_state='1/2/3')
        self.assertTrue(sensor.has_group_address(GroupAddress('1/2/3')))
        self.assertFalse(sensor.has_group_address(GroupAddress('1/2/4')))

    #
    # STATE ADDRESSES
    #
    def test_state_addresses(self):
        """Test state addresses of sensor object."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            value_type='temperature',
            group_address_state='1/2/3')
        self.assertEqual(sensor.state_addresses(), [GroupAddress('1/2/3')])

    def test_state_addresses_passive(self):
        """Test state addresses of passive sensor object."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            value_type='temperature',
            group_address_state='1/2/3',
            sync_state=False)
        self.assertEqual(sensor.state_addresses(), [])

    #
    # TEST PROCESS
    #
    def test_process(self):
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            value_type='temperature',
            group_address_state='1/2/3')

        telegram = Telegram(GroupAddress('1/2/3'))
        telegram.payload = DPTArray((0x06, 0xa0))
        self.loop.run_until_complete(asyncio.Task(sensor.process(telegram)))
        self.assertEqual(sensor.sensor_value.payload, DPTArray((0x06, 0xa0)))
        self.assertEqual(sensor.resolve_state(), 16.96)

    def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback is called."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="temperature")

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        sensor.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(GroupAddress('1/2/3'))
        telegram.payload = DPTArray((0x01, 0x02))
        self.loop.run_until_complete(asyncio.Task(sensor.process(telegram)))
        after_update_callback.assert_called_with(sensor)
