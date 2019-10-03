"""Unit test for Sensor and ExposeSensor objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.devices import BinarySensor, ExposeSensor, Sensor
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import (
    GroupAddress, Telegram, TelegramDirection, TelegramType)


class SensorExposeLoopTest(unittest.TestCase):
    """Process incoming Telegrams and send the values to the bus again."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_array_sensor_loop(self):
        """Test sensor and expose_sensor with different values."""
        test_cases = [
            ('angle', DPTArray((0x0B)), 16),
            ('brightness', DPTArray((0x27, 0x10)), 10000),
            ('color_temperature', DPTArray((0x0D, 0x48)), 3400),
            ('counter_pulses', DPTArray((0x9F)), -97),
            ('current', DPTArray((0x00, 0x03)), 3),
            ('delta_time_hrs', DPTArray((0x04, 0xD2)), 1234),
            ('delta_time_min', DPTArray((0xFB, 0x2E)), -1234),
            ('delta_time_ms', DPTArray((0x7D, 0x00)), 32000),
            ('delta_time_sec', DPTArray((0x83, 0x00)), -32000),
            ('electric_current', DPTArray((0x3D, 0xCC, 0xCC, 0xCD)), 0.1),
            ('electric_potential', DPTArray((0x43, 0xF0, 0xDE, 0xB8)), 481.74),
            ('energy', DPTArray((0x43, 0xE4, 0x00, 0x00)), 456),
            ('enthalpy', DPTArray((0xC1, 0x4E)), -4387.84),
            ('frequency', DPTArray((0x42, 0x46, 0xCC, 0xCD)), 49.7),
            ('heatflowrate', DPTArray((0x42, 0xAE, 0x00, 0x00)), 87),
            ('humidity', DPTArray((0x6C, 0xB6)), 98795.52),
            ('illuminance', DPTArray((0x2F, 0xE9)), 648),
            ('luminous_flux', DPTArray((0x43, 0x87, 0x40, 0x00)), 270.5),
            ('percent', DPTArray((0x26)), 15),
            ('percentU8', DPTArray((0xCD)), 205),
            ('percentV8', DPTArray((0x9A)), -102),
            ('percentV16', DPTArray((0xFF, 0xFF)), -1),
            ('phaseanglerad', DPTArray((0xC1, 0x10, 0x00, 0x00)), -9),
            ('phaseangledeg', DPTArray((0x43, 0x87, 0x40, 0x00)), 270.5),
            ('power', DPTArray((0x42, 0xA9, 0xBD, 0x71)), 84.87),
            ('powerfactor', DPTArray((0x42, 0xA9, 0x6B, 0x85)), 84.71),
            ('ppm', DPTArray((0x00, 0x03)), 0.03),
            ('pressure', DPTArray((0x42, 0xA9, 0x6B, 0x85)), 84.71),
            ('pressure_2byte', DPTArray((0x2E, 0xA9)), 545.6),
            ('pulse', DPTArray((0x11)), 17),
            ('rotation_angle', DPTArray((0xAE, 0xC0)), -20800),
            ('scene_number', DPTArray((0x00)), 1),
            ('speed', DPTArray((0x00, 0x00, 0x00, 0x00)), 0),
            ('speed_ms', DPTArray((0x0E, 0xA4)), 34),
            ('string',
             DPTArray((0x4B, 0x4E, 0x58, 0x20, 0x69, 0x73, 0x20, 0x4F,
                       0x4B, 0x00, 0x00, 0x00, 0x00, 0x00)),
             "KNX is OK"),
            ('temperature', DPTArray((0x03, 0x12)), 7.86),
            ('voltage', DPTArray((0x07, 0x9A)), 19.46),
            # Generic DPT Without Min/Max and Unit.
            ('DPT-5', DPTArray((0x1F)), 31),
            ('1byte_unsigned', DPTArray((0x08)), 8),
            ('DPT-7', DPTArray((0xD4, 0x31)), 54321),
            ('2byte_unsigned', DPTArray((0x30, 0x39)), 12345),
            ('DPT-8', DPTArray((0x80, 0x44)), -32700),
            ('2byte_signed', DPTArray((0x00, 0x01)), 1),
            ('DPT-9', DPTArray((0x2E, 0xA9)), 545.6),
            ('DPT-12', DPTArray((0x07, 0x5B, 0xCD, 0x15)), 123456789),
            ('4byte_unsigned', DPTArray((0x00, 0x00, 0x00, 0x00)), 0),
            ('DPT-13', DPTArray((0x02, 0xE5, 0x5E, 0xF7)), 48586487),
            ('4byte_signed', DPTArray((0xFD, 0x1A, 0xA1, 0x09)), -48586487),
            ('DPT-14', DPTArray((0x47, 0xC0, 0xF7, 0x20)), 98798.25),
            ('4byte_float', DPTArray((0xC2, 0x09, 0xEE, 0xCC)), -34.4832),
        ]

        for value_type, test_payload, test_value in test_cases:
            with self.subTest(value_type=value_type):
                xknx = XKNX(loop=self.loop)
                sensor = Sensor(
                    xknx,
                    'TestSensor_%s' % value_type,
                    group_address_state='1/1/1',
                    value_type=value_type
                )
                expose = ExposeSensor(
                    xknx,
                    'TestExpose_%s' % value_type,
                    group_address='2/2/2',
                    value_type=value_type
                )

                incoming_telegram = Telegram(GroupAddress('1/1/1'),
                                             TelegramType.GROUP_WRITE,
                                             direction=TelegramDirection.INCOMING,
                                             payload=test_payload)
                self.loop.run_until_complete(asyncio.Task(sensor.process(incoming_telegram)))
                incoming_value = sensor.resolve_state()
                if isinstance(test_value, float):
                    self.assertEqual(round(incoming_value, 4), test_value)
                else:
                    self.assertEqual(incoming_value, test_value)

                # HA sends strings for new values
                stringified_value = str(test_value)
                self.loop.run_until_complete(asyncio.Task(expose.set(stringified_value)))
                self.assertEqual(xknx.telegrams.qsize(), 1)
                outgoing_telegram = xknx.telegrams.get_nowait()
                self.assertEqual(
                    outgoing_telegram,
                    Telegram(
                        GroupAddress('2/2/2'),
                        TelegramType.GROUP_WRITE,
                        direction=TelegramDirection.OUTGOING,
                        payload=test_payload))

    def test_binary_sensor_loop(self):
        """Test binary_sensor and expose_sensor with binary values."""
        test_cases = [
            ('binary', DPTBinary(0), False),
            ('binary', DPTBinary(1), True),
        ]

        for value_type, test_payload, test_value in test_cases:
            with self.subTest(value_type=value_type):
                xknx = XKNX(loop=self.loop)
                sensor = BinarySensor(
                    xknx,
                    'TestSensor_%s' % value_type,
                    group_address_state='1/1/1'
                )
                expose = ExposeSensor(
                    xknx,
                    'TestExpose_%s' % value_type,
                    group_address='2/2/2',
                    value_type=value_type
                )

                incoming_telegram = Telegram(GroupAddress('1/1/1'),
                                             TelegramType.GROUP_WRITE,
                                             direction=TelegramDirection.INCOMING,
                                             payload=test_payload)
                self.loop.run_until_complete(asyncio.Task(sensor.process(incoming_telegram)))
                incoming_value = sensor.is_on()
                self.assertEqual(incoming_value, test_value)

                self.loop.run_until_complete(asyncio.Task(expose.set(test_value)))
                self.assertEqual(xknx.telegrams.qsize(), 1)
                outgoing_telegram = xknx.telegrams.get_nowait()
                self.assertEqual(
                    outgoing_telegram,
                    Telegram(
                        GroupAddress('2/2/2'),
                        TelegramType.GROUP_WRITE,
                        direction=TelegramDirection.OUTGOING,
                        payload=test_payload))
