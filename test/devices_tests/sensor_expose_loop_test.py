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
            ('absolute_temperature', DPTArray((0x44, 0xD7, 0xD2, 0x8B,)), 1726.5795),
            ('acceleration', DPTArray((0x45, 0x94, 0xD8, 0x5D,)), 4763.0454),
            ('acceleration_angular', DPTArray((0x45, 0xEA, 0x62, 0x34,)), 7500.2754),
            ('activation_energy', DPTArray((0x46, 0x0, 0x3E, 0xEE,)), 8207.7324),
            ('active_energy', DPTArray((0x26, 0x37, 0x49, 0x7F,)), 641157503),
            ('active_energy_kwh', DPTArray((0x37, 0x5, 0x5, 0xEA,)), 923076074),
            ('activity', DPTArray((0x45, 0x76, 0x0, 0xA3,)), 3936.0398),
            ('amplitude', DPTArray((0x45, 0x9A, 0xED, 0x8,)), 4957.6289),
            ('angle', DPTArray((0xE4,)), 322),
            ('angle_deg', DPTArray((0x44, 0x5C, 0x20, 0x2B,)), 880.5026),
            ('angle_rad', DPTArray((0x44, 0x36, 0x75, 0x1,)), 729.8282),
            ('angular_frequency', DPTArray((0x43, 0xBC, 0x20, 0x8D,)), 376.2543),
            ('angular_momentum', DPTArray((0xC2, 0x75, 0xB7, 0xB5,)), -61.4294),
            ('angular_velocity', DPTArray((0xC4, 0xD9, 0x10, 0xB3,)), -1736.5219),
            ('apparant_energy', DPTArray((0xD3, 0xBD, 0x1E, 0xA5,)), -742580571),
            ('apparant_energy_kvah', DPTArray((0x49, 0x40, 0xC9, 0x9,)), 1228982537),
            ('area', DPTArray((0x45, 0x63, 0x1E, 0xCD,)), 3633.9250),
            ('brightness', DPTArray((0xC3, 0x56,)), 50006),
            ('capacitance', DPTArray((0x45, 0xC9, 0x1D, 0x9D,)), 6435.7017),
            ('charge_density_surface', DPTArray((0x45, 0xDB, 0x66, 0x99,)), 7020.8247),
            ('charge_density_volume', DPTArray((0xC4, 0x8C, 0x33, 0xD7,)), -1121.6200),
            ('color_temperature', DPTArray((0x6C, 0x95,)), 27797),
            ('common_temperature', DPTArray((0x45, 0xD9, 0xC6, 0x3F,)), 6968.7808),
            ('compressibility', DPTArray((0x45, 0x89, 0x94, 0xAB,)), 4402.5835),
            ('conductance', DPTArray((0x45, 0xA6, 0x28, 0xF9,)), 5317.1216),
            ('counter_pulses', DPTArray((0x9D,)), -99),
            ('current', DPTArray((0xCA, 0xCC,)), 51916),
            ('delta_time_hrs', DPTArray((0x47, 0x80,)), 18304),
            ('delta_time_min', DPTArray((0xB9, 0x7B,)), -18053),
            ('delta_time_ms', DPTArray((0x58, 0x77,)), 22647),
            ('delta_time_sec', DPTArray((0xA3, 0x6A,)), -23702),
            ('density', DPTArray((0x44, 0xA5, 0xCB, 0x27,)), 1326.3485),
            ('electrical_conductivity', DPTArray((0xC4, 0xC6, 0xF5, 0x6E,)), -1591.6697),
            ('electric_charge', DPTArray((0x46, 0x14, 0xF6, 0xA0,)), 9533.6562),
            ('electric_current', DPTArray((0x45, 0xAD, 0x45, 0x90,)), 5544.6953),
            ('electric_current_density', DPTArray((0x45, 0x7C, 0x57, 0xF6,)), 4037.4976),
            ('electric_dipole_moment', DPTArray((0x45, 0x58, 0xF1, 0x73,)), 3471.0906),
            ('electric_displacement', DPTArray((0xC5, 0x34, 0x8B, 0x0,)), -2888.6875),
            ('electric_field_strength', DPTArray((0xC6, 0x17, 0x1C, 0x39,)), -9671.0557),
            ('electric_flux', DPTArray((0x45, 0x8F, 0x6C, 0xFD,)), 4589.6235),
            ('electric_flux_density', DPTArray((0xC6, 0x0, 0x50, 0xA8,)), -8212.1641),
            ('electric_polarization', DPTArray((0x45, 0xF8, 0x89, 0xC6,)), 7953.2217),
            ('electric_potential', DPTArray((0xC6, 0x18, 0xA4, 0xAF,)), -9769.1709),
            ('electric_potential_difference', DPTArray((0xC6, 0xF, 0x1D, 0x6,)), -9159.2559),
            ('electromagnetic_moment', DPTArray((0x45, 0x82, 0x48, 0xAE,)), 4169.0850),
            ('electromotive_force', DPTArray((0x45, 0xBC, 0xEF, 0xEB,)), 6045.9897),
            ('energy', DPTArray((0x45, 0x4B, 0xB3, 0xF8,)), 3259.2480),
            ('enthalpy', DPTArray((0x76, 0xDD,)), 287866.88),
            ('flow_rate_m3h', DPTArray((0x99, 0xEA, 0xC0, 0x55,)), -1712668587),
            ('force', DPTArray((0x45, 0x9E, 0x2C, 0xE1,)), 5061.6099),
            ('frequency', DPTArray((0x45, 0xC2, 0x3C, 0x44,)), 6215.5332),
            ('heatcapacity', DPTArray((0xC5, 0xB3, 0x56, 0x7E,)), -5738.8115),
            ('heatflowrate', DPTArray((0x44, 0xEC, 0x80, 0x7A,)), 1892.0149),
            ('heat_quantity', DPTArray((0xC5, 0xA6, 0xB6, 0xD5,)), -5334.8540),
            ('humidity', DPTArray((0x7E, 0xE1,)), 577044.48),
            ('impedance', DPTArray((0x45, 0xDD, 0x79, 0x6D,)), 7087.1782),
            ('illuminance', DPTArray((0x7C, 0x5E,)), 366346.24),
            ('kelvin_per_percent', DPTArray((0xFA, 0xBD,)), -441384.96),
            ('length', DPTArray((0xC5, 0x9D, 0xAE, 0xC5,)), -5045.8462),
            ('length_mm', DPTArray((0x56, 0xB9,)), 22201),
            ('light_quantity', DPTArray((0x45, 0x4A, 0xF5, 0x68,)), 3247.3379),
            ('long_delta_timesec', DPTArray((0x45, 0xB2, 0x17, 0x54,)), 1169299284),
            ('luminance', DPTArray((0x45, 0x18, 0xD9, 0x76,)), 2445.5913),
            ('luminous_flux', DPTArray((0x45, 0xBD, 0x16, 0x9,)), 6050.7544),
            ('luminous_intensity', DPTArray((0x46, 0xB, 0xBE, 0x7E,)), 8943.6230),
            ('magnetic_field_strength', DPTArray((0x44, 0x15, 0xF1, 0xAD,)), 599.7762),
            ('magnetic_flux', DPTArray((0xC5, 0xCB, 0x3C, 0x98,)), -6503.5742),
            ('magnetic_flux_density', DPTArray((0x45, 0xB6, 0xBD, 0x42,)), 5847.6572),
            ('magnetic_moment', DPTArray((0xC3, 0x8E, 0x7F, 0x73,)), -284.9957),
            ('magnetic_polarization', DPTArray((0x45, 0x8C, 0xFA, 0xCB,)), 4511.3491),
            ('magnetization', DPTArray((0x45, 0xF7, 0x9D, 0xA2,)), 7923.7041),
            ('magnetomotive_force', DPTArray((0xC6, 0x4, 0xC2, 0xDA,)), -8496.7129),
            ('mass', DPTArray((0x45, 0x8F, 0x70, 0xA4,)), 4590.0801),
            ('mass_flux', DPTArray((0xC6, 0x7, 0x34, 0xFF,)), -8653.2490),
            ('mol', DPTArray((0xC4, 0xA0, 0xF4, 0x68,)), -1287.6377),
            ('momentum', DPTArray((0xC5, 0x27, 0xAA, 0x5B,)), -2682.6472),
            ('percent', DPTArray((0xE3,)), 89),
            ('percentU8', DPTArray((0x6B,)), 107),
            ('percentV8', DPTArray((0x20,)), 32),
            ('percentV16', DPTArray((0x8A, 0x2F,)), -30161),
            ('phaseanglerad', DPTArray((0x45, 0x54, 0xAC, 0x2E,)), 3402.7612),
            ('phaseangledeg', DPTArray((0xC5, 0x25, 0x13, 0x38,)), -2641.2012),
            ('power', DPTArray((0x45, 0xCB, 0xE2, 0x5C,)), 6524.2949),
            ('power_2byte', DPTArray((0x6D, 0x91,)), 116736.00),
            ('power_density', DPTArray((0x65, 0x3E,)), 54968.32),
            ('powerfactor', DPTArray((0xC5, 0x35, 0x28, 0x21,)), -2898.5081),
            ('ppm', DPTArray((0xF3, 0xC8)), -176947.20),
            ('pressure', DPTArray((0xC5, 0xE6, 0xE6, 0x63,)), -7388.7983),
            ('pressure_2byte', DPTArray((0x7C, 0xF4,)), 415498.24),
            ('pulse', DPTArray((0xFC,)), 252),
            ('rain_amount', DPTArray((0xF0, 0x1)), -335380.48),
            ('reactance', DPTArray((0x45, 0xB0, 0x50, 0x91,)), 5642.0708),
            ('reactive_energy', DPTArray((0x1A, 0x49, 0x6D, 0xA7,)), 441019815),
            ('reactive_energy_kvarh', DPTArray((0xCC, 0x62, 0x5, 0x31,)), -865991375),
            ('resistance', DPTArray((0xC5, 0xFC, 0x5F, 0xC2,)), -8075.9697),
            ('resistivity', DPTArray((0xC5, 0x57, 0x76, 0xC3,)), -3447.4226),
            ('rotation_angle', DPTArray((0x2D, 0xDC,)), 11740),
            ('scene_number', DPTArray((0x1,)), 2),
            ('self_inductance', DPTArray((0xC4, 0xA1, 0xB0, 0x6,)), -1293.5007),
            ('solid_angle', DPTArray((0xC5, 0xC6, 0xE5, 0x47,)), -6364.6597),
            ('sound_intensity', DPTArray((0xC4, 0xF2, 0x56, 0xE6,)), -1938.7156),
            ('speed', DPTArray((0xC5, 0xCD, 0x1C, 0x6A,)), -6563.5518),
            ('stress', DPTArray((0x45, 0xDC, 0xA8, 0xF2,)), 7061.1182),
            ('surface_tension', DPTArray((0x46, 0xB, 0xAC, 0x11,)), 8939.0166),
            ('string', DPTArray((0x4B, 0x4E, 0x58, 0x20, 0x69, 0x73, 0x20, 0x4F, 0x4B, 0x0, 0x0, 0x0, 0x0, 0x0,)),
             "KNX is OK"),
            ('temperature', DPTArray((0x77, 0x88,)), 315883.52),
            ('temperature_a', DPTArray((0xF1, 0xDB,)), -257720.32),
            ('temperature_difference', DPTArray((0xC6, 0xC, 0x50, 0xBC,)), -8980.1836),
            ('temperature_difference_2byte', DPTArray((0xA9, 0xF4,)), -495.36),
            ('temperature_f', DPTArray((0x67, 0xA9,)), 80322.56),
            ('thermal_capacity', DPTArray((0x45, 0x83, 0xEA, 0xB3,)), 4221.3374),
            ('thermal_conductivity', DPTArray((0xC5, 0x9C, 0x4D, 0x22,)), -5001.6416),
            ('thermoelectric_power', DPTArray((0x41, 0xCF, 0x9E, 0x4F,)), 25.9523),
            ('time_1', DPTArray((0x5E, 0x1E,)), 32071.68),
            ('time_2', DPTArray((0xFB, 0x29,)), -405995.52),
            ('time_period_100msec', DPTArray((0x6A, 0x35,)), 27189),
            ('time_period_10msec', DPTArray((0x32, 0x3,)), 12803),
            ('time_period_hrs', DPTArray((0x29, 0xDE,)), 10718),
            ('time_period_min', DPTArray((0x0, 0x54,)), 84),
            ('time_period_msec', DPTArray((0x93, 0xC7,)), 37831),
            ('time_period_sec', DPTArray((0xE0, 0xF5,)), 57589),
            ('time_seconds', DPTArray((0x45, 0xEC, 0x91, 0x7C,)), 7570.1855),
            ('torque', DPTArray((0xC5, 0x9, 0x23, 0x5F,)), -2194.2107),
            ('voltage', DPTArray((0x6D, 0xBF,)), 120504.32),
            ('volume', DPTArray((0x46, 0x16, 0x98, 0x43,)), 9638.0654),
            ('volume_flow', DPTArray((0x7C, 0xF5,)), 415825.92),
            ('volume_flux', DPTArray((0xC5, 0x4, 0x2D, 0x72,)), -2114.8403),
            ('weight', DPTArray((0x45, 0x20, 0x10, 0xE8,)), 2561.0566),
            ('work', DPTArray((0x45, 0x64, 0x5D, 0xBE,)), 3653.8589),
            ('wind_speed_ms', DPTArray((0x7D, 0x98,)), 469237.76),
            ('wind_speed_kmh', DPTArray((0x7F, 0x55)), 615055.36),

            # # Generic DPT Without Min/Max and Unit.
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
            ('4byte_float', DPTArray((0xC2, 0x09, 0xEE, 0xCC)), -34.4832)
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
