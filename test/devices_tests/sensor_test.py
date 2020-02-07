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

    def test_str_absolute_temperature(self):
        """Test resolve state with absolute_temperature sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="absolute_temperature")
        sensor.sensor_value.payload = DPTArray((0x44, 0xD7, 0xD2, 0x8B,))

        self.assertEqual(sensor.resolve_state(), 1726.5794677734375)
        self.assertEqual(sensor.unit_of_measurement(), "K")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_acceleration(self):
        """Test resolve state with acceleration sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="acceleration")
        sensor.sensor_value.payload = DPTArray((0x45, 0x94, 0xD8, 0x5D,))

        self.assertEqual(sensor.resolve_state(), 4763.04541015625)
        self.assertEqual(sensor.unit_of_measurement(), "m/s²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_acceleration_angular(self):
        """Test resolve state with acceleration_angular sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="acceleration_angular")
        sensor.sensor_value.payload = DPTArray((0x45, 0xEA, 0x62, 0x34,))

        self.assertEqual(sensor.resolve_state(), 7500.275390625)
        self.assertEqual(sensor.unit_of_measurement(), "rad/s²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_activation_energy(self):
        """Test resolve state with activation_energy sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="activation_energy")
        sensor.sensor_value.payload = DPTArray((0x46, 0x0, 0x3E, 0xEE,))

        self.assertEqual(sensor.resolve_state(), 8207.732421875)
        self.assertEqual(sensor.unit_of_measurement(), "J/mol")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_active_energy(self):
        """Test resolve state with active_energy sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="active_energy")
        sensor.sensor_value.payload = DPTArray((0x26, 0x37, 0x49, 0x7F,))

        self.assertEqual(sensor.resolve_state(), 641157503)
        self.assertEqual(sensor.unit_of_measurement(), "Wh")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_active_energy_kwh(self):
        """Test resolve state with active_energy_kwh sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="active_energy_kwh")
        sensor.sensor_value.payload = DPTArray((0x37, 0x5, 0x5, 0xEA,))

        self.assertEqual(sensor.resolve_state(), 923076074)
        self.assertEqual(sensor.unit_of_measurement(), "kWh")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_activity(self):
        """Test resolve state with activity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="activity")
        sensor.sensor_value.payload = DPTArray((0x45, 0x76, 0x0, 0xA3,))

        self.assertEqual(sensor.resolve_state(), 3936.039794921875)
        self.assertEqual(sensor.unit_of_measurement(), "s⁻¹")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_amplitude(self):
        """Test resolve state with amplitude sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="amplitude")
        sensor.sensor_value.payload = DPTArray((0x45, 0x9A, 0xED, 0x8,))

        self.assertEqual(sensor.resolve_state(), 4957.62890625)
        self.assertEqual(sensor.unit_of_measurement(), "")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_angle(self):
        """Test resolve state with angle sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="angle")
        sensor.sensor_value.payload = DPTArray((0xE4,))

        self.assertEqual(sensor.resolve_state(), 322)
        self.assertEqual(sensor.unit_of_measurement(), "°")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_angle_deg(self):
        """Test resolve state with angle_deg sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="angle_deg")
        sensor.sensor_value.payload = DPTArray((0x44, 0x5C, 0x20, 0x2B,))

        self.assertEqual(sensor.resolve_state(), 880.5026245117188)
        self.assertEqual(sensor.unit_of_measurement(), "°")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_angle_rad(self):
        """Test resolve state with angle_rad sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="angle_rad")
        sensor.sensor_value.payload = DPTArray((0x44, 0x36, 0x75, 0x1,))

        self.assertEqual(sensor.resolve_state(), 729.8281860351562)
        self.assertEqual(sensor.unit_of_measurement(), "rad")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_angular_frequency(self):
        """Test resolve state with angular_frequency sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="angular_frequency")
        sensor.sensor_value.payload = DPTArray((0x43, 0xBC, 0x20, 0x8D,))

        self.assertEqual(sensor.resolve_state(), 376.2543029785156)
        self.assertEqual(sensor.unit_of_measurement(), "rad/s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_angular_momentum(self):
        """Test resolve state with angular_momentum sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="angular_momentum")
        sensor.sensor_value.payload = DPTArray((0xC2, 0x75, 0xB7, 0xB5,))

        self.assertEqual(sensor.resolve_state(), -61.42940139770508)
        self.assertEqual(sensor.unit_of_measurement(), "J s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_angular_velocity(self):
        """Test resolve state with angular_velocity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="angular_velocity")
        sensor.sensor_value.payload = DPTArray((0xC4, 0xD9, 0x10, 0xB3,))

        self.assertEqual(sensor.resolve_state(), -1736.5218505859375)
        self.assertEqual(sensor.unit_of_measurement(), "rad/s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_apparant_energy(self):
        """Test resolve state with apparant_energy sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="apparant_energy")
        sensor.sensor_value.payload = DPTArray((0xD3, 0xBD, 0x1E, 0xA5,))

        self.assertEqual(sensor.resolve_state(), -742580571)
        self.assertEqual(sensor.unit_of_measurement(), "VAh")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_apparant_energy_kvah(self):
        """Test resolve state with apparant_energy_kvah sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="apparant_energy_kvah")
        sensor.sensor_value.payload = DPTArray((0x49, 0x40, 0xC9, 0x9,))

        self.assertEqual(sensor.resolve_state(), 1228982537)
        self.assertEqual(sensor.unit_of_measurement(), "kVAh")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_area(self):
        """Test resolve state with area sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="area")
        sensor.sensor_value.payload = DPTArray((0x45, 0x63, 0x1E, 0xCD,))

        self.assertEqual(sensor.resolve_state(), 3633.925048828125)
        self.assertEqual(sensor.unit_of_measurement(), "m²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_brightness(self):
        """Test resolve state with brightness sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="brightness")
        sensor.sensor_value.payload = DPTArray((0xC3, 0x56,))

        self.assertEqual(sensor.resolve_state(), 50006)
        self.assertEqual(sensor.unit_of_measurement(), "lx")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_capacitance(self):
        """Test resolve state with capacitance sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="capacitance")
        sensor.sensor_value.payload = DPTArray((0x45, 0xC9, 0x1D, 0x9D,))

        self.assertEqual(sensor.resolve_state(), 6435.70166015625)
        self.assertEqual(sensor.unit_of_measurement(), "F")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_charge_density_surface(self):
        """Test resolve state with charge_density_surface sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="charge_density_surface")
        sensor.sensor_value.payload = DPTArray((0x45, 0xDB, 0x66, 0x99,))

        self.assertEqual(sensor.resolve_state(), 7020.82470703125)
        self.assertEqual(sensor.unit_of_measurement(), "C/m²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_charge_density_volume(self):
        """Test resolve state with charge_density_volume sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="charge_density_volume")
        sensor.sensor_value.payload = DPTArray((0xC4, 0x8C, 0x33, 0xD7,))

        self.assertEqual(sensor.resolve_state(), -1121.6199951171875)
        self.assertEqual(sensor.unit_of_measurement(), "C/m³")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_color_temperature(self):
        """Test resolve state with color_temperature sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="color_temperature")
        sensor.sensor_value.payload = DPTArray((0x6C, 0x95,))

        self.assertEqual(sensor.resolve_state(), 27797)
        self.assertEqual(sensor.unit_of_measurement(), "K")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_common_temperature(self):
        """Test resolve state with common_temperature sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="common_temperature")
        sensor.sensor_value.payload = DPTArray((0x45, 0xD9, 0xC6, 0x3F,))

        self.assertEqual(sensor.resolve_state(), 6968.78076171875)
        self.assertEqual(sensor.unit_of_measurement(), "°C")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_compressibility(self):
        """Test resolve state with compressibility sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="compressibility")
        sensor.sensor_value.payload = DPTArray((0x45, 0x89, 0x94, 0xAB,))

        self.assertEqual(sensor.resolve_state(), 4402.58349609375)
        self.assertEqual(sensor.unit_of_measurement(), "m²/N")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_conductance(self):
        """Test resolve state with conductance sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="conductance")
        sensor.sensor_value.payload = DPTArray((0x45, 0xA6, 0x28, 0xF9,))

        self.assertEqual(sensor.resolve_state(), 5317.12158203125)
        self.assertEqual(sensor.unit_of_measurement(), "S")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_counter_pulses(self):
        """Test resolve state with counter_pulses sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="counter_pulses")
        sensor.sensor_value.payload = DPTArray((0x9D,))

        self.assertEqual(sensor.resolve_state(), -99)
        self.assertEqual(sensor.unit_of_measurement(), "counter pulses")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_current(self):
        """Test resolve state with current sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="current")
        sensor.sensor_value.payload = DPTArray((0xCA, 0xCC,))

        self.assertEqual(sensor.resolve_state(), 51916)
        self.assertEqual(sensor.unit_of_measurement(), "mA")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_delta_time_hrs(self):
        """Test resolve state with delta_time_hrs sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="delta_time_hrs")
        sensor.sensor_value.payload = DPTArray((0x47, 0x80,))

        self.assertEqual(sensor.resolve_state(), 18304)
        self.assertEqual(sensor.unit_of_measurement(), "h")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_delta_time_min(self):
        """Test resolve state with delta_time_min sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="delta_time_min")
        sensor.sensor_value.payload = DPTArray((0xB9, 0x7B,))

        self.assertEqual(sensor.resolve_state(), -18053)
        self.assertEqual(sensor.unit_of_measurement(), "min")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_delta_time_ms(self):
        """Test resolve state with delta_time_ms sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="delta_time_ms")
        sensor.sensor_value.payload = DPTArray((0x58, 0x77,))

        self.assertEqual(sensor.resolve_state(), 22647)
        self.assertEqual(sensor.unit_of_measurement(), "ms")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_delta_time_sec(self):
        """Test resolve state with delta_time_sec sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="delta_time_sec")
        sensor.sensor_value.payload = DPTArray((0xA3, 0x6A,))

        self.assertEqual(sensor.resolve_state(), -23702)
        self.assertEqual(sensor.unit_of_measurement(), "s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_density(self):
        """Test resolve state with density sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="density")
        sensor.sensor_value.payload = DPTArray((0x44, 0xA5, 0xCB, 0x27,))

        self.assertEqual(sensor.resolve_state(), 1326.3485107421875)
        self.assertEqual(sensor.unit_of_measurement(), "kg/m³")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electrical_conductivity(self):
        """Test resolve state with electrical_conductivity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electrical_conductivity")
        sensor.sensor_value.payload = DPTArray((0xC4, 0xC6, 0xF5, 0x6E,))

        self.assertEqual(sensor.resolve_state(), -1591.669677734375)
        self.assertEqual(sensor.unit_of_measurement(), "S/m")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electric_charge(self):
        """Test resolve state with electric_charge sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_charge")
        sensor.sensor_value.payload = DPTArray((0x46, 0x14, 0xF6, 0xA0,))

        self.assertEqual(sensor.resolve_state(), 9533.65625)
        self.assertEqual(sensor.unit_of_measurement(), "C")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electric_current(self):
        """Test resolve state with electric_current sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_current")
        sensor.sensor_value.payload = DPTArray((0x45, 0xAD, 0x45, 0x90,))

        self.assertEqual(sensor.resolve_state(), 5544.6953125)
        self.assertEqual(sensor.unit_of_measurement(), "A")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electric_current_density(self):
        """Test resolve state with electric_current_density sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_current_density")
        sensor.sensor_value.payload = DPTArray((0x45, 0x7C, 0x57, 0xF6,))

        self.assertEqual(sensor.resolve_state(), 4037.49755859375)
        self.assertEqual(sensor.unit_of_measurement(), "A/m²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electric_dipole_moment(self):
        """Test resolve state with electric_dipole_moment sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_dipole_moment")
        sensor.sensor_value.payload = DPTArray((0x45, 0x58, 0xF1, 0x73,))

        self.assertEqual(sensor.resolve_state(), 3471.090576171875)
        self.assertEqual(sensor.unit_of_measurement(), "C m")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electric_displacement(self):
        """Test resolve state with electric_displacement sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_displacement")
        sensor.sensor_value.payload = DPTArray((0xC5, 0x34, 0x8B, 0x0,))

        self.assertEqual(sensor.resolve_state(), -2888.6875)
        self.assertEqual(sensor.unit_of_measurement(), "C/m²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electric_field_strength(self):
        """Test resolve state with electric_field_strength sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_field_strength")
        sensor.sensor_value.payload = DPTArray((0xC6, 0x17, 0x1C, 0x39,))

        self.assertEqual(sensor.resolve_state(), -9671.0556640625)
        self.assertEqual(sensor.unit_of_measurement(), "V/m")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electric_flux(self):
        """Test resolve state with electric_flux sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_flux")
        sensor.sensor_value.payload = DPTArray((0x45, 0x8F, 0x6C, 0xFD,))

        self.assertEqual(sensor.resolve_state(), 4589.62353515625)
        self.assertEqual(sensor.unit_of_measurement(), "c")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electric_flux_density(self):
        """Test resolve state with electric_flux_density sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_flux_density")
        sensor.sensor_value.payload = DPTArray((0xC6, 0x0, 0x50, 0xA8,))

        self.assertEqual(sensor.resolve_state(), -8212.1640625)
        self.assertEqual(sensor.unit_of_measurement(), "C/m²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electric_polarization(self):
        """Test resolve state with electric_polarization sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_polarization")
        sensor.sensor_value.payload = DPTArray((0x45, 0xF8, 0x89, 0xC6,))

        self.assertEqual(sensor.resolve_state(), 7953.2216796875)
        self.assertEqual(sensor.unit_of_measurement(), "C/m²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electric_potential(self):
        """Test resolve state with electric_potential sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_potential")
        sensor.sensor_value.payload = DPTArray((0xC6, 0x18, 0xA4, 0xAF,))

        self.assertEqual(sensor.resolve_state(), -9769.1708984375)
        self.assertEqual(sensor.unit_of_measurement(), "V")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electric_potential_difference(self):
        """Test resolve state with electric_potential_difference sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electric_potential_difference")
        sensor.sensor_value.payload = DPTArray((0xC6, 0xF, 0x1D, 0x6,))

        self.assertEqual(sensor.resolve_state(), -9159.255859375)
        self.assertEqual(sensor.unit_of_measurement(), "V")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electromagnetic_moment(self):
        """Test resolve state with electromagnetic_moment sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electromagnetic_moment")
        sensor.sensor_value.payload = DPTArray((0x45, 0x82, 0x48, 0xAE,))

        self.assertEqual(sensor.resolve_state(), 4169.0849609375)
        self.assertEqual(sensor.unit_of_measurement(), "A m²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_electromotive_force(self):
        """Test resolve state with electromotive_force sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="electromotive_force")
        sensor.sensor_value.payload = DPTArray((0x45, 0xBC, 0xEF, 0xEB,))

        self.assertEqual(sensor.resolve_state(), 6045.98974609375)
        self.assertEqual(sensor.unit_of_measurement(), "V")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_energy(self):
        """Test resolve state with energy sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="energy")
        sensor.sensor_value.payload = DPTArray((0x45, 0x4B, 0xB3, 0xF8,))

        self.assertEqual(sensor.resolve_state(), 3259.248046875)
        self.assertEqual(sensor.unit_of_measurement(), "J")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_enthalpy(self):
        """Test resolve state with enthalpy sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="enthalpy")
        sensor.sensor_value.payload = DPTArray((0x76, 0xDD,))

        self.assertEqual(sensor.resolve_state(), 287866.88)
        self.assertEqual(sensor.unit_of_measurement(), "H")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_flow_rate_m3h(self):
        """Test resolve state with flow_rate_m3h sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="flow_rate_m3h")
        sensor.sensor_value.payload = DPTArray((0x99, 0xEA, 0xC0, 0x55,))

        self.assertEqual(sensor.resolve_state(), -1712668587)
        self.assertEqual(sensor.unit_of_measurement(), "m³/h")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_force(self):
        """Test resolve state with force sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="force")
        sensor.sensor_value.payload = DPTArray((0x45, 0x9E, 0x2C, 0xE1,))

        self.assertEqual(sensor.resolve_state(), 5061.60986328125)
        self.assertEqual(sensor.unit_of_measurement(), "N")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_frequency(self):
        """Test resolve state with frequency sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="frequency")
        sensor.sensor_value.payload = DPTArray((0x45, 0xC2, 0x3C, 0x44,))

        self.assertEqual(sensor.resolve_state(), 6215.533203125)
        self.assertEqual(sensor.unit_of_measurement(), "Hz")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_heatcapacity(self):
        """Test resolve state with heatcapacity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="heatcapacity")
        sensor.sensor_value.payload = DPTArray((0xC5, 0xB3, 0x56, 0x7E,))

        self.assertEqual(sensor.resolve_state(), -5738.8115234375)
        self.assertEqual(sensor.unit_of_measurement(), "J/K")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_heatflowrate(self):
        """Test resolve state with heatflowrate sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="heatflowrate")
        sensor.sensor_value.payload = DPTArray((0x44, 0xEC, 0x80, 0x7A,))

        self.assertEqual(sensor.resolve_state(), 1892.014892578125)
        self.assertEqual(sensor.unit_of_measurement(), "W")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_heat_quantity(self):
        """Test resolve state with heat_quantity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="heat_quantity")
        sensor.sensor_value.payload = DPTArray((0xC5, 0xA6, 0xB6, 0xD5,))

        self.assertEqual(sensor.resolve_state(), -5334.85400390625)
        self.assertEqual(sensor.unit_of_measurement(), "J")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_humidity(self):
        """Test resolve state with humidity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="humidity")
        sensor.sensor_value.payload = DPTArray((0x7E, 0xE1,))

        self.assertEqual(sensor.resolve_state(), 577044.48)
        self.assertEqual(sensor.unit_of_measurement(), "%")
        self.assertEqual(sensor.ha_device_class(), 'humidity')

    def test_str_impedance(self):
        """Test resolve state with impedance sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="impedance")
        sensor.sensor_value.payload = DPTArray((0x45, 0xDD, 0x79, 0x6D,))

        self.assertEqual(sensor.resolve_state(), 7087.17822265625)
        self.assertEqual(sensor.unit_of_measurement(), "Ω")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_illuminance(self):
        """Test resolve state with illuminance sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="illuminance")
        sensor.sensor_value.payload = DPTArray((0x7C, 0x5E,))

        self.assertEqual(sensor.resolve_state(), 366346.24)
        self.assertEqual(sensor.unit_of_measurement(), "lx")
        self.assertEqual(sensor.ha_device_class(), 'illuminance')

    def test_str_kelvin_per_percent(self):
        """Test resolve state with kelvin_per_percent sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="kelvin_per_percent")
        sensor.sensor_value.payload = DPTArray((0xFA, 0xBD,))

        self.assertEqual(sensor.resolve_state(), -441384.96)
        self.assertEqual(sensor.unit_of_measurement(), "K/%")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_length(self):
        """Test resolve state with length sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="length")
        sensor.sensor_value.payload = DPTArray((0xC5, 0x9D, 0xAE, 0xC5,))

        self.assertEqual(sensor.resolve_state(), -5045.84619140625)
        self.assertEqual(sensor.unit_of_measurement(), "m")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_length_mm(self):
        """Test resolve state with length_mm sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="length_mm")
        sensor.sensor_value.payload = DPTArray((0x56, 0xB9,))

        self.assertEqual(sensor.resolve_state(), 22201)
        self.assertEqual(sensor.unit_of_measurement(), "mm")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_light_quantity(self):
        """Test resolve state with light_quantity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="light_quantity")
        sensor.sensor_value.payload = DPTArray((0x45, 0x4A, 0xF5, 0x68,))

        self.assertEqual(sensor.resolve_state(), 3247.337890625)
        self.assertEqual(sensor.unit_of_measurement(), "lm s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_long_delta_timesec(self):
        """Test resolve state with long_delta_timesec sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="long_delta_timesec")
        sensor.sensor_value.payload = DPTArray((0x45, 0xB2, 0x17, 0x54,))

        self.assertEqual(sensor.resolve_state(), 1169299284)
        self.assertEqual(sensor.unit_of_measurement(), "s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_luminance(self):
        """Test resolve state with luminance sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="luminance")
        sensor.sensor_value.payload = DPTArray((0x45, 0x18, 0xD9, 0x76,))

        self.assertEqual(sensor.resolve_state(), 2445.59130859375)
        self.assertEqual(sensor.unit_of_measurement(), "cd/m²")
        self.assertEqual(sensor.ha_device_class(), 'illuminance')

    def test_str_luminous_flux(self):
        """Test resolve state with luminous_flux sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="luminous_flux")
        sensor.sensor_value.payload = DPTArray((0x45, 0xBD, 0x16, 0x9,))

        self.assertEqual(sensor.resolve_state(), 6050.75439453125)
        self.assertEqual(sensor.unit_of_measurement(), "lm")
        self.assertEqual(sensor.ha_device_class(), 'illuminance')

    def test_str_luminous_intensity(self):
        """Test resolve state with luminous_intensity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="luminous_intensity")
        sensor.sensor_value.payload = DPTArray((0x46, 0xB, 0xBE, 0x7E,))

        self.assertEqual(sensor.resolve_state(), 8943.623046875)
        self.assertEqual(sensor.unit_of_measurement(), "cd")
        self.assertEqual(sensor.ha_device_class(), 'illuminance')

    def test_str_magnetic_field_strength(self):
        """Test resolve state with magnetic_field_strength sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="magnetic_field_strength")
        sensor.sensor_value.payload = DPTArray((0x44, 0x15, 0xF1, 0xAD,))

        self.assertEqual(sensor.resolve_state(), 599.7761840820312)
        self.assertEqual(sensor.unit_of_measurement(), "A/m")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_magnetic_flux(self):
        """Test resolve state with magnetic_flux sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="magnetic_flux")
        sensor.sensor_value.payload = DPTArray((0xC5, 0xCB, 0x3C, 0x98,))

        self.assertEqual(sensor.resolve_state(), -6503.57421875)
        self.assertEqual(sensor.unit_of_measurement(), "Wb")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_magnetic_flux_density(self):
        """Test resolve state with magnetic_flux_density sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="magnetic_flux_density")
        sensor.sensor_value.payload = DPTArray((0x45, 0xB6, 0xBD, 0x42,))

        self.assertEqual(sensor.resolve_state(), 5847.6572265625)
        self.assertEqual(sensor.unit_of_measurement(), "T")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_magnetic_moment(self):
        """Test resolve state with magnetic_moment sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="magnetic_moment")
        sensor.sensor_value.payload = DPTArray((0xC3, 0x8E, 0x7F, 0x73,))

        self.assertEqual(sensor.resolve_state(), -284.9956970214844)
        self.assertEqual(sensor.unit_of_measurement(), "A m²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_magnetic_polarization(self):
        """Test resolve state with magnetic_polarization sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="magnetic_polarization")
        sensor.sensor_value.payload = DPTArray((0x45, 0x8C, 0xFA, 0xCB,))

        self.assertEqual(sensor.resolve_state(), 4511.34912109375)
        self.assertEqual(sensor.unit_of_measurement(), "T")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_magnetization(self):
        """Test resolve state with magnetization sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="magnetization")
        sensor.sensor_value.payload = DPTArray((0x45, 0xF7, 0x9D, 0xA2,))

        self.assertEqual(sensor.resolve_state(), 7923.7041015625)
        self.assertEqual(sensor.unit_of_measurement(), "A/m")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_magnetomotive_force(self):
        """Test resolve state with magnetomotive_force sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="magnetomotive_force")
        sensor.sensor_value.payload = DPTArray((0xC6, 0x4, 0xC2, 0xDA,))

        self.assertEqual(sensor.resolve_state(), -8496.712890625)
        self.assertEqual(sensor.unit_of_measurement(), "A")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_mass(self):
        """Test resolve state with mass sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="mass")
        sensor.sensor_value.payload = DPTArray((0x45, 0x8F, 0x70, 0xA4,))

        self.assertEqual(sensor.resolve_state(), 4590.080078125)
        self.assertEqual(sensor.unit_of_measurement(), "kg")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_mass_flux(self):
        """Test resolve state with mass_flux sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="mass_flux")
        sensor.sensor_value.payload = DPTArray((0xC6, 0x7, 0x34, 0xFF,))

        self.assertEqual(sensor.resolve_state(), -8653.2490234375)
        self.assertEqual(sensor.unit_of_measurement(), "kg/s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_mol(self):
        """Test resolve state with mol sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="mol")
        sensor.sensor_value.payload = DPTArray((0xC4, 0xA0, 0xF4, 0x68,))

        self.assertEqual(sensor.resolve_state(), -1287.6376953125)
        self.assertEqual(sensor.unit_of_measurement(), "mol")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_momentum(self):
        """Test resolve state with momentum sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="momentum")
        sensor.sensor_value.payload = DPTArray((0xC5, 0x27, 0xAA, 0x5B,))

        self.assertEqual(sensor.resolve_state(), -2682.647216796875)
        self.assertEqual(sensor.unit_of_measurement(), "N/s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_percent(self):
        """Test resolve state with percent sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="percent")
        sensor.sensor_value.payload = DPTArray((0xE3,))

        self.assertEqual(sensor.resolve_state(), 89)
        self.assertEqual(sensor.unit_of_measurement(), "%")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_percentU8(self):
        """Test resolve state with percentU8 sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="percentU8")
        sensor.sensor_value.payload = DPTArray((0x6B,))

        self.assertEqual(sensor.resolve_state(), 107)
        self.assertEqual(sensor.unit_of_measurement(), "%")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_percentV8(self):
        """Test resolve state with percentV8 sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="percentV8")
        sensor.sensor_value.payload = DPTArray((0x20,))

        self.assertEqual(sensor.resolve_state(), 32)
        self.assertEqual(sensor.unit_of_measurement(), "%")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_percentV16(self):
        """Test resolve state with percentV16 sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="percentV16")
        sensor.sensor_value.payload = DPTArray((0x8A, 0x2F,))

        self.assertEqual(sensor.resolve_state(), -30161)
        self.assertEqual(sensor.unit_of_measurement(), "%")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_phaseanglerad(self):
        """Test resolve state with phaseanglerad sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="phaseanglerad")
        sensor.sensor_value.payload = DPTArray((0x45, 0x54, 0xAC, 0x2E,))

        self.assertEqual(sensor.resolve_state(), 3402.76123046875)
        self.assertEqual(sensor.unit_of_measurement(), "rad")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_phaseangledeg(self):
        """Test resolve state with phaseangledeg sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="phaseangledeg")
        sensor.sensor_value.payload = DPTArray((0xC5, 0x25, 0x13, 0x38,))

        self.assertEqual(sensor.resolve_state(), -2641.201171875)
        self.assertEqual(sensor.unit_of_measurement(), "°")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_power(self):
        """Test resolve state with power sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="power")
        sensor.sensor_value.payload = DPTArray((0x45, 0xCB, 0xE2, 0x5C,))

        self.assertEqual(sensor.resolve_state(), 6524.294921875)
        self.assertEqual(sensor.unit_of_measurement(), "W")
        self.assertEqual(sensor.ha_device_class(), 'power')

    def test_str_power_2byte(self):
        """Test resolve state with power_2byte sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="power_2byte")
        sensor.sensor_value.payload = DPTArray((0x6D, 0x91,))

        self.assertEqual(sensor.resolve_state(), 116736.0)
        self.assertEqual(sensor.unit_of_measurement(), "kW")
        self.assertEqual(sensor.ha_device_class(), 'power')

    def test_str_power_density(self):
        """Test resolve state with power_density sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="power_density")
        sensor.sensor_value.payload = DPTArray((0x65, 0x3E,))

        self.assertEqual(sensor.resolve_state(), 54968.32)
        self.assertEqual(sensor.unit_of_measurement(), "W/m²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_powerfactor(self):
        """Test resolve state with powerfactor sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="powerfactor")
        sensor.sensor_value.payload = DPTArray((0xC5, 0x35, 0x28, 0x21,))

        self.assertEqual(sensor.resolve_state(), -2898.508056640625)
        self.assertEqual(sensor.unit_of_measurement(), "cosΦ")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_ppm(self):
        """Test resolve state with ppm sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="ppm")
        sensor.sensor_value.payload = DPTArray((0x7F, 0x74,))

        self.assertEqual(sensor.resolve_state(), 625213.44)
        self.assertEqual(sensor.unit_of_measurement(), "ppm")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_pressure(self):
        """Test resolve state with pressure sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="pressure")
        sensor.sensor_value.payload = DPTArray((0xC5, 0xE6, 0xE6, 0x63,))

        self.assertEqual(sensor.resolve_state(), -7388.79833984375)
        self.assertEqual(sensor.unit_of_measurement(), "Pa")
        self.assertEqual(sensor.ha_device_class(), 'pressure')

    def test_str_pressure_2byte(self):
        """Test resolve state with pressure_2byte sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="pressure_2byte")
        sensor.sensor_value.payload = DPTArray((0x7C, 0xF4,))

        self.assertEqual(sensor.resolve_state(), 415498.24)
        self.assertEqual(sensor.unit_of_measurement(), "Pa")
        self.assertEqual(sensor.ha_device_class(), 'pressure')

    def test_str_pulse(self):
        """Test resolve state with pulse sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="pulse")
        sensor.sensor_value.payload = DPTArray((0xFC,))

        self.assertEqual(sensor.resolve_state(), 252)
        self.assertEqual(sensor.unit_of_measurement(), "")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_rain_amount(self):
        """Test resolve state with rain_amount sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="rain_amount")
        sensor.sensor_value.payload = DPTArray((0xE0, 0xD0,))

        self.assertEqual(sensor.resolve_state(), -75366.4)
        self.assertEqual(sensor.unit_of_measurement(), "l/m²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_reactance(self):
        """Test resolve state with reactance sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="reactance")
        sensor.sensor_value.payload = DPTArray((0x45, 0xB0, 0x50, 0x91,))

        self.assertEqual(sensor.resolve_state(), 5642.07080078125)
        self.assertEqual(sensor.unit_of_measurement(), "Ω")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_reactive_energy(self):
        """Test resolve state with reactive_energy sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="reactive_energy")
        sensor.sensor_value.payload = DPTArray((0x1A, 0x49, 0x6D, 0xA7,))

        self.assertEqual(sensor.resolve_state(), 441019815)
        self.assertEqual(sensor.unit_of_measurement(), "VARh")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_reactive_energy_kvarh(self):
        """Test resolve state with reactive_energy_kvarh sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="reactive_energy_kvarh")
        sensor.sensor_value.payload = DPTArray((0xCC, 0x62, 0x5, 0x31,))

        self.assertEqual(sensor.resolve_state(), -865991375)
        self.assertEqual(sensor.unit_of_measurement(), "kVARh")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_resistance(self):
        """Test resolve state with resistance sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="resistance")
        sensor.sensor_value.payload = DPTArray((0xC5, 0xFC, 0x5F, 0xC2,))

        self.assertEqual(sensor.resolve_state(), -8075.9697265625)
        self.assertEqual(sensor.unit_of_measurement(), "Ω")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_resistivity(self):
        """Test resolve state with resistivity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="resistivity")
        sensor.sensor_value.payload = DPTArray((0xC5, 0x57, 0x76, 0xC3,))

        self.assertEqual(sensor.resolve_state(), -3447.422607421875)
        self.assertEqual(sensor.unit_of_measurement(), "Ω m")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_rotation_angle(self):
        """Test resolve state with rotation_angle sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="rotation_angle")
        sensor.sensor_value.payload = DPTArray((0x2D, 0xDC,))

        self.assertEqual(sensor.resolve_state(), 11740)
        self.assertEqual(sensor.unit_of_measurement(), "°")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_scene_number(self):
        """Test resolve state with scene_number sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="scene_number")
        sensor.sensor_value.payload = DPTArray((0x1,))

        self.assertEqual(sensor.resolve_state(), 2)
        self.assertEqual(sensor.unit_of_measurement(), "")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_self_inductance(self):
        """Test resolve state with self_inductance sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="self_inductance")
        sensor.sensor_value.payload = DPTArray((0xC4, 0xA1, 0xB0, 0x6,))

        self.assertEqual(sensor.resolve_state(), -1293.500732421875)
        self.assertEqual(sensor.unit_of_measurement(), "H")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_solid_angle(self):
        """Test resolve state with solid_angle sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="solid_angle")
        sensor.sensor_value.payload = DPTArray((0xC5, 0xC6, 0xE5, 0x47,))

        self.assertEqual(sensor.resolve_state(), -6364.65966796875)
        self.assertEqual(sensor.unit_of_measurement(), "sr")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_sound_intensity(self):
        """Test resolve state with sound_intensity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="sound_intensity")
        sensor.sensor_value.payload = DPTArray((0xC4, 0xF2, 0x56, 0xE6,))

        self.assertEqual(sensor.resolve_state(), -1938.715576171875)
        self.assertEqual(sensor.unit_of_measurement(), "W/m²")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_speed(self):
        """Test resolve state with speed sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="speed")
        sensor.sensor_value.payload = DPTArray((0xC5, 0xCD, 0x1C, 0x6A,))

        self.assertEqual(sensor.resolve_state(), -6563.5517578125)
        self.assertEqual(sensor.unit_of_measurement(), "m/s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_stress(self):
        """Test resolve state with stress sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="stress")
        sensor.sensor_value.payload = DPTArray((0x45, 0xDC, 0xA8, 0xF2,))

        self.assertEqual(sensor.resolve_state(), 7061.1181640625)
        self.assertEqual(sensor.unit_of_measurement(), "Pa")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_surface_tension(self):
        """Test resolve state with surface_tension sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="surface_tension")
        sensor.sensor_value.payload = DPTArray((0x46, 0xB, 0xAC, 0x11,))

        self.assertEqual(sensor.resolve_state(), 8939.0166015625)
        self.assertEqual(sensor.unit_of_measurement(), "N/m")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_temperature(self):
        """Test resolve state with temperature sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="temperature")
        sensor.sensor_value.payload = DPTArray((0x77, 0x88,))

        self.assertEqual(sensor.resolve_state(), 315883.52)
        self.assertEqual(sensor.unit_of_measurement(), "°C")
        self.assertEqual(sensor.ha_device_class(), 'temperature')

    def test_str_temperature_a(self):
        """Test resolve state with temperature_a sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="temperature_a")
        sensor.sensor_value.payload = DPTArray((0xF1, 0xDB,))

        self.assertEqual(sensor.resolve_state(), -257720.32)
        self.assertEqual(sensor.unit_of_measurement(), "K/h")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_temperature_difference(self):
        """Test resolve state with temperature_difference sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="temperature_difference")
        sensor.sensor_value.payload = DPTArray((0xC6, 0xC, 0x50, 0xBC,))

        self.assertEqual(sensor.resolve_state(), -8980.18359375)
        self.assertEqual(sensor.unit_of_measurement(), "K")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_temperature_difference_2byte(self):
        """Test resolve state with temperature_difference_2byte sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="temperature_difference_2byte")
        sensor.sensor_value.payload = DPTArray((0xA9, 0xF4,))

        self.assertEqual(sensor.resolve_state(), -495.36)
        self.assertEqual(sensor.unit_of_measurement(), "K")
        self.assertEqual(sensor.ha_device_class(), 'temperature')

    def test_str_temperature_f(self):
        """Test resolve state with temperature_f sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="temperature_f")
        sensor.sensor_value.payload = DPTArray((0x67, 0xA9,))

        self.assertEqual(sensor.resolve_state(), 80322.56)
        self.assertEqual(sensor.unit_of_measurement(), "°F")
        self.assertEqual(sensor.ha_device_class(), 'temperature')

    def test_str_thermal_capacity(self):
        """Test resolve state with thermal_capacity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="thermal_capacity")
        sensor.sensor_value.payload = DPTArray((0x45, 0x83, 0xEA, 0xB3,))

        self.assertEqual(sensor.resolve_state(), 4221.33740234375)
        self.assertEqual(sensor.unit_of_measurement(), "J/K")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_thermal_conductivity(self):
        """Test resolve state with thermal_conductivity sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="thermal_conductivity")
        sensor.sensor_value.payload = DPTArray((0xC5, 0x9C, 0x4D, 0x22,))

        self.assertEqual(sensor.resolve_state(), -5001.6416015625)
        self.assertEqual(sensor.unit_of_measurement(), "W/mK")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_thermoelectric_power(self):
        """Test resolve state with thermoelectric_power sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="thermoelectric_power")
        sensor.sensor_value.payload = DPTArray((0x41, 0xCF, 0x9E, 0x4F,))

        self.assertEqual(sensor.resolve_state(), 25.952299118041992)
        self.assertEqual(sensor.unit_of_measurement(), "V/K")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_time_1(self):
        """Test resolve state with time_1 sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="time_1")
        sensor.sensor_value.payload = DPTArray((0x5E, 0x1E,))

        self.assertEqual(sensor.resolve_state(), 32071.68)
        self.assertEqual(sensor.unit_of_measurement(), "s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_time_2(self):
        """Test resolve state with time_2 sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="time_2")
        sensor.sensor_value.payload = DPTArray((0xFB, 0x29,))

        self.assertEqual(sensor.resolve_state(), -405995.52)
        self.assertEqual(sensor.unit_of_measurement(), "ms")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_time_period_100msec(self):
        """Test resolve state with time_period_100msec sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="time_period_100msec")
        sensor.sensor_value.payload = DPTArray((0x6A, 0x35,))

        self.assertEqual(sensor.resolve_state(), 27189)
        self.assertEqual(sensor.unit_of_measurement(), "ms")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_time_period_10msec(self):
        """Test resolve state with time_period_10msec sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="time_period_10msec")
        sensor.sensor_value.payload = DPTArray((0x32, 0x3,))

        self.assertEqual(sensor.resolve_state(), 12803)
        self.assertEqual(sensor.unit_of_measurement(), "ms")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_time_period_hrs(self):
        """Test resolve state with time_period_hrs sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="time_period_hrs")
        sensor.sensor_value.payload = DPTArray((0x29, 0xDE,))

        self.assertEqual(sensor.resolve_state(), 10718)
        self.assertEqual(sensor.unit_of_measurement(), "h")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_time_period_min(self):
        """Test resolve state with time_period_min sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="time_period_min")
        sensor.sensor_value.payload = DPTArray((0x0, 0x54,))

        self.assertEqual(sensor.resolve_state(), 84)
        self.assertEqual(sensor.unit_of_measurement(), "min")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_time_period_msec(self):
        """Test resolve state with time_period_msec sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="time_period_msec")
        sensor.sensor_value.payload = DPTArray((0x93, 0xC7,))

        self.assertEqual(sensor.resolve_state(), 37831)
        self.assertEqual(sensor.unit_of_measurement(), "ms")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_time_period_sec(self):
        """Test resolve state with time_period_sec sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="time_period_sec")
        sensor.sensor_value.payload = DPTArray((0xE0, 0xF5,))

        self.assertEqual(sensor.resolve_state(), 57589)
        self.assertEqual(sensor.unit_of_measurement(), "s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_time_seconds(self):
        """Test resolve state with time_seconds sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="time_seconds")
        sensor.sensor_value.payload = DPTArray((0x45, 0xEC, 0x91, 0x7C,))

        self.assertEqual(sensor.resolve_state(), 7570.185546875)
        self.assertEqual(sensor.unit_of_measurement(), "s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_torque(self):
        """Test resolve state with torque sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="torque")
        sensor.sensor_value.payload = DPTArray((0xC5, 0x9, 0x23, 0x5F,))

        self.assertEqual(sensor.resolve_state(), -2194.210693359375)
        self.assertEqual(sensor.unit_of_measurement(), "N m")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_voltage(self):
        """Test resolve state with voltage sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="voltage")
        sensor.sensor_value.payload = DPTArray((0x6D, 0xBF,))

        self.assertEqual(sensor.resolve_state(), 120504.32)
        self.assertEqual(sensor.unit_of_measurement(), "mV")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_volume(self):
        """Test resolve state with volume sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="volume")
        sensor.sensor_value.payload = DPTArray((0x46, 0x16, 0x98, 0x43,))

        self.assertEqual(sensor.resolve_state(), 9638.0654296875)
        self.assertEqual(sensor.unit_of_measurement(), "m³")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_volume_flow(self):
        """Test resolve state with volume_flow sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="volume_flow")
        sensor.sensor_value.payload = DPTArray((0x7C, 0xF5,))

        self.assertEqual(sensor.resolve_state(), 415825.92)
        self.assertEqual(sensor.unit_of_measurement(), "l/h")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_volume_flux(self):
        """Test resolve state with volume_flux sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="volume_flux")
        sensor.sensor_value.payload = DPTArray((0xC5, 0x4, 0x2D, 0x72,))

        self.assertEqual(sensor.resolve_state(), -2114.84033203125)
        self.assertEqual(sensor.unit_of_measurement(), "m³/s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_weight(self):
        """Test resolve state with weight sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="weight")
        sensor.sensor_value.payload = DPTArray((0x45, 0x20, 0x10, 0xE8,))

        self.assertEqual(sensor.resolve_state(), 2561.056640625)
        self.assertEqual(sensor.unit_of_measurement(), "N")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_work(self):
        """Test resolve state with work sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="work")
        sensor.sensor_value.payload = DPTArray((0x45, 0x64, 0x5D, 0xBE,))

        self.assertEqual(sensor.resolve_state(), 3653.85888671875)
        self.assertEqual(sensor.unit_of_measurement(), "J")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_wind_speed_ms(self):
        """Test resolve state with wind_speed_ms sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="wind_speed_ms")
        sensor.sensor_value.payload = DPTArray((0x7D, 0x98,))

        self.assertEqual(sensor.resolve_state(), 469237.76)
        self.assertEqual(sensor.unit_of_measurement(), "m/s")
        self.assertEqual(sensor.ha_device_class(), None)

    def test_str_wind_speed_kmh(self):
        """Test resolve state with wind_speed_kmh sensor."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address_state='1/2/3',
            value_type="wind_speed_kmh")
        sensor.sensor_value.payload = DPTArray((0x68, 0x0,))

        self.assertEqual(sensor.resolve_state(), 0.0)
        self.assertEqual(sensor.unit_of_measurement(), "km/h")
        self.assertEqual(sensor.ha_device_class(), None)

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
