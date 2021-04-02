"""Unit test for Sensor objects."""
from unittest.mock import AsyncMock

import pytest
from xknx import XKNX
from xknx.devices import Sensor
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


@pytest.mark.asyncio
class TestSensor:
    """Test class for Sensor objects."""

    #
    # STR FUNCTIONS
    #
    def test_str_absolute_temperature(self):
        """Test resolve state with absolute_temperature sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="absolute_temperature",
        )
        sensor.sensor_value.payload = DPTArray((0x44, 0xD7, 0xD2, 0x8B))

        assert sensor.resolve_state() == 1726.5794677734375
        assert sensor.unit_of_measurement() == "K"
        assert sensor.ha_device_class() is None

    async def test_always_callback_sensor(self):
        """Test always callback sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            always_callback=False,
            value_type="volume_liquid_litre",
        )
        after_update_callback = AsyncMock()
        sensor.register_device_updated_cb(after_update_callback)
        payload = DPTArray((0x00, 0x00, 0x01, 0x00))
        #  set initial payload of sensor
        sensor.sensor_value.payload = payload
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueWrite(payload)
        )
        response_telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(payload),
        )
        # verify not called when always_callback is False
        await sensor.process(telegram)
        after_update_callback.assert_not_called()
        after_update_callback.reset_mock()

        sensor.always_callback = True
        # verify called when always_callback is True
        await sensor.process(telegram)
        after_update_callback.assert_called_once()
        after_update_callback.reset_mock()

        # verify not called when processing read responses
        await sensor.process(response_telegram)
        after_update_callback.assert_not_called()

    def test_str_acceleration(self):
        """Test resolve state with acceleration sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="acceleration"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x94, 0xD8, 0x5D))

        assert sensor.resolve_state() == 4763.04541015625
        assert sensor.unit_of_measurement() == "m/s²"
        assert sensor.ha_device_class() is None

    def test_str_volume_liquid_litre(self):
        """Test resolve state with volume liquid sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="volume_liquid_litre",
        )
        sensor.sensor_value.payload = DPTArray((0x00, 0x00, 0x01, 0x00))

        assert sensor.resolve_state() == 256
        assert sensor.unit_of_measurement() == "l"
        assert sensor.ha_device_class() is None

    def test_str_volume_m3(self):
        """Test resolve state with volume m3 sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="volume_m3"
        )
        sensor.sensor_value.payload = DPTArray((0x00, 0x00, 0x01, 0x00))

        assert sensor.resolve_state() == 256
        assert sensor.unit_of_measurement() == "m³"
        assert sensor.ha_device_class() is None

    def test_str_acceleration_angular(self):
        """Test resolve state with acceleration_angular sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="acceleration_angular",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xEA, 0x62, 0x34))

        assert sensor.resolve_state() == 7500.275390625
        assert sensor.unit_of_measurement() == "rad/s²"
        assert sensor.ha_device_class() is None

    def test_str_activation_energy(self):
        """Test resolve state with activation_energy sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="activation_energy",
        )
        sensor.sensor_value.payload = DPTArray((0x46, 0x0, 0x3E, 0xEE))

        assert sensor.resolve_state() == 8207.732421875
        assert sensor.unit_of_measurement() == "J/mol"
        assert sensor.ha_device_class() is None

    def test_str_active_energy(self):
        """Test resolve state with active_energy sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="active_energy"
        )
        sensor.sensor_value.payload = DPTArray((0x26, 0x37, 0x49, 0x7F))

        assert sensor.resolve_state() == 641157503
        assert sensor.unit_of_measurement() == "Wh"
        assert sensor.ha_device_class() == "energy"

    def test_str_active_energy_kwh(self):
        """Test resolve state with active_energy_kwh sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="active_energy_kwh",
        )
        sensor.sensor_value.payload = DPTArray((0x37, 0x5, 0x5, 0xEA))

        assert sensor.resolve_state() == 923076074
        assert sensor.unit_of_measurement() == "kWh"
        assert sensor.ha_device_class() == "energy"

    def test_str_activity(self):
        """Test resolve state with activity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="activity"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x76, 0x0, 0xA3))

        assert sensor.resolve_state() == 3936.039794921875
        assert sensor.unit_of_measurement() == "s⁻¹"
        assert sensor.ha_device_class() is None

    def test_str_amplitude(self):
        """Test resolve state with amplitude sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="amplitude"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x9A, 0xED, 0x8))

        assert sensor.resolve_state() == 4957.62890625
        assert sensor.unit_of_measurement() == ""
        assert sensor.ha_device_class() is None

    def test_str_angle(self):
        """Test resolve state with angle sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="angle"
        )
        sensor.sensor_value.payload = DPTArray((0xE4,))

        assert sensor.resolve_state() == 322
        assert sensor.unit_of_measurement() == "°"
        assert sensor.ha_device_class() is None

    def test_str_angle_deg(self):
        """Test resolve state with angle_deg sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="angle_deg"
        )
        sensor.sensor_value.payload = DPTArray((0x44, 0x5C, 0x20, 0x2B))

        assert sensor.resolve_state() == 880.5026245117188
        assert sensor.unit_of_measurement() == "°"
        assert sensor.ha_device_class() is None

    def test_str_angle_rad(self):
        """Test resolve state with angle_rad sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="angle_rad"
        )
        sensor.sensor_value.payload = DPTArray((0x44, 0x36, 0x75, 0x1))

        assert sensor.resolve_state() == 729.8281860351562
        assert sensor.unit_of_measurement() == "rad"
        assert sensor.ha_device_class() is None

    def test_str_angular_frequency(self):
        """Test resolve state with angular_frequency sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="angular_frequency",
        )
        sensor.sensor_value.payload = DPTArray((0x43, 0xBC, 0x20, 0x8D))

        assert sensor.resolve_state() == 376.2543029785156
        assert sensor.unit_of_measurement() == "rad/s"
        assert sensor.ha_device_class() is None

    def test_str_angular_momentum(self):
        """Test resolve state with angular_momentum sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="angular_momentum",
        )
        sensor.sensor_value.payload = DPTArray((0xC2, 0x75, 0xB7, 0xB5))

        assert sensor.resolve_state() == -61.42940139770508
        assert sensor.unit_of_measurement() == "J s"
        assert sensor.ha_device_class() is None

    def test_str_angular_velocity(self):
        """Test resolve state with angular_velocity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="angular_velocity",
        )
        sensor.sensor_value.payload = DPTArray((0xC4, 0xD9, 0x10, 0xB3))

        assert sensor.resolve_state() == -1736.5218505859375
        assert sensor.unit_of_measurement() == "rad/s"
        assert sensor.ha_device_class() is None

    def test_str_apparant_energy(self):
        """Test resolve state with apparant_energy sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="apparant_energy",
        )
        sensor.sensor_value.payload = DPTArray((0xD3, 0xBD, 0x1E, 0xA5))

        assert sensor.resolve_state() == -742580571
        assert sensor.unit_of_measurement() == "VAh"
        assert sensor.ha_device_class() == "energy"

    def test_str_apparant_energy_kvah(self):
        """Test resolve state with apparant_energy_kvah sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="apparant_energy_kvah",
        )
        sensor.sensor_value.payload = DPTArray((0x49, 0x40, 0xC9, 0x9))

        assert sensor.resolve_state() == 1228982537
        assert sensor.unit_of_measurement() == "kVAh"
        assert sensor.ha_device_class() == "energy"

    def test_str_area(self):
        """Test resolve state with area sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="area"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x63, 0x1E, 0xCD))

        assert sensor.resolve_state() == 3633.925048828125
        assert sensor.unit_of_measurement() == "m²"
        assert sensor.ha_device_class() is None

    def test_str_brightness(self):
        """Test resolve state with brightness sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="brightness"
        )
        sensor.sensor_value.payload = DPTArray((0xC3, 0x56))

        assert sensor.resolve_state() == 50006
        assert sensor.unit_of_measurement() == "lx"
        assert sensor.ha_device_class() is None

    def test_str_capacitance(self):
        """Test resolve state with capacitance sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="capacitance"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xC9, 0x1D, 0x9D))

        assert sensor.resolve_state() == 6435.70166015625
        assert sensor.unit_of_measurement() == "F"
        assert sensor.ha_device_class() is None

    def test_str_charge_density_surface(self):
        """Test resolve state with charge_density_surface sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="charge_density_surface",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xDB, 0x66, 0x99))

        assert sensor.resolve_state() == 7020.82470703125
        assert sensor.unit_of_measurement() == "C/m²"
        assert sensor.ha_device_class() is None

    def test_str_charge_density_volume(self):
        """Test resolve state with charge_density_volume sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="charge_density_volume",
        )
        sensor.sensor_value.payload = DPTArray((0xC4, 0x8C, 0x33, 0xD7))

        assert sensor.resolve_state() == -1121.6199951171875
        assert sensor.unit_of_measurement() == "C/m³"
        assert sensor.ha_device_class() is None

    def test_str_color_temperature(self):
        """Test resolve state with color_temperature sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="color_temperature",
        )
        sensor.sensor_value.payload = DPTArray((0x6C, 0x95))

        assert sensor.resolve_state() == 27797
        assert sensor.unit_of_measurement() == "K"
        assert sensor.ha_device_class() is None

    def test_str_common_temperature(self):
        """Test resolve state with common_temperature sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="common_temperature",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xD9, 0xC6, 0x3F))

        assert sensor.resolve_state() == 6968.78076171875
        assert sensor.unit_of_measurement() == "°C"
        assert sensor.ha_device_class() is None

    def test_str_compressibility(self):
        """Test resolve state with compressibility sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="compressibility",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x89, 0x94, 0xAB))

        assert sensor.resolve_state() == 4402.58349609375
        assert sensor.unit_of_measurement() == "m²/N"
        assert sensor.ha_device_class() is None

    def test_str_conductance(self):
        """Test resolve state with conductance sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="conductance"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xA6, 0x28, 0xF9))

        assert sensor.resolve_state() == 5317.12158203125
        assert sensor.unit_of_measurement() == "S"
        assert sensor.ha_device_class() is None

    def test_str_counter_pulses(self):
        """Test resolve state with counter_pulses sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="counter_pulses"
        )
        sensor.sensor_value.payload = DPTArray((0x9D,))

        assert sensor.resolve_state() == -99
        assert sensor.unit_of_measurement() == "counter pulses"
        assert sensor.ha_device_class() is None

    def test_str_current(self):
        """Test resolve state with current sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="current"
        )
        sensor.sensor_value.payload = DPTArray((0xCA, 0xCC))

        assert sensor.resolve_state() == 51916
        assert sensor.unit_of_measurement() == "mA"
        assert sensor.ha_device_class() is None

    def test_str_delta_time_hrs(self):
        """Test resolve state with delta_time_hrs sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="delta_time_hrs"
        )
        sensor.sensor_value.payload = DPTArray((0x47, 0x80))

        assert sensor.resolve_state() == 18304
        assert sensor.unit_of_measurement() == "h"
        assert sensor.ha_device_class() is None

    def test_str_delta_time_min(self):
        """Test resolve state with delta_time_min sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="delta_time_min"
        )
        sensor.sensor_value.payload = DPTArray((0xB9, 0x7B))

        assert sensor.resolve_state() == -18053
        assert sensor.unit_of_measurement() == "min"
        assert sensor.ha_device_class() is None

    def test_str_delta_time_ms(self):
        """Test resolve state with delta_time_ms sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="delta_time_ms"
        )
        sensor.sensor_value.payload = DPTArray((0x58, 0x77))

        assert sensor.resolve_state() == 22647
        assert sensor.unit_of_measurement() == "ms"
        assert sensor.ha_device_class() is None

    def test_str_delta_time_sec(self):
        """Test resolve state with delta_time_sec sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="delta_time_sec"
        )
        sensor.sensor_value.payload = DPTArray((0xA3, 0x6A))

        assert sensor.resolve_state() == -23702
        assert sensor.unit_of_measurement() == "s"
        assert sensor.ha_device_class() is None

    def test_str_density(self):
        """Test resolve state with density sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="density"
        )
        sensor.sensor_value.payload = DPTArray((0x44, 0xA5, 0xCB, 0x27))

        assert sensor.resolve_state() == 1326.3485107421875
        assert sensor.unit_of_measurement() == "kg/m³"
        assert sensor.ha_device_class() is None

    def test_str_electrical_conductivity(self):
        """Test resolve state with electrical_conductivity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electrical_conductivity",
        )
        sensor.sensor_value.payload = DPTArray((0xC4, 0xC6, 0xF5, 0x6E))

        assert sensor.resolve_state() == -1591.669677734375
        assert sensor.unit_of_measurement() == "S/m"
        assert sensor.ha_device_class() is None

    def test_str_electric_charge(self):
        """Test resolve state with electric_charge sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electric_charge",
        )
        sensor.sensor_value.payload = DPTArray((0x46, 0x14, 0xF6, 0xA0))

        assert sensor.resolve_state() == 9533.65625
        assert sensor.unit_of_measurement() == "C"
        assert sensor.ha_device_class() is None

    def test_str_electric_current(self):
        """Test resolve state with electric_current sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electric_current",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xAD, 0x45, 0x90))

        assert sensor.resolve_state() == 5544.6953125
        assert sensor.unit_of_measurement() == "A"
        assert sensor.ha_device_class() is None

    def test_str_electric_current_density(self):
        """Test resolve state with electric_current_density sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electric_current_density",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x7C, 0x57, 0xF6))

        assert sensor.resolve_state() == 4037.49755859375
        assert sensor.unit_of_measurement() == "A/m²"
        assert sensor.ha_device_class() is None

    def test_str_electric_dipole_moment(self):
        """Test resolve state with electric_dipole_moment sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electric_dipole_moment",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x58, 0xF1, 0x73))

        assert sensor.resolve_state() == 3471.090576171875
        assert sensor.unit_of_measurement() == "C m"
        assert sensor.ha_device_class() is None

    def test_str_electric_displacement(self):
        """Test resolve state with electric_displacement sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electric_displacement",
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0x34, 0x8B, 0x0))

        assert sensor.resolve_state() == -2888.6875
        assert sensor.unit_of_measurement() == "C/m²"
        assert sensor.ha_device_class() is None

    def test_str_electric_field_strength(self):
        """Test resolve state with electric_field_strength sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electric_field_strength",
        )
        sensor.sensor_value.payload = DPTArray((0xC6, 0x17, 0x1C, 0x39))

        assert sensor.resolve_state() == -9671.0556640625
        assert sensor.unit_of_measurement() == "V/m"
        assert sensor.ha_device_class() is None

    def test_str_electric_flux(self):
        """Test resolve state with electric_flux sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="electric_flux"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x8F, 0x6C, 0xFD))

        assert sensor.resolve_state() == 4589.62353515625
        assert sensor.unit_of_measurement() == "c"
        assert sensor.ha_device_class() is None

    def test_str_electric_flux_density(self):
        """Test resolve state with electric_flux_density sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electric_flux_density",
        )
        sensor.sensor_value.payload = DPTArray((0xC6, 0x0, 0x50, 0xA8))

        assert sensor.resolve_state() == -8212.1640625
        assert sensor.unit_of_measurement() == "C/m²"
        assert sensor.ha_device_class() is None

    def test_str_electric_polarization(self):
        """Test resolve state with electric_polarization sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electric_polarization",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xF8, 0x89, 0xC6))

        assert sensor.resolve_state() == 7953.2216796875
        assert sensor.unit_of_measurement() == "C/m²"
        assert sensor.ha_device_class() is None

    def test_str_electric_potential(self):
        """Test resolve state with electric_potential sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electric_potential",
        )
        sensor.sensor_value.payload = DPTArray((0xC6, 0x18, 0xA4, 0xAF))

        assert sensor.resolve_state() == -9769.1708984375
        assert sensor.unit_of_measurement() == "V"
        assert sensor.ha_device_class() is None

    def test_str_electric_potential_difference(self):
        """Test resolve state with electric_potential_difference sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electric_potential_difference",
        )
        sensor.sensor_value.payload = DPTArray((0xC6, 0xF, 0x1D, 0x6))

        assert sensor.resolve_state() == -9159.255859375
        assert sensor.unit_of_measurement() == "V"
        assert sensor.ha_device_class() is None

    def test_str_electromagnetic_moment(self):
        """Test resolve state with electromagnetic_moment sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electromagnetic_moment",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x82, 0x48, 0xAE))

        assert sensor.resolve_state() == 4169.0849609375
        assert sensor.unit_of_measurement() == "A m²"
        assert sensor.ha_device_class() is None

    def test_str_electromotive_force(self):
        """Test resolve state with electromotive_force sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="electromotive_force",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xBC, 0xEF, 0xEB))

        assert sensor.resolve_state() == 6045.98974609375
        assert sensor.unit_of_measurement() == "V"
        assert sensor.ha_device_class() is None

    def test_str_energy(self):
        """Test resolve state with energy sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="energy"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x4B, 0xB3, 0xF8))

        assert sensor.resolve_state() == 3259.248046875
        assert sensor.unit_of_measurement() == "J"
        assert sensor.ha_device_class() is None

    def test_str_enthalpy(self):
        """Test resolve state with enthalpy sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="enthalpy"
        )
        sensor.sensor_value.payload = DPTArray((0x76, 0xDD))

        assert sensor.resolve_state() == 287866.88
        assert sensor.unit_of_measurement() == "H"
        assert sensor.ha_device_class() is None

    def test_str_flow_rate_m3h(self):
        """Test resolve state with flow_rate_m3h sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="flow_rate_m3h"
        )
        sensor.sensor_value.payload = DPTArray((0x99, 0xEA, 0xC0, 0x55))

        assert sensor.resolve_state() == -1712668587
        assert sensor.unit_of_measurement() == "m³/h"
        assert sensor.ha_device_class() is None

    def test_str_force(self):
        """Test resolve state with force sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="force"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x9E, 0x2C, 0xE1))

        assert sensor.resolve_state() == 5061.60986328125
        assert sensor.unit_of_measurement() == "N"
        assert sensor.ha_device_class() is None

    def test_str_frequency(self):
        """Test resolve state with frequency sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="frequency"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xC2, 0x3C, 0x44))

        assert sensor.resolve_state() == 6215.533203125
        assert sensor.unit_of_measurement() == "Hz"
        assert sensor.ha_device_class() is None

    def test_str_heatcapacity(self):
        """Test resolve state with heatcapacity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="heatcapacity"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0xB3, 0x56, 0x7E))

        assert sensor.resolve_state() == -5738.8115234375
        assert sensor.unit_of_measurement() == "J/K"
        assert sensor.ha_device_class() is None

    def test_str_heatflowrate(self):
        """Test resolve state with heatflowrate sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="heatflowrate"
        )
        sensor.sensor_value.payload = DPTArray((0x44, 0xEC, 0x80, 0x7A))

        assert sensor.resolve_state() == 1892.014892578125
        assert sensor.unit_of_measurement() == "W"
        assert sensor.ha_device_class() is None

    def test_str_heat_quantity(self):
        """Test resolve state with heat_quantity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="heat_quantity"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0xA6, 0xB6, 0xD5))

        assert sensor.resolve_state() == -5334.85400390625
        assert sensor.unit_of_measurement() == "J"
        assert sensor.ha_device_class() is None

    def test_str_humidity(self):
        """Test resolve state with humidity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="humidity"
        )
        sensor.sensor_value.payload = DPTArray((0x7E, 0xE1))

        assert sensor.resolve_state() == 577044.48
        assert sensor.unit_of_measurement() == "%"
        assert sensor.ha_device_class() == "humidity"

    def test_str_impedance(self):
        """Test resolve state with impedance sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="impedance"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xDD, 0x79, 0x6D))

        assert sensor.resolve_state() == 7087.17822265625
        assert sensor.unit_of_measurement() == "Ω"
        assert sensor.ha_device_class() is None

    def test_str_illuminance(self):
        """Test resolve state with illuminance sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="illuminance"
        )
        sensor.sensor_value.payload = DPTArray((0x7C, 0x5E))

        assert sensor.resolve_state() == 366346.24
        assert sensor.unit_of_measurement() == "lx"
        assert sensor.ha_device_class() == "illuminance"

    def test_str_kelvin_per_percent(self):
        """Test resolve state with kelvin_per_percent sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="kelvin_per_percent",
        )
        sensor.sensor_value.payload = DPTArray((0xFA, 0xBD))

        assert sensor.resolve_state() == -441384.96
        assert sensor.unit_of_measurement() == "K/%"
        assert sensor.ha_device_class() is None

    def test_str_length(self):
        """Test resolve state with length sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="length"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0x9D, 0xAE, 0xC5))

        assert sensor.resolve_state() == -5045.84619140625
        assert sensor.unit_of_measurement() == "m"
        assert sensor.ha_device_class() is None

    def test_str_length_mm(self):
        """Test resolve state with length_mm sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="length_mm"
        )
        sensor.sensor_value.payload = DPTArray((0x56, 0xB9))

        assert sensor.resolve_state() == 22201
        assert sensor.unit_of_measurement() == "mm"
        assert sensor.ha_device_class() is None

    def test_str_light_quantity(self):
        """Test resolve state with light_quantity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="light_quantity"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x4A, 0xF5, 0x68))

        assert sensor.resolve_state() == 3247.337890625
        assert sensor.unit_of_measurement() == "lm s"
        assert sensor.ha_device_class() is None

    def test_str_long_delta_timesec(self):
        """Test resolve state with long_delta_timesec sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="long_delta_timesec",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xB2, 0x17, 0x54))

        assert sensor.resolve_state() == 1169299284
        assert sensor.unit_of_measurement() == "s"
        assert sensor.ha_device_class() is None

    def test_str_luminance(self):
        """Test resolve state with luminance sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="luminance"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x18, 0xD9, 0x76))

        assert sensor.resolve_state() == 2445.59130859375
        assert sensor.unit_of_measurement() == "cd/m²"
        assert sensor.ha_device_class() == "illuminance"

    def test_str_luminous_flux(self):
        """Test resolve state with luminous_flux sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="luminous_flux"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xBD, 0x16, 0x9))

        assert sensor.resolve_state() == 6050.75439453125
        assert sensor.unit_of_measurement() == "lm"
        assert sensor.ha_device_class() == "illuminance"

    def test_str_luminous_intensity(self):
        """Test resolve state with luminous_intensity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="luminous_intensity",
        )
        sensor.sensor_value.payload = DPTArray((0x46, 0xB, 0xBE, 0x7E))

        assert sensor.resolve_state() == 8943.623046875
        assert sensor.unit_of_measurement() == "cd"
        assert sensor.ha_device_class() == "illuminance"

    def test_str_magnetic_field_strength(self):
        """Test resolve state with magnetic_field_strength sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="magnetic_field_strength",
        )
        sensor.sensor_value.payload = DPTArray((0x44, 0x15, 0xF1, 0xAD))

        assert sensor.resolve_state() == 599.7761840820312
        assert sensor.unit_of_measurement() == "A/m"
        assert sensor.ha_device_class() is None

    def test_str_magnetic_flux(self):
        """Test resolve state with magnetic_flux sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="magnetic_flux"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0xCB, 0x3C, 0x98))

        assert sensor.resolve_state() == -6503.57421875
        assert sensor.unit_of_measurement() == "Wb"
        assert sensor.ha_device_class() is None

    def test_str_magnetic_flux_density(self):
        """Test resolve state with magnetic_flux_density sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="magnetic_flux_density",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xB6, 0xBD, 0x42))

        assert sensor.resolve_state() == 5847.6572265625
        assert sensor.unit_of_measurement() == "T"
        assert sensor.ha_device_class() is None

    def test_str_magnetic_moment(self):
        """Test resolve state with magnetic_moment sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="magnetic_moment",
        )
        sensor.sensor_value.payload = DPTArray((0xC3, 0x8E, 0x7F, 0x73))

        assert sensor.resolve_state() == -284.9956970214844
        assert sensor.unit_of_measurement() == "A m²"
        assert sensor.ha_device_class() is None

    def test_str_magnetic_polarization(self):
        """Test resolve state with magnetic_polarization sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="magnetic_polarization",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x8C, 0xFA, 0xCB))

        assert sensor.resolve_state() == 4511.34912109375
        assert sensor.unit_of_measurement() == "T"
        assert sensor.ha_device_class() is None

    def test_str_magnetization(self):
        """Test resolve state with magnetization sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="magnetization"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xF7, 0x9D, 0xA2))

        assert sensor.resolve_state() == 7923.7041015625
        assert sensor.unit_of_measurement() == "A/m"
        assert sensor.ha_device_class() is None

    def test_str_magnetomotive_force(self):
        """Test resolve state with magnetomotive_force sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="magnetomotive_force",
        )
        sensor.sensor_value.payload = DPTArray((0xC6, 0x4, 0xC2, 0xDA))

        assert sensor.resolve_state() == -8496.712890625
        assert sensor.unit_of_measurement() == "A"
        assert sensor.ha_device_class() is None

    def test_str_mass(self):
        """Test resolve state with mass sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="mass"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x8F, 0x70, 0xA4))

        assert sensor.resolve_state() == 4590.080078125
        assert sensor.unit_of_measurement() == "kg"
        assert sensor.ha_device_class() is None

    def test_str_mass_flux(self):
        """Test resolve state with mass_flux sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="mass_flux"
        )
        sensor.sensor_value.payload = DPTArray((0xC6, 0x7, 0x34, 0xFF))

        assert sensor.resolve_state() == -8653.2490234375
        assert sensor.unit_of_measurement() == "kg/s"
        assert sensor.ha_device_class() is None

    def test_str_mol(self):
        """Test resolve state with mol sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="mol"
        )
        sensor.sensor_value.payload = DPTArray((0xC4, 0xA0, 0xF4, 0x68))

        assert sensor.resolve_state() == -1287.6376953125
        assert sensor.unit_of_measurement() == "mol"
        assert sensor.ha_device_class() is None

    def test_str_momentum(self):
        """Test resolve state with momentum sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="momentum"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0x27, 0xAA, 0x5B))

        assert sensor.resolve_state() == -2682.647216796875
        assert sensor.unit_of_measurement() == "N/s"
        assert sensor.ha_device_class() is None

    def test_str_percent(self):
        """Test resolve state with percent sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="percent"
        )
        sensor.sensor_value.payload = DPTArray((0xE3,))

        assert sensor.resolve_state() == 89
        assert sensor.unit_of_measurement() == "%"
        assert sensor.ha_device_class() is None

    def test_str_percent_u8(self):
        """Test resolve state with percentU8 sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="percentU8"
        )
        sensor.sensor_value.payload = DPTArray((0x6B,))

        assert sensor.resolve_state() == 107
        assert sensor.unit_of_measurement() == "%"
        assert sensor.ha_device_class() is None

    def test_str_percent_v8(self):
        """Test resolve state with percentV8 sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="percentV8"
        )
        sensor.sensor_value.payload = DPTArray((0x20,))

        assert sensor.resolve_state() == 32
        assert sensor.unit_of_measurement() == "%"
        assert sensor.ha_device_class() is None

    def test_str_percent_v16(self):
        """Test resolve state with percentV16 sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="percentV16"
        )
        sensor.sensor_value.payload = DPTArray((0x8A, 0x2F))

        assert sensor.resolve_state() == -30161
        assert sensor.unit_of_measurement() == "%"
        assert sensor.ha_device_class() is None

    def test_str_phaseanglerad(self):
        """Test resolve state with phaseanglerad sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="phaseanglerad"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x54, 0xAC, 0x2E))

        assert sensor.resolve_state() == 3402.76123046875
        assert sensor.unit_of_measurement() == "rad"
        assert sensor.ha_device_class() is None

    def test_str_phaseangledeg(self):
        """Test resolve state with phaseangledeg sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="phaseangledeg"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0x25, 0x13, 0x38))

        assert sensor.resolve_state() == -2641.201171875
        assert sensor.unit_of_measurement() == "°"
        assert sensor.ha_device_class() is None

    def test_str_power(self):
        """Test resolve state with power sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="power"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xCB, 0xE2, 0x5C))

        assert sensor.resolve_state() == 6524.294921875
        assert sensor.unit_of_measurement() == "W"
        assert sensor.ha_device_class() == "power"

    def test_str_power_2byte(self):
        """Test resolve state with power_2byte sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="power_2byte"
        )
        sensor.sensor_value.payload = DPTArray((0x6D, 0x91))

        assert sensor.resolve_state() == 116736.0
        assert sensor.unit_of_measurement() == "kW"
        assert sensor.ha_device_class() == "power"

    def test_str_power_density(self):
        """Test resolve state with power_density sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="power_density"
        )
        sensor.sensor_value.payload = DPTArray((0x65, 0x3E))

        assert sensor.resolve_state() == 54968.32
        assert sensor.unit_of_measurement() == "W/m²"
        assert sensor.ha_device_class() is None

    def test_str_powerfactor(self):
        """Test resolve state with powerfactor sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="powerfactor"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0x35, 0x28, 0x21))

        assert sensor.resolve_state() == -2898.508056640625
        assert sensor.unit_of_measurement() == "cosΦ"
        assert sensor.ha_device_class() == "power_factor"

    def test_str_ppm(self):
        """Test resolve state with ppm sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="ppm"
        )
        sensor.sensor_value.payload = DPTArray((0x7F, 0x74))

        assert sensor.resolve_state() == 625213.44
        assert sensor.unit_of_measurement() == "ppm"
        assert sensor.ha_device_class() is None

    def test_str_pressure(self):
        """Test resolve state with pressure sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="pressure"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0xE6, 0xE6, 0x63))

        assert sensor.resolve_state() == -7388.79833984375
        assert sensor.unit_of_measurement() == "Pa"
        assert sensor.ha_device_class() == "pressure"

    def test_str_pressure_2byte(self):
        """Test resolve state with pressure_2byte sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="pressure_2byte"
        )
        sensor.sensor_value.payload = DPTArray((0x7C, 0xF4))

        assert sensor.resolve_state() == 415498.24
        assert sensor.unit_of_measurement() == "Pa"
        assert sensor.ha_device_class() == "pressure"

    def test_str_pulse(self):
        """Test resolve state with pulse sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="pulse"
        )
        sensor.sensor_value.payload = DPTArray((0xFC,))

        assert sensor.resolve_state() == 252
        assert sensor.unit_of_measurement() == "counter pulses"
        assert sensor.ha_device_class() is None

    def test_str_rain_amount(self):
        """Test resolve state with rain_amount sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="rain_amount"
        )
        sensor.sensor_value.payload = DPTArray((0xE0, 0xD0))

        assert sensor.resolve_state() == -75366.4
        assert sensor.unit_of_measurement() == "l/m²"
        assert sensor.ha_device_class() is None

    def test_str_reactance(self):
        """Test resolve state with reactance sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="reactance"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xB0, 0x50, 0x91))

        assert sensor.resolve_state() == 5642.07080078125
        assert sensor.unit_of_measurement() == "Ω"
        assert sensor.ha_device_class() is None

    def test_str_reactive_energy(self):
        """Test resolve state with reactive_energy sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="reactive_energy",
        )
        sensor.sensor_value.payload = DPTArray((0x1A, 0x49, 0x6D, 0xA7))

        assert sensor.resolve_state() == 441019815
        assert sensor.unit_of_measurement() == "VARh"
        assert sensor.ha_device_class() == "energy"

    def test_str_reactive_energy_kvarh(self):
        """Test resolve state with reactive_energy_kvarh sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="reactive_energy_kvarh",
        )
        sensor.sensor_value.payload = DPTArray((0xCC, 0x62, 0x5, 0x31))

        assert sensor.resolve_state() == -865991375
        assert sensor.unit_of_measurement() == "kVARh"
        assert sensor.ha_device_class() == "energy"

    def test_str_resistance(self):
        """Test resolve state with resistance sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="resistance"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0xFC, 0x5F, 0xC2))

        assert sensor.resolve_state() == -8075.9697265625
        assert sensor.unit_of_measurement() == "Ω"
        assert sensor.ha_device_class() is None

    def test_str_resistivity(self):
        """Test resolve state with resistivity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="resistivity"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0x57, 0x76, 0xC3))

        assert sensor.resolve_state() == -3447.422607421875
        assert sensor.unit_of_measurement() == "Ω m"
        assert sensor.ha_device_class() is None

    def test_str_rotation_angle(self):
        """Test resolve state with rotation_angle sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="rotation_angle"
        )
        sensor.sensor_value.payload = DPTArray((0x2D, 0xDC))

        assert sensor.resolve_state() == 11740
        assert sensor.unit_of_measurement() == "°"
        assert sensor.ha_device_class() is None

    def test_str_scene_number(self):
        """Test resolve state with scene_number sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="scene_number"
        )
        sensor.sensor_value.payload = DPTArray((0x1,))

        assert sensor.resolve_state() == 2
        assert sensor.unit_of_measurement() == ""
        assert sensor.ha_device_class() is None

    def test_str_self_inductance(self):
        """Test resolve state with self_inductance sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="self_inductance",
        )
        sensor.sensor_value.payload = DPTArray((0xC4, 0xA1, 0xB0, 0x6))

        assert sensor.resolve_state() == -1293.500732421875
        assert sensor.unit_of_measurement() == "H"
        assert sensor.ha_device_class() is None

    def test_str_solid_angle(self):
        """Test resolve state with solid_angle sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="solid_angle"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0xC6, 0xE5, 0x47))

        assert sensor.resolve_state() == -6364.65966796875
        assert sensor.unit_of_measurement() == "sr"
        assert sensor.ha_device_class() is None

    def test_str_sound_intensity(self):
        """Test resolve state with sound_intensity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="sound_intensity",
        )
        sensor.sensor_value.payload = DPTArray((0xC4, 0xF2, 0x56, 0xE6))

        assert sensor.resolve_state() == -1938.715576171875
        assert sensor.unit_of_measurement() == "W/m²"
        assert sensor.ha_device_class() is None

    def test_str_speed(self):
        """Test resolve state with speed sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="speed"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0xCD, 0x1C, 0x6A))

        assert sensor.resolve_state() == -6563.5517578125
        assert sensor.unit_of_measurement() == "m/s"
        assert sensor.ha_device_class() is None

    def test_str_stress(self):
        """Test resolve state with stress sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="stress"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xDC, 0xA8, 0xF2))

        assert sensor.resolve_state() == 7061.1181640625
        assert sensor.unit_of_measurement() == "Pa"
        assert sensor.ha_device_class() is None

    def test_str_surface_tension(self):
        """Test resolve state with surface_tension sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="surface_tension",
        )
        sensor.sensor_value.payload = DPTArray((0x46, 0xB, 0xAC, 0x11))

        assert sensor.resolve_state() == 8939.0166015625
        assert sensor.unit_of_measurement() == "N/m"
        assert sensor.ha_device_class() is None

    def test_str_temperature(self):
        """Test resolve state with temperature sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="temperature"
        )
        sensor.sensor_value.payload = DPTArray((0x77, 0x88))

        assert sensor.resolve_state() == 315883.52
        assert sensor.unit_of_measurement() == "°C"
        assert sensor.ha_device_class() == "temperature"

    def test_str_temperature_a(self):
        """Test resolve state with temperature_a sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="temperature_a"
        )
        sensor.sensor_value.payload = DPTArray((0xF1, 0xDB))

        assert sensor.resolve_state() == -257720.32
        assert sensor.unit_of_measurement() == "K/h"
        assert sensor.ha_device_class() is None

    def test_str_temperature_difference(self):
        """Test resolve state with temperature_difference sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="temperature_difference",
        )
        sensor.sensor_value.payload = DPTArray((0xC6, 0xC, 0x50, 0xBC))

        assert sensor.resolve_state() == -8980.18359375
        assert sensor.unit_of_measurement() == "K"
        assert sensor.ha_device_class() is None

    def test_str_temperature_difference_2byte(self):
        """Test resolve state with temperature_difference_2byte sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="temperature_difference_2byte",
        )
        sensor.sensor_value.payload = DPTArray((0xA9, 0xF4))

        assert sensor.resolve_state() == -495.36
        assert sensor.unit_of_measurement() == "K"
        assert sensor.ha_device_class() == "temperature"

    def test_str_temperature_f(self):
        """Test resolve state with temperature_f sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="temperature_f"
        )
        sensor.sensor_value.payload = DPTArray((0x67, 0xA9))

        assert sensor.resolve_state() == 80322.56
        assert sensor.unit_of_measurement() == "°F"
        assert sensor.ha_device_class() == "temperature"

    def test_str_thermal_capacity(self):
        """Test resolve state with thermal_capacity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="thermal_capacity",
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x83, 0xEA, 0xB3))

        assert sensor.resolve_state() == 4221.33740234375
        assert sensor.unit_of_measurement() == "J/K"
        assert sensor.ha_device_class() is None

    def test_str_thermal_conductivity(self):
        """Test resolve state with thermal_conductivity sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="thermal_conductivity",
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0x9C, 0x4D, 0x22))

        assert sensor.resolve_state() == -5001.6416015625
        assert sensor.unit_of_measurement() == "W/mK"
        assert sensor.ha_device_class() is None

    def test_str_thermoelectric_power(self):
        """Test resolve state with thermoelectric_power sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="thermoelectric_power",
        )
        sensor.sensor_value.payload = DPTArray((0x41, 0xCF, 0x9E, 0x4F))

        assert sensor.resolve_state() == 25.952299118041992
        assert sensor.unit_of_measurement() == "V/K"
        assert sensor.ha_device_class() is None

    def test_str_time_1(self):
        """Test resolve state with time_1 sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="time_1"
        )
        sensor.sensor_value.payload = DPTArray((0x5E, 0x1E))

        assert sensor.resolve_state() == 32071.68
        assert sensor.unit_of_measurement() == "s"
        assert sensor.ha_device_class() is None

    def test_str_time_2(self):
        """Test resolve state with time_2 sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="time_2"
        )
        sensor.sensor_value.payload = DPTArray((0xFB, 0x29))

        assert sensor.resolve_state() == -405995.52
        assert sensor.unit_of_measurement() == "ms"
        assert sensor.ha_device_class() is None

    def test_str_time_period_100msec(self):
        """Test resolve state with time_period_100msec sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="time_period_100msec",
        )
        sensor.sensor_value.payload = DPTArray((0x6A, 0x35))

        assert sensor.resolve_state() == 27189
        assert sensor.unit_of_measurement() == "ms"
        assert sensor.ha_device_class() is None

    def test_str_time_period_10msec(self):
        """Test resolve state with time_period_10msec sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="time_period_10msec",
        )
        sensor.sensor_value.payload = DPTArray((0x32, 0x3))

        assert sensor.resolve_state() == 12803
        assert sensor.unit_of_measurement() == "ms"
        assert sensor.ha_device_class() is None

    def test_str_time_period_hrs(self):
        """Test resolve state with time_period_hrs sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="time_period_hrs",
        )
        sensor.sensor_value.payload = DPTArray((0x29, 0xDE))

        assert sensor.resolve_state() == 10718
        assert sensor.unit_of_measurement() == "h"
        assert sensor.ha_device_class() is None

    def test_str_time_period_min(self):
        """Test resolve state with time_period_min sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="time_period_min",
        )
        sensor.sensor_value.payload = DPTArray((0x0, 0x54))

        assert sensor.resolve_state() == 84
        assert sensor.unit_of_measurement() == "min"
        assert sensor.ha_device_class() is None

    def test_str_time_period_msec(self):
        """Test resolve state with time_period_msec sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="time_period_msec",
        )
        sensor.sensor_value.payload = DPTArray((0x93, 0xC7))

        assert sensor.resolve_state() == 37831
        assert sensor.unit_of_measurement() == "ms"
        assert sensor.ha_device_class() is None

    def test_str_time_period_sec(self):
        """Test resolve state with time_period_sec sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type="time_period_sec",
        )
        sensor.sensor_value.payload = DPTArray((0xE0, 0xF5))

        assert sensor.resolve_state() == 57589
        assert sensor.unit_of_measurement() == "s"
        assert sensor.ha_device_class() is None

    def test_str_time_seconds(self):
        """Test resolve state with time_seconds sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="time_seconds"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0xEC, 0x91, 0x7C))

        assert sensor.resolve_state() == 7570.185546875
        assert sensor.unit_of_measurement() == "s"
        assert sensor.ha_device_class() is None

    def test_str_torque(self):
        """Test resolve state with torque sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="torque"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0x9, 0x23, 0x5F))

        assert sensor.resolve_state() == -2194.210693359375
        assert sensor.unit_of_measurement() == "N m"
        assert sensor.ha_device_class() is None

    def test_str_voltage(self):
        """Test resolve state with voltage sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="voltage"
        )
        sensor.sensor_value.payload = DPTArray((0x6D, 0xBF))

        assert sensor.resolve_state() == 120504.32
        assert sensor.unit_of_measurement() == "mV"
        assert sensor.ha_device_class() is None

    def test_str_volume(self):
        """Test resolve state with volume sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="volume"
        )
        sensor.sensor_value.payload = DPTArray((0x46, 0x16, 0x98, 0x43))

        assert sensor.resolve_state() == 9638.0654296875
        assert sensor.unit_of_measurement() == "m³"
        assert sensor.ha_device_class() is None

    def test_str_volume_flow(self):
        """Test resolve state with volume_flow sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="volume_flow"
        )
        sensor.sensor_value.payload = DPTArray((0x7C, 0xF5))

        assert sensor.resolve_state() == 415825.92
        assert sensor.unit_of_measurement() == "l/h"
        assert sensor.ha_device_class() is None

    def test_str_volume_flux(self):
        """Test resolve state with volume_flux sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="volume_flux"
        )
        sensor.sensor_value.payload = DPTArray((0xC5, 0x4, 0x2D, 0x72))

        assert sensor.resolve_state() == -2114.84033203125
        assert sensor.unit_of_measurement() == "m³/s"
        assert sensor.ha_device_class() is None

    def test_str_weight(self):
        """Test resolve state with weight sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="weight"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x20, 0x10, 0xE8))

        assert sensor.resolve_state() == 2561.056640625
        assert sensor.unit_of_measurement() == "N"
        assert sensor.ha_device_class() is None

    def test_str_work(self):
        """Test resolve state with work sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="work"
        )
        sensor.sensor_value.payload = DPTArray((0x45, 0x64, 0x5D, 0xBE))

        assert sensor.resolve_state() == 3653.85888671875
        assert sensor.unit_of_measurement() == "J"
        assert sensor.ha_device_class() is None

    def test_str_wind_speed_ms(self):
        """Test resolve state with wind_speed_ms sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="wind_speed_ms"
        )
        sensor.sensor_value.payload = DPTArray((0x7D, 0x98))

        assert sensor.resolve_state() == 469237.76
        assert sensor.unit_of_measurement() == "m/s"
        assert sensor.ha_device_class() is None

    def test_str_wind_speed_kmh(self):
        """Test resolve state with wind_speed_kmh sensor."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="wind_speed_kmh"
        )
        sensor.sensor_value.payload = DPTArray((0x68, 0x0))

        assert sensor.resolve_state() == 0.0
        assert sensor.unit_of_measurement() == "km/h"
        assert sensor.ha_device_class() is None

    #
    # SYNC
    #
    async def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", value_type="temperature", group_address_state="1/2/3"
        )
        await sensor.sync()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )

    #
    # HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test sensor has group address."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", value_type="temperature", group_address_state="1/2/3"
        )
        assert sensor.has_group_address(GroupAddress("1/2/3"))
        assert not sensor.has_group_address(GroupAddress("1/2/4"))

    #
    # TEST PROCESS
    #
    async def test_process(self):
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", value_type="temperature", group_address_state="1/2/3"
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x06, 0xA0))),
        )
        await sensor.process(telegram)
        assert sensor.sensor_value.payload == DPTArray((0x06, 0xA0))
        assert sensor.resolve_state() == 16.96

    async def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback is called."""

        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="temperature"
        )
        after_update_callback = AsyncMock()
        sensor.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x01, 0x02))),
        )
        await sensor.process(telegram)
        after_update_callback.assert_called_with(sensor)

    def test_unique_id(self):
        """Test unique id functionality."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="temperature"
        )
        assert sensor.unique_id == "1/2/3"
