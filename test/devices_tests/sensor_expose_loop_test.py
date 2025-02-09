"""Unit test for Sensor and ExposeSensor objects."""

from unittest.mock import AsyncMock, Mock, call

import pytest

from xknx import XKNX
from xknx.devices import BinarySensor, ExposeSensor, Sensor
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import AddressFilter, Telegram, TelegramDirection
from xknx.telegram.address import GroupAddress, InternalGroupAddress
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


class TestSensorExposeLoop:
    """Process incoming Telegrams and send the values to the bus again."""

    test_cases = [
        ("absolute_temperature", DPTArray((0x44, 0xD7, 0xD2, 0x87)), 1726.579),
        ("acceleration", DPTArray((0x45, 0x94, 0xD8, 0x5C)), 4763.045),
        ("acceleration_angular", DPTArray((0x45, 0xEA, 0x62, 0x33)), 7500.275),
        ("activation_energy", DPTArray((0x46, 0x0, 0x3E, 0xEE)), 8207.732),
        ("active_energy", DPTArray((0x26, 0x37, 0x49, 0x7F)), 641157503),
        ("active_energy_kwh", DPTArray((0x37, 0x5, 0x5, 0xEA)), 923076074),
        ("activity", DPTArray((0x45, 0x76, 0x0, 0xA4)), 3936.04),
        ("amplitude", DPTArray((0x45, 0x9A, 0xED, 0x8)), 4957.629),
        ("angle", DPTArray((0xE4,)), 322),
        ("angle_deg", DPTArray((0x44, 0x5C, 0x20, 0x2B)), 880.5026),
        ("angle_rad", DPTArray((0x44, 0x36, 0x75, 0x1)), 729.8282),
        ("angular_frequency", DPTArray((0x43, 0xBC, 0x20, 0x8D)), 376.2543),
        ("angular_momentum", DPTArray((0xC2, 0x75, 0xB7, 0xB5)), -61.4294),
        ("angular_velocity", DPTArray((0xC4, 0xD9, 0x10, 0xB4)), -1736.522),
        ("apparant_energy", DPTArray((0xD3, 0xBD, 0x1E, 0xA5)), -742580571),
        ("apparant_energy_kvah", DPTArray((0x49, 0x40, 0xC9, 0x9)), 1228982537),
        ("area", DPTArray((0x45, 0x63, 0x1E, 0xCD)), 3633.925),
        ("brightness", DPTArray((0xC3, 0x56)), 50006),
        ("capacitance", DPTArray((0x45, 0xC9, 0x1D, 0x9E)), 6435.702),
        ("charge_density_surface", DPTArray((0x45, 0xDB, 0x66, 0x9A)), 7020.825),
        ("charge_density_volume", DPTArray((0xC4, 0x8C, 0x33, 0xD7)), -1121.62),
        ("color_temperature", DPTArray((0x6C, 0x95)), 27797),
        ("common_temperature", DPTArray((0x45, 0xD9, 0xC6, 0x3F)), 6968.781),
        ("compressibility", DPTArray((0x45, 0x89, 0x94, 0xAA)), 4402.583),
        ("conductance", DPTArray((0x45, 0xA6, 0x28, 0xFA)), 5317.122),
        ("counter_pulses", DPTArray((0x9D,)), -99),
        ("current", DPTArray((0xCA, 0xCC)), 51916),
        ("delta_time_hrs", DPTArray((0x47, 0x80)), 18304),
        ("delta_time_min", DPTArray((0xB9, 0x7B)), -18053),
        ("delta_time_ms", DPTArray((0x58, 0x77)), 22647),
        ("delta_time_sec", DPTArray((0xA3, 0x6A)), -23702),
        ("density", DPTArray((0x44, 0xA5, 0xCB, 0x2B)), 1326.349),
        ("electrical_conductivity", DPTArray((0xC4, 0xC6, 0xF5, 0x71)), -1591.67),
        ("electric_charge", DPTArray((0x46, 0x14, 0xF6, 0xA0)), 9533.656),
        ("electric_current", DPTArray((0x45, 0xAD, 0x45, 0x8F)), 5544.695),
        ("electric_current_density", DPTArray((0x45, 0x7C, 0x57, 0xF8)), 4037.498),
        ("electric_dipole_moment", DPTArray((0x39, 0x01, 0x74, 0x2F)), 0.0001234568),
        ("electric_displacement", DPTArray((0xC5, 0x34, 0x8B, 0x02)), -2888.688),
        ("electric_field_strength", DPTArray((0xC6, 0x17, 0x1C, 0x39)), -9671.056),
        ("electric_flux", DPTArray((0x45, 0x8F, 0x6C, 0xFE)), 4589.624),
        ("electric_flux_density", DPTArray((0xC6, 0x0, 0x50, 0xA8)), -8212.164),
        ("electric_polarization", DPTArray((0x45, 0xF8, 0x89, 0xC7)), 7953.222),
        ("electric_potential", DPTArray((0xC6, 0x18, 0xA4, 0xAF)), -9769.171),
        ("electric_potential_difference", DPTArray((0xC6, 0xF, 0x1D, 0x6)), -9159.256),
        ("electromagnetic_moment", DPTArray((0x45, 0x82, 0x48, 0xAE)), 4169.085),
        ("electromotive_force", DPTArray((0x45, 0xBC, 0xEF, 0xEC)), 6045.99),
        ("energy", DPTArray((0x45, 0x4B, 0xB3, 0xF8)), 3259.248),
        ("enthalpy", DPTArray((0x76, 0xDD)), 287866.88),
        ("flow_rate_m3h", DPTArray((0x99, 0xEA, 0xC0, 0x55)), -1712668587),
        ("force", DPTArray((0x45, 0x9E, 0x2C, 0xE1)), 5061.61),
        ("frequency", DPTArray((0x45, 0xC2, 0x3C, 0x44)), 6215.533),
        ("heatcapacity", DPTArray((0xC5, 0xB3, 0x56, 0x7F)), -5738.812),
        ("heatflowrate", DPTArray((0x44, 0xEC, 0x80, 0x7B)), 1892.015),
        ("heat_quantity", DPTArray((0xC5, 0xA6, 0xB6, 0xD5)), -5334.854),
        ("humidity", DPTArray((0x7E, 0xE1)), 577044.48),
        ("impedance", DPTArray((0x45, 0xDD, 0x79, 0x6D)), 7087.178),
        ("illuminance", DPTArray((0x7C, 0x5E)), 366346.24),
        ("kelvin_per_percent", DPTArray((0xFA, 0xBD)), -441384.96),
        ("length", DPTArray((0xC5, 0x9D, 0xAE, 0xC5)), -5045.846),
        ("length_mm", DPTArray((0x56, 0xB9)), 22201),
        ("light_quantity", DPTArray((0x45, 0x4A, 0xF5, 0x68)), 3247.338),
        ("long_delta_timesec", DPTArray((0x45, 0xB2, 0x17, 0x54)), 1169299284),
        ("luminance", DPTArray((0x45, 0x18, 0xD9, 0x75)), 2445.591),
        ("luminous_flux", DPTArray((0x45, 0xBD, 0x16, 0x8)), 6050.754),
        ("luminous_intensity", DPTArray((0x46, 0xB, 0xBE, 0x7E)), 8943.623),
        ("magnetic_field_strength", DPTArray((0x44, 0x15, 0xF1, 0xAD)), 599.7762),
        ("magnetic_flux", DPTArray((0xC5, 0xCB, 0x3C, 0x98)), -6503.574),
        ("magnetic_flux_density", DPTArray((0x45, 0xB6, 0xBD, 0x42)), 5847.657),
        ("magnetic_moment", DPTArray((0xC3, 0x8E, 0x7F, 0x73)), -284.9957),
        ("magnetic_polarization", DPTArray((0x45, 0x8C, 0xFA, 0xCB)), 4511.349),
        ("magnetization", DPTArray((0x45, 0xF7, 0x9D, 0xA2)), 7923.704),
        ("magnetomotive_force", DPTArray((0xC6, 0x4, 0xC2, 0xDA)), -8496.713),
        ("mass", DPTArray((0x45, 0x8F, 0x70, 0xA4)), 4590.08),
        ("mass_flux", DPTArray((0xC6, 0x7, 0x34, 0xFF)), -8653.249),
        ("mol", DPTArray((0xC4, 0xA0, 0xF4, 0x6A)), -1287.638),
        ("momentum", DPTArray((0xC5, 0x27, 0xAA, 0x5A)), -2682.647),
        ("percent", DPTArray((0xE3,)), 89),
        ("percentU8", DPTArray((0x6B,)), 107),
        ("percentV8", DPTArray((0x20,)), 32),
        ("percentV16", DPTArray((0x8A, 0x2F)), -301.61),
        ("phaseanglerad", DPTArray((0x45, 0x54, 0xAC, 0x2D)), 3402.761),
        ("phaseangledeg", DPTArray((0xC5, 0x25, 0x13, 0x37)), -2641.201),
        ("power", DPTArray((0x45, 0xCB, 0xE2, 0x5C)), 6524.295),
        ("power_2byte", DPTArray((0x6D, 0x91)), 116736.00),
        ("power_density", DPTArray((0x65, 0x3E)), 54968.32),
        ("powerfactor", DPTArray((0xC5, 0x35, 0x28, 0x21)), -2898.508),
        ("ppm", DPTArray((0xF3, 0xC8)), -176947.20),
        ("pressure", DPTArray((0xC5, 0xE6, 0xE6, 0x62)), -7388.798),
        ("pressure_2byte", DPTArray((0x7C, 0xF4)), 415498.24),
        ("pulse", DPTArray((0xFC,)), 252),
        ("pulse_2byte_signed", DPTArray((0x80, 0x44)), -32700),
        ("rain_amount", DPTArray((0xF0, 0x1)), -335380.48),
        ("reactance", DPTArray((0x45, 0xB0, 0x50, 0x91)), 5642.071),
        ("reactive_energy", DPTArray((0x1A, 0x49, 0x6D, 0xA7)), 441019815),
        ("reactive_energy_kvarh", DPTArray((0xCC, 0x62, 0x5, 0x31)), -865991375),
        ("resistance", DPTArray((0xC5, 0xFC, 0x5F, 0xC3)), -8075.97),
        ("resistivity", DPTArray((0xC5, 0x57, 0x76, 0xC5)), -3447.423),
        ("rotation_angle", DPTArray((0x2D, 0xDC)), 11740),
        ("scene_number", DPTArray((0x1,)), 2),
        ("self_inductance", DPTArray((0xC4, 0xA1, 0xB0, 0x8)), -1293.501),
        ("solid_angle", DPTArray((0xC5, 0xC6, 0xE5, 0x48)), -6364.66),
        ("sound_intensity", DPTArray((0xC4, 0xF2, 0x56, 0xE9)), -1938.716),
        ("speed", DPTArray((0xC5, 0xCD, 0x1C, 0x6A)), -6563.552),
        ("stress", DPTArray((0x45, 0xDC, 0xA8, 0xF2)), 7061.118),
        ("surface_tension", DPTArray((0x46, 0xB, 0xAC, 0x11)), 8939.017),
        (
            "string",
            DPTArray(
                (
                    0x4B,
                    0x4E,
                    0x58,
                    0x20,
                    0x69,
                    0x73,
                    0x20,
                    0x4F,
                    0x4B,
                    0x0,
                    0x0,
                    0x0,
                    0x0,
                    0x0,
                )
            ),
            "KNX is OK",
        ),
        ("temperature", DPTArray((0x77, 0x88)), 315883.52),
        ("temperature_a", DPTArray((0xF1, 0xDB)), -257720.32),
        ("temperature_difference", DPTArray((0xC6, 0xC, 0x50, 0xBC)), -8980.184),
        ("temperature_difference_2byte", DPTArray((0xA9, 0xF4)), -495.36),
        ("temperature_f", DPTArray((0x67, 0xA9)), 80322.56),
        ("thermal_capacity", DPTArray((0x45, 0x83, 0xEA, 0xB2)), 4221.337),
        ("thermal_conductivity", DPTArray((0xC5, 0x9C, 0x4D, 0x23)), -5001.642),
        ("thermoelectric_power", DPTArray((0x41, 0xCF, 0x9E, 0x4F)), 25.9523),
        ("time_1", DPTArray((0x5E, 0x1E)), 32071.68),
        ("time_2", DPTArray((0xFB, 0x29)), -405995.52),
        ("time_period_100msec", DPTArray((0x6A, 0x35)), 2718900),
        ("time_period_10msec", DPTArray((0x32, 0x3)), 128030),
        ("time_period_hrs", DPTArray((0x29, 0xDE)), 10718),
        ("time_period_min", DPTArray((0x0, 0x54)), 84),
        ("time_period_msec", DPTArray((0x93, 0xC7)), 37831),
        ("time_period_sec", DPTArray((0xE0, 0xF5)), 57589),
        ("time_seconds", DPTArray((0x45, 0xEC, 0x91, 0x7D)), 7570.186),
        ("torque", DPTArray((0xC5, 0x9, 0x23, 0x60)), -2194.211),
        ("voltage", DPTArray((0x6D, 0xBF)), 120504.32),
        ("volume", DPTArray((0x46, 0x16, 0x98, 0x43)), 9638.065),
        ("volume_flow", DPTArray((0x7C, 0xF5)), 415825.92),
        ("volume_flux", DPTArray((0xC5, 0x4, 0x2D, 0x71)), -2114.84),
        ("weight", DPTArray((0x45, 0x20, 0x10, 0xE9)), 2561.057),
        ("work", DPTArray((0x45, 0x64, 0x5D, 0xBE)), 3653.859),
        ("wind_speed_ms", DPTArray((0x7D, 0x98)), 469237.76),
        ("wind_speed_kmh", DPTArray((0x7F, 0x55)), 615055.36),
        # # Generic DPT Without Min/Max and Unit.
        ("1byte_unsigned", DPTArray(0x08), 8),
        ("2byte_unsigned", DPTArray((0x30, 0x39)), 12345),
        ("2byte_signed", DPTArray((0x00, 0x01)), 1),
        ("2byte_float", DPTArray((0x2E, 0xA9)), 545.6),
        ("4byte_unsigned", DPTArray((0x00, 0x00, 0x00, 0x00)), 0),
        ("4byte_signed", DPTArray((0xFD, 0x1A, 0xA1, 0x09)), -48586487),
        ("4byte_float", DPTArray((0xC2, 0x09, 0xEE, 0xCC)), -34.4832),
    ]

    @pytest.mark.parametrize(("value_type", "test_payload", "test_value"), test_cases)
    async def test_array_sensor_loop(
        self, value_type: str, test_payload: DPTArray, test_value: float
    ) -> None:
        """Test sensor and expose_sensor with different values."""
        xknx = XKNX()
        xknx.cemi_handler = AsyncMock()
        await xknx.telegram_queue.start()

        expose = ExposeSensor(
            xknx,
            "TestExpose",
            group_address="1/1/1",
            value_type=value_type,
        )
        xknx.devices.async_add(expose)
        assert expose.resolve_state() is None
        # set a value from expose - HA sends strings for new values
        stringified_value = str(test_value)
        await expose.set(stringified_value)

        outgoing_telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(test_payload),
        )
        await xknx.telegrams.join()
        xknx.cemi_handler.send_telegram.assert_called_with(outgoing_telegram)
        assert expose.resolve_state() == test_value

        # init sensor after expose is set - with same group address
        sensor = Sensor(
            xknx,
            "TestSensor",
            group_address_state="1/1/1",
            value_type=value_type,
        )
        xknx.devices.async_add(sensor)
        assert sensor.resolve_state() is None

        # read sensor state (from expose as it has the same GA)
        # wait_for_result so we don't have to await self.xknx.telegrams.join()
        await sensor.sync(wait_for_result=True)
        read_telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueRead(),
        )
        response_telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueResponse(test_payload),
        )
        xknx.cemi_handler.send_telegram.assert_has_calls(
            [
                call(read_telegram),
                call(response_telegram),
            ]
        )
        # test if Sensor has successfully read from ExposeSensor
        assert sensor.resolve_state() == test_value
        assert expose.resolve_state() == sensor.resolve_state()
        await xknx.telegram_queue.stop()


