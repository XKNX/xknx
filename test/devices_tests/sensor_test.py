"""Unit test for Sensor objects."""

from unittest.mock import Mock

import pytest

from xknx import XKNX
from xknx.devices import Sensor
from xknx.dpt import (
    DPT2ByteFloat,
    DPT2ByteSigned,
    DPT2ByteUnsigned,
    DPT4ByteFloat,
    DPT4ByteSigned,
    DPT4ByteUnsigned,
    DPT8ByteSigned,
    DPTArray,
    DPTScaling,
    DPTSignedRelativeValue,
    DPTString,
    DPTValue1ByteUnsigned,
)
from xknx.exceptions.exception import DeviceIllegalValue
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


class TestSensor:
    """Test class for Sensor objects."""

    @pytest.mark.parametrize(
        "value_type,raw_payload,expected_state",
        [
            # DPT-14 values are according to ETS group monitor values
            (
                "absolute_temperature",
                DPTArray((0x44, 0xD7, 0xD2, 0x8B)),
                1726.579,
            ),
            (
                "acceleration",
                DPTArray((0x45, 0x94, 0xD8, 0x5D)),
                4763.045,
            ),
            (
                "volume_liquid_litre",
                DPTArray((0x00, 0x00, 0x01, 0x00)),
                256,
            ),
            (
                "volume_m3",
                DPTArray((0x00, 0x00, 0x01, 0x00)),
                256,
            ),
            (
                "active_energy",
                DPTArray((0x26, 0x37, 0x49, 0x7F)),
                641157503,
            ),
            (
                "active_energy_kwh",
                DPTArray((0x37, 0x5, 0x5, 0xEA)),
                923076074,
            ),
            (
                "activity",
                DPTArray((0x45, 0x76, 0x0, 0xA3)),
                3936.04,
            ),
            (
                "amplitude",
                DPTArray((0x45, 0x9A, 0xED, 0x8)),
                4957.629,
            ),
            (
                "angle",
                DPTArray((0xE4,)),
                322,
            ),
            (
                "angle_deg",
                DPTArray((0x44, 0x5C, 0x20, 0x2B)),
                880.5026,
            ),
            (
                "angle_rad",
                DPTArray((0x44, 0x36, 0x75, 0x1)),
                729.8282,
            ),
            (
                "angular_frequency",
                DPTArray((0x43, 0xBC, 0x20, 0x8D)),
                376.2543,
            ),
            (
                "angular_momentum",
                DPTArray((0xC2, 0x75, 0xB7, 0xB5)),
                -61.4294,
            ),
            (
                "angular_velocity",
                DPTArray((0xC4, 0xD9, 0x10, 0xB3)),
                -1736.522,
            ),
            (
                "apparant_energy",
                DPTArray((0xD3, 0xBD, 0x1E, 0xA5)),
                -742580571,
            ),
            (
                "apparant_energy_kvah",
                DPTArray((0x49, 0x40, 0xC9, 0x9)),
                1228982537,
            ),
            (
                "area",
                DPTArray((0x45, 0x63, 0x1E, 0xCD)),
                3633.925,
            ),
            (
                "brightness",
                DPTArray((0xC3, 0x56)),
                50006,
            ),
            (
                "capacitance",
                DPTArray((0x45, 0xC9, 0x1D, 0x9D)),
                6435.702,
            ),
            (
                "charge_density_surface",
                DPTArray((0x45, 0xDB, 0x66, 0x99)),
                7020.825,
            ),
            (
                "charge_density_volume",
                DPTArray((0xC4, 0x8C, 0x33, 0xD7)),
                -1121.62,
            ),
            (
                "color_temperature",
                DPTArray((0x6C, 0x95)),
                27797,
            ),
            (
                "common_temperature",
                DPTArray((0x45, 0xD9, 0xC6, 0x3F)),
                6968.781,
            ),
            (
                "compressibility",
                DPTArray((0x45, 0x89, 0x94, 0xAB)),
                4402.583,
            ),
            (
                "conductance",
                DPTArray((0x45, 0xA6, 0x28, 0xF9)),
                5317.122,
            ),
            (
                "counter_pulses",
                DPTArray((0x9D,)),
                -99,
            ),
            (
                "current",
                DPTArray((0xCA, 0xCC)),
                51916,
            ),
            (
                "delta_time_hrs",
                DPTArray((0x47, 0x80)),
                18304,
            ),
            (
                "delta_time_min",
                DPTArray((0xB9, 0x7B)),
                -18053,
            ),
            (
                "delta_time_ms",
                DPTArray((0x58, 0x77)),
                22647,
            ),
            (
                "delta_time_sec",
                DPTArray((0xA3, 0x6A)),
                -23702,
            ),
            (
                "density",
                DPTArray((0x44, 0xA5, 0xCB, 0x27)),
                1326.349,
            ),
            (
                "electrical_conductivity",
                DPTArray((0xC4, 0xC6, 0xF5, 0x6E)),
                -1591.67,
            ),
            (
                "electric_charge",
                DPTArray((0x46, 0x14, 0xF6, 0xA0)),
                9533.656,
            ),
            (
                "electric_current",
                DPTArray((0x45, 0xAD, 0x45, 0x90)),
                5544.695,
            ),
            (
                "electric_current_density",
                DPTArray((0x45, 0x7C, 0x57, 0xF6)),
                4037.498,
            ),
            (
                "electric_dipole_moment",
                DPTArray((0x45, 0x58, 0xF1, 0x73)),
                3471.091,
            ),
            (
                "electric_displacement",
                DPTArray((0xC5, 0x34, 0x8B, 0x0)),
                -2888.688,
            ),
            (
                "electric_field_strength",
                DPTArray((0xC6, 0x17, 0x1C, 0x39)),
                -9671.056,
            ),
            (
                "electric_flux",
                DPTArray((0x45, 0x8F, 0x6C, 0xFD)),
                4589.624,
            ),
            (
                "electric_flux_density",
                DPTArray((0xC6, 0x0, 0x50, 0xA8)),
                -8212.164,
            ),
            (
                "electric_polarization",
                DPTArray((0x45, 0xF8, 0x89, 0xC6)),
                7953.222,
            ),
            (
                "electric_potential",
                DPTArray((0xC6, 0x18, 0xA4, 0xAF)),
                -9769.171,
            ),
            (
                "electric_potential_difference",
                DPTArray((0xC6, 0xF, 0x1D, 0x6)),
                -9159.256,
            ),
            (
                "electromagnetic_moment",
                DPTArray((0x45, 0x82, 0x48, 0xAE)),
                4169.085,
            ),
            (
                "electromotive_force",
                DPTArray((0x45, 0xBC, 0xEF, 0xEB)),
                6045.99,
            ),
            (
                "energy",
                DPTArray((0x45, 0x4B, 0xB3, 0xF8)),
                3259.248,
            ),
            (
                "enthalpy",
                DPTArray((0x76, 0xDD)),
                287866.88,
            ),
            (
                "flow_rate_m3h",
                DPTArray((0x99, 0xEA, 0xC0, 0x55)),
                -1712668587,
            ),
            (
                "force",
                DPTArray((0x45, 0x9E, 0x2C, 0xE1)),
                5061.61,
            ),
            (
                "frequency",
                DPTArray((0x45, 0xC2, 0x3C, 0x44)),
                6215.533,
            ),
            (
                "heatcapacity",
                DPTArray((0xC5, 0xB3, 0x56, 0x7E)),
                -5738.812,
            ),
            (
                "heatflowrate",
                DPTArray((0x44, 0xEC, 0x80, 0x7A)),
                1892.015,
            ),
            (
                "heat_quantity",
                DPTArray((0xC5, 0xA6, 0xB6, 0xD5)),
                -5334.854,
            ),
            (
                "humidity",
                DPTArray((0x7E, 0xE1)),
                577044.48,
            ),
            (
                "impedance",
                DPTArray((0x45, 0xDD, 0x79, 0x6D)),
                7087.178,
            ),
            (
                "illuminance",
                DPTArray((0x7C, 0x5E)),
                366346.24,
            ),
            (
                "kelvin_per_percent",
                DPTArray((0xFA, 0xBD)),
                -441384.96,
            ),
            (
                "length",
                DPTArray((0xC5, 0x9D, 0xAE, 0xC5)),
                -5045.846,
            ),
            (
                "length_mm",
                DPTArray((0x56, 0xB9)),
                22201,
            ),
            (
                "light_quantity",
                DPTArray((0x45, 0x4A, 0xF5, 0x68)),
                3247.338,
            ),
            (
                "long_delta_timesec",
                DPTArray((0x45, 0xB2, 0x17, 0x54)),
                1169299284,
            ),
            (
                "luminance",
                DPTArray((0x45, 0x18, 0xD9, 0x76)),
                2445.591,
            ),
            (
                "luminous_flux",
                DPTArray((0x45, 0xBD, 0x16, 0x9)),
                6050.754,
            ),
            (
                "luminous_intensity",
                DPTArray((0x46, 0xB, 0xBE, 0x7E)),
                8943.623,
            ),
            (
                "magnetic_field_strength",
                DPTArray((0x44, 0x15, 0xF1, 0xAD)),
                599.7762,
            ),
            (
                "magnetic_flux",
                DPTArray((0xC5, 0xCB, 0x3C, 0x98)),
                -6503.574,
            ),
            (
                "magnetic_flux_density",
                DPTArray((0x45, 0xB6, 0xBD, 0x42)),
                5847.657,
            ),
            (
                "magnetic_moment",
                DPTArray((0xC3, 0x8E, 0x7F, 0x73)),
                -284.9957,
            ),
            (
                "magnetic_polarization",
                DPTArray((0x45, 0x8C, 0xFA, 0xCB)),
                4511.349,
            ),
            (
                "magnetization",
                DPTArray((0x45, 0xF7, 0x9D, 0xA2)),
                7923.704,
            ),
            (
                "magnetomotive_force",
                DPTArray((0xC6, 0x4, 0xC2, 0xDA)),
                -8496.713,
            ),
            (
                "mass",
                DPTArray((0x45, 0x8F, 0x70, 0xA4)),
                4590.08,
            ),
            (
                "mass_flux",
                DPTArray((0xC6, 0x7, 0x34, 0xFF)),
                -8653.249,
            ),
            (
                "mol",
                DPTArray((0xC4, 0xA0, 0xF4, 0x68)),
                -1287.638,
            ),
            (
                "momentum",
                DPTArray((0xC5, 0x27, 0xAA, 0x5B)),
                -2682.647,
            ),
            (
                "percent",
                DPTArray((0xE3,)),
                89,
            ),
            (
                "percentU8",
                DPTArray((0x6B,)),
                107,
            ),
            (
                "percentV8",
                DPTArray((0x20,)),
                32,
            ),
            (
                "percentV16",
                DPTArray((0x8A, 0x2F)),
                -301.61,
            ),
            (
                "phaseanglerad",
                DPTArray((0x45, 0x54, 0xAC, 0x2E)),
                3402.761,
            ),
            (
                "phaseangledeg",
                DPTArray((0xC5, 0x25, 0x13, 0x38)),
                -2641.201,
            ),
            (
                "power",
                DPTArray((0x45, 0xCB, 0xE2, 0x5C)),
                6524.295,
            ),
            (
                "power_2byte",
                DPTArray((0x6D, 0x91)),
                116736.0,
            ),
            (
                "power_density",
                DPTArray((0x65, 0x3E)),
                54968.32,
            ),
            (
                "powerfactor",
                DPTArray((0xC5, 0x35, 0x28, 0x21)),
                -2898.508,
            ),
            (
                "ppm",
                DPTArray((0x7F, 0x74)),
                625213.44,
            ),
            (
                "pressure",
                DPTArray((0xC5, 0xE6, 0xE6, 0x63)),
                -7388.798,
            ),
            (
                "pressure_2byte",
                DPTArray((0x7C, 0xF4)),
                415498.24,
            ),
            (
                "pulse",
                DPTArray((0xFC,)),
                252,
            ),
            (
                "rain_amount",
                DPTArray((0xE0, 0xD0)),
                -75366.4,
            ),
            (
                "reactance",
                DPTArray((0x45, 0xB0, 0x50, 0x91)),
                5642.071,
            ),
            (
                "reactive_energy",
                DPTArray((0x1A, 0x49, 0x6D, 0xA7)),
                441019815,
            ),
            (
                "reactive_energy_kvarh",
                DPTArray((0xCC, 0x62, 0x5, 0x31)),
                -865991375,
            ),
            (
                "resistance",
                DPTArray((0xC5, 0xFC, 0x5F, 0xC2)),
                -8075.97,
            ),
            (
                "resistivity",
                DPTArray((0xC5, 0x57, 0x76, 0xC3)),
                -3447.423,
            ),
            (
                "rotation_angle",
                DPTArray((0x2D, 0xDC)),
                11740,
            ),
            (
                "scene_number",
                DPTArray((0x1,)),
                2,
            ),
            (
                "self_inductance",
                DPTArray((0xC4, 0xA1, 0xB0, 0x6)),
                -1293.501,
            ),
            (
                "solid_angle",
                DPTArray((0xC5, 0xC6, 0xE5, 0x47)),
                -6364.66,
            ),
            (
                "sound_intensity",
                DPTArray((0xC4, 0xF2, 0x56, 0xE6)),
                -1938.716,
            ),
            (
                "speed",
                DPTArray((0xC5, 0xCD, 0x1C, 0x6A)),
                -6563.552,
            ),
            (
                "stress",
                DPTArray((0x45, 0xDC, 0xA8, 0xF2)),
                7061.118,
            ),
            (
                "surface_tension",
                DPTArray((0x46, 0xB, 0xAC, 0x11)),
                8939.017,
            ),
            (
                "temperature",
                DPTArray((0x77, 0x88)),
                315883.52,
            ),
            (
                "temperature_a",
                DPTArray((0xF1, 0xDB)),
                -257720.32,
            ),
            (
                "temperature_difference",
                DPTArray((0xC6, 0xC, 0x50, 0xBC)),
                -8980.184,
            ),
            (
                "temperature_difference_2byte",
                DPTArray((0xA9, 0xF4)),
                -495.36,
            ),
            (
                "temperature_f",
                DPTArray((0x67, 0xA9)),
                80322.56,
            ),
            (
                "thermal_capacity",
                DPTArray((0x45, 0x83, 0xEA, 0xB3)),
                4221.337,
            ),
            (
                "thermal_conductivity",
                DPTArray((0xC5, 0x9C, 0x4D, 0x22)),
                -5001.642,
            ),
            (
                "thermoelectric_power",
                DPTArray((0x41, 0xCF, 0x9E, 0x4F)),
                25.9523,
            ),
            (
                "time_1",
                DPTArray((0x5E, 0x1E)),
                32071.68,
            ),
            (
                "time_2",
                DPTArray((0xFB, 0x29)),
                -405995.52,
            ),
            (
                "time_period_100msec",
                DPTArray((0x6A, 0x35)),
                2718900,
            ),
            (
                "time_period_10msec",
                DPTArray((0x32, 0x3)),
                128030,
            ),
            (
                "time_period_hrs",
                DPTArray((0x29, 0xDE)),
                10718,
            ),
            (
                "time_period_min",
                DPTArray((0x0, 0x54)),
                84,
            ),
            (
                "time_period_msec",
                DPTArray((0x93, 0xC7)),
                37831,
            ),
            (
                "time_period_sec",
                DPTArray((0xE0, 0xF5)),
                57589,
            ),
            (
                "time_seconds",
                DPTArray((0x45, 0xEC, 0x91, 0x7C)),
                7570.186,
            ),
            (
                "torque",
                DPTArray((0xC5, 0x9, 0x23, 0x5F)),
                -2194.211,
            ),
            (
                "voltage",
                DPTArray((0x6D, 0xBF)),
                120504.32,
            ),
            (
                "volume",
                DPTArray((0x46, 0x16, 0x98, 0x43)),
                9638.065,
            ),
            (
                "volume_flow",
                DPTArray((0x7C, 0xF5)),
                415825.92,
            ),
            (
                "volume_flux",
                DPTArray((0xC5, 0x4, 0x2D, 0x72)),
                -2114.84,
            ),
            (
                "weight",
                DPTArray((0x45, 0x20, 0x10, 0xE8)),
                2561.057,
            ),
            (
                "work",
                DPTArray((0x45, 0x64, 0x5D, 0xBE)),
                3653.859,
            ),
            (
                "wind_speed_ms",
                DPTArray((0x7D, 0x98)),
                469237.76,
            ),
            (
                "wind_speed_kmh",
                DPTArray((0x68, 0x0)),
                0.0,
            ),
        ],
    )
    async def test_sensor_value_types(
        self,
        value_type,
        raw_payload,
        expected_state,
    ):
        """Test sensor value types."""
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/2/3",
            value_type=value_type,
        )
        sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(value=raw_payload),
            )
        )

        assert sensor.resolve_state() == expected_state

    async def test_sensor_invalid_value_type(self):
        """Test sensor with invalid value type."""
        with pytest.raises(DeviceIllegalValue):
            Sensor(
                XKNX(),
                "TestSensor",
                group_address_state="1/2/3",
                value_type="invalid",
            )

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
        after_update_callback = Mock()
        sensor.register_device_updated_cb(after_update_callback)
        payload = DPTArray((0x00, 0x00, 0x01, 0x00))
        #  set initial payload of sensor
        sensor.sensor_value.value = 256
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueWrite(payload)
        )
        response_telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(payload),
        )
        # verify not called when always_callback is False
        sensor.process(telegram)
        after_update_callback.assert_not_called()
        after_update_callback.reset_mock()

        sensor.always_callback = True
        # verify called when always_callback is True
        sensor.process(telegram)
        after_update_callback.assert_called_once()
        after_update_callback.reset_mock()

        # verify not called when processing read responses
        sensor.process(response_telegram)
        after_update_callback.assert_not_called()

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
        sensor.process(telegram)
        assert sensor.sensor_value.value == 16.96
        assert sensor.sensor_value.telegram.payload.value == DPTArray((0x06, 0xA0))
        assert sensor.resolve_state() == 16.96
        # test HomeAssistant device class
        assert sensor.ha_device_class() == "temperature"

    async def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback is called."""

        xknx = XKNX()
        sensor = Sensor(
            xknx, "TestSensor", group_address_state="1/2/3", value_type="temperature"
        )
        after_update_callback = Mock()
        sensor.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x01, 0x02))),
        )
        sensor.process(telegram)
        after_update_callback.assert_called_with(sensor)
        assert sensor.last_telegram == telegram

    #
    # TEST GET SUPPORTED DPTS
    #
    async def test_get_supported_dpts(self):
        """Test supported dpts."""
        supported_dpts = Sensor.supported_dpts

        # supported_dpts should be not empty or print error message
        assert supported_dpts, "Supported DPTs are empty"

        # Expected types
        expected_base_types = (
            DPTValue1ByteUnsigned,
            DPTScaling,
            DPTSignedRelativeValue,
            DPT2ByteUnsigned,
            DPT2ByteSigned,
            DPT2ByteFloat,
            DPT4ByteUnsigned,
            DPT4ByteSigned,
            DPT4ByteFloat,
            DPTString,
            DPT8ByteSigned,
        )

        # Verify all items are subclasses of expected types
        for dpt in supported_dpts:
            assert issubclass(
                dpt, expected_base_types
            ), f"{dpt.__name__} is not a subclass of expected base types: {', '.join([base.__name__ for base in expected_base_types])}"

    @pytest.mark.parametrize(
        "dpt, expected_value_type",
        [
            ("5", "1byte_unsigned"),
            ("5.001", "percent"),
            ("5.003", "angle"),
            ("5.004", "percentU8"),
            ("5.005", "decimal_factor"),
            ("5.006", "tariff"),
            ("5.010", "pulse"),
            ("6", "1byte_signed"),
            ("6.001", "percentV8"),
            ("6.010", "counter_pulses"),
            ("7", "2byte_unsigned"),
            ("7.001", "pulse_2byte"),
            ("7.002", "time_period_msec"),
            ("7.003", "time_period_10msec"),
            ("7.004", "time_period_100msec"),
            ("7.005", "time_period_sec"),
            ("7.006", "time_period_min"),
            ("7.007", "time_period_hrs"),
            ("7.011", "length_mm"),
            ("7.012", "current"),
            ("7.013", "brightness"),
            ("7.600", "color_temperature"),
            ("8", "2byte_signed"),
            ("8.001", "pulse_2byte_signed"),
            ("8.002", "delta_time_ms"),
            ("8.003", "delta_time_10ms"),
            ("8.004", "delta_time_100ms"),
            ("8.005", "delta_time_sec"),
            ("8.006", "delta_time_min"),
            ("8.007", "delta_time_hrs"),
            ("8.010", "percentV16"),
            ("8.011", "rotation_angle"),
            ("8.012", "length_m"),
            ("9", "2byte_float"),
            ("9.001", "temperature"),
            ("9.002", "temperature_difference_2byte"),
            ("9.003", "temperature_a"),
            ("9.004", "illuminance"),
            ("9.005", "wind_speed_ms"),
            ("9.006", "pressure_2byte"),
            ("9.007", "humidity"),
            ("9.008", "ppm"),
            ("9.009", "air_flow"),
            ("9.010", "time_1"),
            ("9.011", "time_2"),
            ("9.020", "voltage"),
            ("9.021", "curr"),
            ("9.022", "power_density"),
            ("9.023", "kelvin_per_percent"),
            ("9.024", "power_2byte"),
            ("9.025", "volume_flow"),
            ("9.026", "rain_amount"),
            ("9.027", "temperature_f"),
            ("9.028", "wind_speed_kmh"),
            ("9.029", "absolute_humidity"),
            ("9.030", "concentration_ugm3"),
            ("9.60000", "enthalpy"),
            ("12", "4byte_unsigned"),
            ("12.001", "pulse_4_ucount"),
            ("12.100", "long_time_period_sec"),
            ("12.101", "long_time_period_min"),
            ("12.102", "long_time_period_hrs"),
            ("12.1200", "volume_liquid_litre"),
            ("12.1201", "volume_m3"),
            ("13", "4byte_signed"),
            ("13.001", "pulse_4byte"),
            ("13.002", "flow_rate_m3h"),
            ("13.010", "active_energy"),
            ("13.011", "apparant_energy"),
            ("13.012", "reactive_energy"),
            ("13.013", "active_energy_kwh"),
            ("13.014", "apparant_energy_kvah"),
            ("13.015", "reactive_energy_kvarh"),
            ("13.016", "active_energy_mwh"),
            ("13.100", "long_delta_timesec"),
            ("14", "4byte_float"),
            ("14.000", "acceleration"),
            ("14.001", "acceleration_angular"),
            ("14.002", "activation_energy"),
            ("14.003", "activity"),
            ("14.004", "mol"),
            ("14.005", "amplitude"),
            ("14.006", "angle_rad"),
            ("14.007", "angle_deg"),
            ("14.008", "angular_momentum"),
            ("14.009", "angular_velocity"),
            ("14.010", "area"),
            ("14.011", "capacitance"),
            ("14.012", "charge_density_surface"),
            ("14.013", "charge_density_volume"),
            ("14.014", "compressibility"),
            ("14.015", "conductance"),
            ("14.016", "electrical_conductivity"),
            ("14.017", "density"),
            ("14.018", "electric_charge"),
            ("14.019", "electric_current"),
            ("14.020", "electric_current_density"),
            ("14.021", "electric_dipole_moment"),
            ("14.022", "electric_displacement"),
            ("14.023", "electric_field_strength"),
            ("14.024", "electric_flux"),
            ("14.025", "electric_flux_density"),
            ("14.026", "electric_polarization"),
            ("14.027", "electric_potential"),
            ("14.028", "electric_potential_difference"),
            ("14.029", "electromagnetic_moment"),
            ("14.030", "electromotive_force"),
            ("14.031", "energy"),
            ("14.032", "force"),
            ("14.033", "frequency"),
            ("14.034", "angular_frequency"),
            ("14.035", "heatcapacity"),
            ("14.036", "heatflowrate"),
            ("14.037", "heat_quantity"),
            ("14.038", "impedance"),
            ("14.039", "length"),
            ("14.040", "light_quantity"),
            ("14.041", "luminance"),
            ("14.042", "luminous_flux"),
            ("14.043", "luminous_intensity"),
            ("14.044", "magnetic_field_strength"),
            ("14.045", "magnetic_flux"),
            ("14.046", "magnetic_flux_density"),
            ("14.047", "magnetic_moment"),
            ("14.048", "magnetic_polarization"),
            ("14.049", "magnetization"),
            ("14.050", "magnetomotive_force"),
            ("14.051", "mass"),
            ("14.052", "mass_flux"),
            ("14.053", "momentum"),
            ("14.054", "phaseanglerad"),
            ("14.055", "phaseangledeg"),
            ("14.056", "power"),
            ("14.057", "powerfactor"),
            ("14.058", "pressure"),
            ("14.059", "reactance"),
            ("14.060", "resistance"),
            ("14.061", "resistivity"),
            ("14.062", "self_inductance"),
            ("14.063", "solid_angle"),
            ("14.064", "sound_intensity"),
            ("14.065", "speed"),
            ("14.066", "stress"),
            ("14.067", "surface_tension"),
            ("14.068", "common_temperature"),
            ("14.069", "absolute_temperature"),
            ("14.070", "temperature_difference"),
            ("14.071", "thermal_capacity"),
            ("14.072", "thermal_conductivity"),
            ("14.073", "thermoelectric_power"),
            ("14.074", "time_seconds"),
            ("14.075", "torque"),
            ("14.076", "volume"),
            ("14.077", "volume_flux"),
            ("14.078", "weight"),
            ("14.079", "work"),
            ("14.080", "apparent_power"),
            ("16.000", "string"),
            ("16.001", "latin_1"),
            ("17.001", "scene_number"),
            ("29", "8byte_signed"),
            ("29.010", "active_energy_8byte"),
            ("29.011", "apparant_energy_8byte"),
            ("29.012", "reactive_energy_8byte"),
            ("99.999", None),
        ],
    )
    async def test_transcode_dpt_to_value_type(
        self, dpt: str, expected_value_type: str
    ):
        """Test transcode DPT to value type with pytest parameters."""
        result = Sensor.transcode_dpt_to_value_type(dpt)
        assert (
            result == expected_value_type
        ), f"Expected {expected_value_type}, got {result}"