class TestBinarySensorExposeLoop:
    """Process incoming Telegrams and send the values to the bus again."""

    @pytest.mark.parametrize(
        ("value_type", "test_payload", "test_value"),
        [
            ("binary", DPTBinary(0), False),
            ("binary", DPTBinary(1), True),
        ],
    )
    async def test_binary_sensor_loop(
        self, value_type: str, test_payload: DPTBinary, test_value: bool
    ) -> None:
        """Test binary_sensor and expose_sensor with binary values."""
        xknx = XKNX()
        xknx.cemi_handler = AsyncMock()
        await xknx.telegram_queue.start()

        expose = ExposeSensor(
            xknx,
            "TestExpose",
            group_address="1/1/1",
            value_type=value_type,
        )
        xknx.devices.async_add(expose)
        assert expose.resolve_state() is None

        await expose.set(test_value)
        await xknx.telegrams.join()
        outgoing_telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(test_payload),
        )
        xknx.cemi_handler.send_telegram.assert_called_with(outgoing_telegram)
        assert expose.resolve_state() == test_value

        bin_sensor = BinarySensor(
            xknx,
            "TestSensor",
            group_address_state="1/1/1",
        )
        xknx.devices.async_add(bin_sensor)
        assert bin_sensor.state is None

        # read sensor state (from expose as it has the same GA)
        # wait_for_result so we don't have to await self.xknx.telegrams.join()
        await bin_sensor.sync(wait_for_result=True)
        read_telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueRead(),
        )
        response_telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueResponse(test_payload),
        )
        xknx.cemi_handler.send_telegram.assert_has_calls(
            [
                call(read_telegram),
                call(response_telegram),
            ]
        )
        # test if Sensor has successfully read from ExposeSensor
        assert bin_sensor.state == test_value
        assert expose.resolve_state() == bin_sensor.state
        await xknx.telegram_queue.stop()


class TestBinarySensorInternalGroupAddressExposeLoop:
    """Process incoming Telegrams and send values to other devices."""

    @pytest.mark.parametrize(
        ("value_type", "test_payload", "test_value"),
        [
            ("binary", DPTBinary(0), False),
            ("binary", DPTBinary(1), True),
        ],
    )
    async def test_binary_sensor_loop(
        self, value_type: str, test_payload: DPTBinary, test_value: bool
    ) -> None:
        """Test binary_sensor and expose_sensor with binary values."""
        xknx = XKNX()
        xknx.cemi_handler = AsyncMock()

        telegram_callback = Mock()
        xknx.telegram_queue.register_telegram_received_cb(
            telegram_callback,
            address_filters=[AddressFilter("i-test")],
            match_for_outgoing=True,
        )
        await xknx.telegram_queue.start()

        expose = ExposeSensor(
            xknx,
            "TestExpose",
            group_address="i-test",
            value_type=value_type,
        )
        xknx.devices.async_add(expose)
        assert expose.resolve_state() is None

        await expose.set(test_value)
        await xknx.telegrams.join()
        outgoing_telegram = Telegram(
            destination_address=InternalGroupAddress("i-test"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(test_payload),
        )
        # InternalGroupAddress isn't passed to knxip_interface
        xknx.cemi_handler.send_telegram.assert_not_called()
        telegram_callback.assert_called_with(outgoing_telegram)
        assert expose.resolve_state() == test_value

        bin_sensor = BinarySensor(
            xknx,
            "TestSensor",
            group_address_state="i-test",
        )
        xknx.devices.async_add(bin_sensor)
        assert bin_sensor.state is None

        # read sensor state (from expose as it has the same GA)
        # wait_for_result so we don't have to await self.xknx.telegrams.join()
        await bin_sensor.sync(wait_for_result=True)
        read_telegram = Telegram(
            destination_address=InternalGroupAddress("i-test"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueRead(),
        )
        response_telegram = Telegram(
            destination_address=InternalGroupAddress("i-test"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueResponse(test_payload),
        )
        xknx.cemi_handler.send_telegram.assert_not_called()
        telegram_callback.assert_has_calls(
            [
                call(read_telegram),
                call(response_telegram),
            ]
        )
        # test if Sensor has successfully read from ExposeSensor
        assert bin_sensor.state == test_value
        assert expose.resolve_state() == bin_sensor.state
        await xknx.telegram_queue.stop()
