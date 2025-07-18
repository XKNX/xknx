"""Unit test for Climate objects."""

from unittest.mock import Mock, patch

import pytest

from xknx import XKNX
from xknx.devices import Climate, ClimateMode
from xknx.devices.climate import FanSpeedMode, SetpointShiftMode
from xknx.dpt import (
    DPT2ByteFloat,
    DPTArray,
    DPTBinary,
    DPTHumidity,
    DPTHVACContrMode,
    DPTHVACMode,
    DPTHVACStatus,
    DPTTemperature,
    DPTValue1Count,
)
from xknx.dpt.dpt_20 import HVACControllerMode, HVACOperationMode, HVACStatus
from xknx.exceptions import ConversionError, DeviceIllegalValue
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueWrite

DPT_20102_MODES = [
    HVACOperationMode.AUTO,
    HVACOperationMode.COMFORT,
    HVACOperationMode.STANDBY,
    HVACOperationMode.ECONOMY,
    HVACOperationMode.BUILDING_PROTECTION,
]


class TestClimate:
    """Test class for Climate objects."""

    #
    # SUPPORTS TEMPERATURE / SETPOINT
    #
    def test_support_temperature(self) -> None:
        """Test supports_temperature flag."""
        xknx = XKNX()
        climate = Climate(xknx, "TestClimate", group_address_temperature="1/2/3")

        assert climate.temperature.initialized
        assert not climate.target_temperature.initialized

    def test_support_target_temperature(self) -> None:
        """Test supports_target__temperature flag."""
        xknx = XKNX()
        climate = Climate(xknx, "TestClimate", group_address_target_temperature="1/2/3")

        assert not climate.temperature.initialized
        assert climate.target_temperature.initialized

    def test_support_operation_mode(self) -> None:
        """Test supports_supports_operation_mode flag. One group address for all modes."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx, "TestClimate", group_address_operation_mode="1/2/4"
        )
        assert climate_mode.supports_operation_mode

    def test_support_operation_mode2(self) -> None:
        """Test supports_supports_operation_mode flag. Split group addresses for each mode."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx, "TestClimate", group_address_operation_mode_protection="1/2/4"
        )
        assert climate_mode.supports_operation_mode

    #
    # TEST HAS GROUP ADDRESS
    #
    def test_has_group_address(self) -> None:
        """Test if has_group_address function works."""
        xknx = XKNX()
        climate = Climate(
            xknx,
            "TestClimate",
            group_address_temperature="1/2/1",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
            group_address_setpoint_shift_state="1/2/4",
            group_address_on_off="1/2/11",
            group_address_on_off_state="1/2/12",
            group_address_humidity_state="1/2/16",
        )

        assert climate.has_group_address(GroupAddress("1/2/1"))
        assert climate.has_group_address(GroupAddress("1/2/2"))
        assert climate.has_group_address(GroupAddress("1/2/4"))
        assert climate.has_group_address(GroupAddress("1/2/11"))
        assert climate.has_group_address(GroupAddress("1/2/12"))
        assert climate.has_group_address(GroupAddress("1/2/16"))
        assert not climate.has_group_address(GroupAddress("1/2/99"))

        assert climate.group_addresses() == {
            GroupAddress("1/2/1"),
            GroupAddress("1/2/2"),
            GroupAddress("1/2/3"),
            GroupAddress("1/2/4"),
            GroupAddress("1/2/11"),
            GroupAddress("1/2/12"),
            GroupAddress("1/2/16"),
        }

    #
    # TEST HAS GROUP ADDRESS
    #
    def test_has_group_address_mode(self) -> None:
        """Test if has_group_address function works."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            name=None,
            group_address_operation_mode="1/2/4",
            group_address_operation_mode_state="1/2/5",
            group_address_operation_mode_protection="1/2/6",
            group_address_operation_mode_economy="1/2/7",
            group_address_operation_mode_comfort="1/2/8",
            group_address_operation_mode_standby="1/2/9",
            group_address_controller_status="1/2/10",
            group_address_controller_status_state="1/2/11",
            group_address_controller_mode="1/2/12",
            group_address_controller_mode_state="1/2/13",
            group_address_heat_cool="1/2/14",
            group_address_heat_cool_state="1/2/15",
        )

        climate = Climate(xknx, name="TestClimate", mode=climate_mode)

        assert climate.has_group_address(GroupAddress("1/2/4"))
        assert climate.has_group_address(GroupAddress("1/2/5"))
        assert climate.has_group_address(GroupAddress("1/2/6"))
        assert climate.has_group_address(GroupAddress("1/2/7"))
        assert climate.has_group_address(GroupAddress("1/2/8"))
        assert climate.has_group_address(GroupAddress("1/2/9"))
        assert climate.has_group_address(GroupAddress("1/2/10"))
        assert climate.has_group_address(GroupAddress("1/2/11"))
        assert climate.has_group_address(GroupAddress("1/2/12"))
        assert climate.has_group_address(GroupAddress("1/2/13"))
        assert climate.has_group_address(GroupAddress("1/2/14"))
        assert climate.has_group_address(GroupAddress("1/2/15"))
        assert not climate.has_group_address(GroupAddress("1/2/99"))

        assert climate.group_addresses() == {
            GroupAddress("1/2/4"),
            GroupAddress("1/2/5"),
            GroupAddress("1/2/6"),
            GroupAddress("1/2/7"),
            GroupAddress("1/2/8"),
            GroupAddress("1/2/9"),
            GroupAddress("1/2/10"),
            GroupAddress("1/2/11"),
            GroupAddress("1/2/12"),
            GroupAddress("1/2/13"),
            GroupAddress("1/2/14"),
            GroupAddress("1/2/15"),
        }

    #
    # TEST CALLBACK
    #
    async def test_process_callback(self) -> None:
        """Test if after_update_callback is called after update of Climate object was changed."""

        xknx = XKNX()
        climate = Climate(
            xknx,
            "TestClimate",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
            group_address_setpoint_shift_state="1/2/4",
            setpoint_shift_mode=SetpointShiftMode.DPT6010,
        )
        after_update_callback = Mock()
        climate.register_device_updated_cb(after_update_callback)
        xknx.devices.async_add(climate)

        climate.target_temperature.set(23.00)
        xknx.devices.process(xknx.telegrams.get_nowait())
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

        await climate.set_setpoint_shift(-2)
        xknx.devices.process(xknx.telegrams.get_nowait())
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

    async def test_process_callback_mode(self) -> None:
        """Test if after_update_callback is called after update of Climate object was changed."""

        xknx = XKNX()
        after_update_callback = Mock()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/5",
            device_updated_cb=after_update_callback,
        )

        await climate_mode.set_operation_mode(HVACOperationMode.COMFORT)
        after_update_callback.assert_called_with(climate_mode)
        after_update_callback.reset_mock()

        await climate_mode.set_operation_mode(HVACOperationMode.COMFORT)
        after_update_callback.assert_not_called()
        after_update_callback.reset_mock()

        await climate_mode.set_operation_mode(HVACOperationMode.BUILDING_PROTECTION)
        after_update_callback.assert_called_with(climate_mode)
        after_update_callback.reset_mock()

    async def test_process_callback_updated_via_telegram(self) -> None:
        """Test if after_update_callback is called after update of Climate object."""

        xknx = XKNX()
        climate = Climate(
            xknx,
            "TestClimate",
            group_address_temperature="1/2/1",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
        )
        after_update_callback = Mock()
        climate.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTTemperature.to_knx(23)),
        )
        climate.process(telegram)
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

        telegram = Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTTemperature.to_knx(23)),
        )
        climate.process(telegram)
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTValue1Count.to_knx(-4)),
        )
        climate.process(telegram)
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

    async def test_climate_mode_process_callback_updated_via_telegram(self) -> None:
        """Test if after_update_callback is called after update of ClimateMode object."""

        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx, "TestClimateMode", group_address_operation_mode="1/2/4"
        )
        after_update_callback = Mock()

        climate = Climate(xknx, "TestClimate", mode=climate_mode)
        climate_mode.register_device_updated_cb(after_update_callback)

        # Note: the climate object processes the telegram, but the cb
        # is called with the climate_mode object.
        telegram = Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueWrite(DPTArray(1)),
        )
        climate.process(telegram)
        after_update_callback.assert_called_with(climate_mode)
        after_update_callback.reset_mock()

    #
    # TEST SET OPERATION MODE
    #
    async def test_set_operation_mode(self) -> None:
        """Test set_operation_mode."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx, "TestClimate", group_address_operation_mode="1/2/4"
        )

        for operation_mode in DPT_20102_MODES:
            await climate_mode.set_operation_mode(operation_mode)
            assert xknx.telegrams.qsize() == 1
            telegram = xknx.telegrams.get_nowait()
            assert telegram == Telegram(
                destination_address=GroupAddress("1/2/4"),
                payload=GroupValueWrite(DPTHVACMode.to_knx(operation_mode)),
            )

    async def test_set_controller_operation_mode(self) -> None:
        """Test set_operation_mode with DPT20.105 controller."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx, "TestClimate", group_address_controller_mode="1/2/4"
        )

        for controller_mode in DPTHVACContrMode.get_valid_values():
            await climate_mode.set_controller_mode(controller_mode)
            assert xknx.telegrams.qsize() == 1
            telegram = xknx.telegrams.get_nowait()
            assert telegram == Telegram(
                destination_address=GroupAddress("1/2/4"),
                payload=GroupValueWrite(DPTHVACContrMode.to_knx(controller_mode)),
            )

    async def test_set_operation_mode_not_supported(self) -> None:
        """Test set_operation_mode but not supported."""
        xknx = XKNX()
        climate_mode = ClimateMode(xknx, "TestClimate")
        with pytest.raises(DeviceIllegalValue):
            await climate_mode.set_operation_mode(HVACOperationMode.AUTO)

    async def test_set_controller_mode_not_supported(self) -> None:
        """Test set_controller_mode but not supported."""
        xknx = XKNX()
        climate_mode = ClimateMode(xknx, "TestClimate")
        with pytest.raises(DeviceIllegalValue):
            await climate_mode.set_controller_mode(HVACControllerMode.HEAT)

    async def test_set_operation_mode_with_controller_status(self) -> None:
        """Test set_operation_mode with controller status address defined."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx, "TestClimate", group_address_controller_status="1/2/4"
        )

        # needs to be initialized before it can be sent
        with pytest.raises(ConversionError):
            await climate_mode.set_controller_mode(HVACControllerMode.HEAT)

        climate_mode.process(
            Telegram(
                destination_address=GroupAddress("1/2/4"),
                payload=GroupValueWrite(DPTArray((0x01,))),
            )
        )
        assert climate_mode.controller_mode == HVACControllerMode.COOL
        assert climate_mode.operation_mode == HVACOperationMode.COMFORT

        # controller mode
        await climate_mode.set_controller_mode(HVACControllerMode.HEAT)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueWrite(DPTArray((0x21,))),
        )
        climate_mode.process(telegram)  # process to have internal value updated
        # operation mode
        await climate_mode.set_operation_mode(HVACOperationMode.STANDBY)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueWrite(DPTArray((0x22,))),
        )

    async def test_set_operation_mode_with_separate_addresses(self) -> None:
        """Test set_operation_mode with combined and separated group addresses defined."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/4",
            group_address_operation_mode_protection="1/2/5",
            group_address_operation_mode_economy="1/2/6",
            group_address_operation_mode_comfort="1/2/7",
        )

        await climate_mode.set_operation_mode(HVACOperationMode.COMFORT)
        assert xknx.telegrams.qsize() == 4
        telegrams = [xknx.telegrams.get_nowait() for _ in range(4)]
        test_telegrams = [
            Telegram(
                destination_address=GroupAddress("1/2/4"),
                payload=GroupValueWrite(DPTArray(1)),
            ),
            Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTBinary(False)),
            ),
            Telegram(
                destination_address=GroupAddress("1/2/6"),
                payload=GroupValueWrite(DPTBinary(False)),
            ),
            Telegram(
                destination_address=GroupAddress("1/2/7"),
                payload=GroupValueWrite(DPTBinary(True)),
            ),
        ]

        for test_item in test_telegrams:
            assert test_item in telegrams

    async def test_set_heat_cool_binary(self) -> None:
        """Test set_operation_mode with binary heat/cool group addresses defined."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_heat_cool="1/2/14",
            group_address_heat_cool_state="1/2/15",
        )

        await climate_mode.set_controller_mode(HVACControllerMode.HEAT)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/14"),
            payload=GroupValueWrite(DPTBinary(True)),
        )

        await climate_mode.set_controller_mode(HVACControllerMode.COOL)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/14"),
            payload=GroupValueWrite(DPTBinary(False)),
        )

    async def test_set_multiple_mode(self) -> None:
        """Test if set operation or controller mode with multiple mode types."""

        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            name=None,
            group_address_operation_mode="1/2/4",
            group_address_operation_mode_state="1/2/5",
            group_address_operation_mode_protection="1/2/6",
            group_address_operation_mode_economy="1/2/7",
            group_address_operation_mode_comfort="1/2/8",
            group_address_operation_mode_standby="1/2/9",
            group_address_controller_status="1/2/10",
            group_address_controller_status_state="1/2/11",
            group_address_controller_mode="1/2/12",
            group_address_controller_mode_state="1/2/13",
            group_address_heat_cool="1/2/14",
            group_address_heat_cool_state="1/2/15",
        )

        def _process_all_telegrams() -> None:
            """Process all telegrams in the queue in ClimateMode device."""
            for _ in range(xknx.telegrams.qsize()):
                telegram = xknx.telegrams.get_nowait()
                climate_mode.process(telegram)

        # HVACStatus needs to be initialized before it can be sent
        climate_mode.process(
            Telegram(
                destination_address=GroupAddress("1/2/10"),
                payload=GroupValueWrite(DPTArray((0b10000000,))),
            )
        )
        await climate_mode.set_controller_mode(HVACControllerMode.HEAT)
        assert xknx.telegrams.qsize() == 3
        _process_all_telegrams()

        await climate_mode.set_operation_mode(HVACOperationMode.COMFORT)
        assert xknx.telegrams.qsize() == 6
        _process_all_telegrams()

        await climate_mode.set_controller_mode(HVACControllerMode.NODEM)
        assert xknx.telegrams.qsize() == 1  # only supported by controller mode
        _process_all_telegrams()
        assert climate_mode.operation_mode == HVACOperationMode.COMFORT
        assert climate_mode.controller_mode == HVACControllerMode.NODEM

        await climate_mode.set_controller_mode(HVACControllerMode.COOL)
        assert xknx.telegrams.qsize() == 3
        _process_all_telegrams()

        await climate_mode.set_operation_mode(HVACOperationMode.ECONOMY)
        assert xknx.telegrams.qsize() == 6
        _process_all_telegrams()
        assert climate_mode.operation_mode == HVACOperationMode.ECONOMY
        assert climate_mode.controller_mode == HVACControllerMode.COOL

    #
    # TEST initialized_for_setpoint_shift_calculations
    #
    async def test_initialized_for_setpoint_shift_calculations(self) -> None:
        """Test initialized_for_setpoint_shift_calculations method."""
        xknx = XKNX()
        climate1 = Climate(xknx, "TestClimate")
        xknx.devices.async_add(climate1)
        assert not climate1.initialized_for_setpoint_shift_calculations

        climate2 = Climate(
            xknx,
            "TestClimate",
            group_address_setpoint_shift="1/2/3",
            setpoint_shift_mode=SetpointShiftMode.DPT6010,
        )
        xknx.devices.async_add(climate2)
        assert not climate2.initialized_for_setpoint_shift_calculations
        await climate2.set_setpoint_shift(4)
        xknx.devices.process(xknx.telegrams.get_nowait())
        assert not climate2.initialized_for_setpoint_shift_calculations

        climate3 = Climate(
            xknx,
            "TestClimate",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
            setpoint_shift_mode=SetpointShiftMode.DPT6010,
        )
        xknx.devices.async_add(climate3)
        await climate3.set_setpoint_shift(4)
        xknx.devices.process(xknx.telegrams.get_nowait())
        assert not climate3.initialized_for_setpoint_shift_calculations

        climate3.target_temperature.set(23.00)
        xknx.devices.process(xknx.telegrams.get_nowait())
        assert climate3.initialized_for_setpoint_shift_calculations

    async def test_setpoint_shift_mode_autosensing(self) -> None:
        """Test autosensing setpoint_shift_mode."""

        xknx = XKNX()
        climate_dpt6 = Climate(
            xknx,
            "TestClimate",
            group_address_temperature="1/2/1",
            group_address_target_temperature_state="1/2/2",
            group_address_setpoint_shift="1/2/3",
        )
        climate_dpt6.target_temperature.value = 23.00

        # uninitialized
        with pytest.raises(ConversionError):
            await climate_dpt6.set_setpoint_shift(1)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTValue1Count.to_knx(-4)),
        )
        climate_dpt6.process(telegram)
        assert climate_dpt6.initialized_for_setpoint_shift_calculations

        await climate_dpt6.set_setpoint_shift(1)
        _telegram = xknx.telegrams.get_nowait()
        # DPTValue1Count is used for outgoing
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(10)),  # 1 / 0.1 setpoint_shift_step
        )

        climate_dpt9 = Climate(
            xknx,
            "TestClimate",
            group_address_temperature="1/2/1",
            group_address_target_temperature_state="1/2/2",
            group_address_setpoint_shift="1/2/3",
        )
        climate_dpt9.target_temperature.value = 23.00

        # uninitialized
        with pytest.raises(ConversionError):
            await climate_dpt9.set_setpoint_shift(1)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTTemperature.to_knx(-4)),
        )
        climate_dpt9.process(telegram)
        assert climate_dpt9.initialized_for_setpoint_shift_calculations

        await climate_dpt9.set_setpoint_shift(1)
        _telegram = xknx.telegrams.get_nowait()
        # DPTTemperature is used for outgoing
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTTemperature.to_knx(1)),
        )

    #
    # TEST for uninitialized target_temperature_min/target_temperature_max
    #
    def test_uninitalized_for_target_temperature_min_max(self) -> None:
        """Test if target_temperature_min/target_temperature_max return non if not initialized."""
        xknx = XKNX()
        climate = Climate(xknx, "TestClimate")
        assert climate.target_temperature_min is None
        assert climate.target_temperature_max is None

    #
    # TEST for uninitialized target_temperature_min/target_temperature_max but with overridden max and min temperature
    #
    def test_uninitalized_for_target_temperature_min_max_can_be_overridden(
        self,
    ) -> None:
        """Test if target_temperature_min/target_temperature_max return overridden value if specified."""
        xknx = XKNX()
        climate = Climate(xknx, "TestClimate", min_temp="7", max_temp="35")
        assert climate.target_temperature_min == "7"
        assert climate.target_temperature_max == "35"

    #
    # TEST for overridden max and min temp do have precedence over setpoint shift calculations
    #
    async def test_overridden_max_min_temperature_has_priority(self) -> None:
        """Test that the overridden min and max temp always have precedence over setpoint shift calculations."""
        xknx = XKNX()
        climate = Climate(
            xknx,
            "TestClimate",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
            setpoint_shift_mode=SetpointShiftMode.DPT6010,
            max_temp="42",
            min_temp="3",
        )
        xknx.devices.async_add(climate)

        await climate.set_setpoint_shift(4)
        xknx.devices.process(xknx.telegrams.get_nowait())
        assert not climate.initialized_for_setpoint_shift_calculations

        climate.target_temperature.set(23.00)
        xknx.devices.process(xknx.telegrams.get_nowait())
        assert climate.initialized_for_setpoint_shift_calculations
        assert climate.target_temperature_min == "3"
        assert climate.target_temperature_max == "42"

    #
    # TEST TARGET TEMPERATURE
    #
    async def test_target_temperature_up(self) -> None:
        """Test increase target temperature."""

        xknx = XKNX()
        climate = Climate(
            xknx,
            "TestClimate",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
            setpoint_shift_mode=SetpointShiftMode.DPT6010,
        )
        xknx.devices.async_add(climate)

        await climate.set_setpoint_shift(3)
        assert xknx.telegrams.qsize() == 1
        _telegram = xknx.telegrams.get_nowait()
        # DEFAULT_TEMPERATURE_STEP is 0.1 -> payload = setpoint_shift * 10
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(30)),
        )
        xknx.devices.process(_telegram)

        climate.target_temperature.set(23.00)
        assert xknx.telegrams.qsize() == 1
        _telegram = xknx.telegrams.get_nowait()
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPT2ByteFloat().to_knx(23.00)),
        )
        xknx.devices.process(_telegram)
        assert climate.base_temperature == 20

        # First change
        await climate.set_target_temperature(24.00)
        assert xknx.telegrams.qsize() == 2
        _telegram = xknx.telegrams.get_nowait()
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(40)),
        )
        xknx.devices.process(_telegram)
        _telegram = xknx.telegrams.get_nowait()
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPT2ByteFloat().to_knx(24.00)),
        )
        xknx.devices.process(_telegram)
        assert climate.target_temperature.value == 24.00

        # Second change
        await climate.set_target_temperature(23.50)
        assert xknx.telegrams.qsize() == 2
        _telegram = xknx.telegrams.get_nowait()
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(35)),
        )
        xknx.devices.process(_telegram)
        _telegram = xknx.telegrams.get_nowait()
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPT2ByteFloat().to_knx(23.50)),
        )
        xknx.devices.process(_telegram)
        assert climate.target_temperature.value == 23.50

        # Test max target temperature
        # Base (20) - setpoint_shift_max (6)
        assert climate.target_temperature_max == 26.00

        # third change - limit exceeded, setting to max
        await climate.set_target_temperature(26.50)
        assert xknx.telegrams.qsize() == 2
        xknx.devices.process(xknx.telegrams.get_nowait())
        xknx.devices.process(xknx.telegrams.get_nowait())
        assert climate.target_temperature_max == 26.00
        assert climate.setpoint_shift == 6

    async def test_target_temperature_down(self) -> None:
        """Test decrease target temperature."""

        xknx = XKNX()
        climate = Climate(
            xknx,
            "TestClimate",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
            setpoint_shift_mode=SetpointShiftMode.DPT6010,
        )
        xknx.devices.async_add(climate)

        await climate.set_setpoint_shift(1)
        assert xknx.telegrams.qsize() == 1
        _telegram = xknx.telegrams.get_nowait()
        # DEFAULT_TEMPERATURE_STEP is 0.1 -> payload = setpoint_shift * 10
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(10)),
        )
        xknx.devices.process(_telegram)

        climate.target_temperature.set(23.00)
        assert xknx.telegrams.qsize() == 1
        _telegram = xknx.telegrams.get_nowait()
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPT2ByteFloat().to_knx(23.00)),
        )
        xknx.devices.process(_telegram)
        assert climate.base_temperature == 22.0

        # First change
        await climate.set_target_temperature(20.50)
        assert xknx.telegrams.qsize() == 2
        _telegram = xknx.telegrams.get_nowait()
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0xF1)),
        )  # -15
        xknx.devices.process(_telegram)
        _telegram = xknx.telegrams.get_nowait()
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPT2ByteFloat().to_knx(20.50)),
        )
        xknx.devices.process(_telegram)
        assert climate.target_temperature.value == 20.50

        # Second change
        await climate.set_target_temperature(19.00)
        assert xknx.telegrams.qsize() == 2
        _telegram = xknx.telegrams.get_nowait()
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0xE2)),
        )  # -30
        xknx.devices.process(_telegram)
        _telegram = xknx.telegrams.get_nowait()
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPT2ByteFloat().to_knx(19.00)),
        )
        xknx.devices.process(_telegram)
        assert climate.target_temperature.value == 19.00

        # Test min target temperature
        # Base (22) - setpoint_shift_min (6)
        assert climate.target_temperature_min == 16.00

        # third change - limit exceeded, setting to min
        await climate.set_target_temperature(15.50)
        assert xknx.telegrams.qsize() == 2
        xknx.devices.process(xknx.telegrams.get_nowait())
        xknx.devices.process(xknx.telegrams.get_nowait())
        assert climate.target_temperature_min == 16.00
        assert climate.setpoint_shift == -6

    async def test_target_temperature_modified_step(self) -> None:
        """Test increase target temperature with modified step size."""

        xknx = XKNX()
        climate = Climate(
            xknx,
            "TestClimate",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
            setpoint_shift_mode=SetpointShiftMode.DPT6010,
            temperature_step=0.5,
            setpoint_shift_max=10,
            setpoint_shift_min=-10,
        )
        xknx.devices.async_add(climate)

        await climate.set_setpoint_shift(3)
        assert xknx.telegrams.qsize() == 1
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        # temperature_step is 0.5 -> payload = setpoint_shift * 2
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(6)),
        )

        climate.target_temperature.set(23.00)
        assert xknx.telegrams.qsize() == 1
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPT2ByteFloat().to_knx(23.00)),
        )
        assert climate.base_temperature == 20.00
        await climate.set_target_temperature(24.00)
        assert xknx.telegrams.qsize() == 2
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(8)),
        )
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPT2ByteFloat().to_knx(24.00)),
        )
        assert climate.target_temperature.value == 24.00

        # Test max/min target temperature
        assert climate.target_temperature_max == 30.00
        assert climate.target_temperature_min == 10.00

    #
    # TEST BASE TEMPERATURE
    #

    async def test_base_temperature(self) -> None:
        """Test base temperature."""

        xknx = XKNX()
        climate = Climate(
            xknx,
            "TestClimate",
            group_address_target_temperature_state="1/2/1",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
            setpoint_shift_mode=SetpointShiftMode.DPT6010,
        )
        xknx.devices.async_add(climate)

        await climate.set_target_temperature(21.00)
        assert xknx.telegrams.qsize() == 1
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPT2ByteFloat().to_knx(21.00)),
        )
        assert not climate.initialized_for_setpoint_shift_calculations
        assert climate.base_temperature is None

        # setpoint_shift initialized after target_temperature (no temperature change)
        await climate.set_setpoint_shift(1)
        assert xknx.telegrams.qsize() == 1
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        # DEFAULT_TEMPERATURE_STEP is 0.1 -> payload = setpoint_shift * 10
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(10)),
        )
        assert climate.initialized_for_setpoint_shift_calculations
        assert climate.base_temperature == 20.00

        # setpoint_shift changed after initialisation
        await climate.set_setpoint_shift(2)
        # setpoint_shift and target_temperature are sent to the bus
        assert xknx.telegrams.qsize() == 2
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        # DEFAULT_TEMPERATURE_STEP is 0.1 -> payload = setpoint_shift * 10
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(20)),
        )
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert climate.initialized_for_setpoint_shift_calculations
        assert climate.base_temperature == 20.00
        assert climate.target_temperature.value == 22

    async def test_target_temperature_step_mode_9002(self) -> None:
        """Test increase target temperature with modified step size."""

        xknx = XKNX()
        climate = Climate(
            xknx,
            "TestClimate",
            group_address_target_temperature_state="1/2/2",
            group_address_setpoint_shift="1/2/3",
            setpoint_shift_mode=SetpointShiftMode.DPT9002,
            setpoint_shift_max=10,
            setpoint_shift_min=-10,
        )
        xknx.devices.async_add(climate)

        # base temperature is 20 °C
        climate.target_temperature.process(
            Telegram(
                destination_address=GroupAddress("1/2/2"),
                payload=GroupValueWrite(DPT2ByteFloat().to_knx(20.00)),
            )
        )
        await climate.set_setpoint_shift(0)
        assert xknx.telegrams.qsize() == 1
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert climate.initialized_for_setpoint_shift_calculations
        assert climate.base_temperature == 20.00
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x00, 0x00))),
        )  # 0
        # - 0.6 °C = 19.4
        await climate.set_target_temperature(19.40)
        assert xknx.telegrams.qsize() == 1
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x87, 0xC4))),
        )  # -0.6
        # simulate incoming new target temperature for next calculation
        climate.target_temperature.process(
            Telegram(
                destination_address=GroupAddress("1/2/2"),
                payload=GroupValueWrite(DPT2ByteFloat().to_knx(19.40)),
            )
        )
        # + 3.5 °C = 23.5
        await climate.set_target_temperature(23.50)
        assert xknx.telegrams.qsize() == 1
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x01, 0x5E))),
        )  # +3.5

    #
    # TEST TEMPERATURE STEP
    #
    async def test_temperature_step(self) -> None:
        """Test base temperature step."""

        xknx = XKNX()
        climate = Climate(
            xknx,
            "TestClimate",
            group_address_target_temperature_state="1/2/1",
            group_address_target_temperature="1/2/2",
        )

        await climate.set_target_temperature(21.00)
        # default temperature_step for non setpoint_shift
        assert climate.temperature_step == 0.1

        climate = Climate(
            xknx,
            "TestClimate",
            group_address_target_temperature_state="1/2/1",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
        )
        # default temperature_step for setpoint_shift
        assert climate.temperature_step == 0.1

        climate = Climate(
            xknx,
            "TestClimate",
            group_address_target_temperature_state="1/2/1",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
            temperature_step=0.3,
        )
        assert climate.temperature_step == 0.3

    #
    # TEST SYNC
    #
    async def test_sync(self) -> None:
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        climate = Climate(xknx, "TestClimate", group_address_temperature="1/2/3")
        await climate.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())

    async def test_sync_operation_mode(self) -> None:
        """Test sync function / sending group reads to KNX bus for operation mode."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/3",
            group_address_operation_mode_state="1/2/4",
        )
        await climate_mode.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(GroupAddress("1/2/4"), payload=GroupValueRead())

    async def test_sync_controller_status(self) -> None:
        """Test sync function / sending group reads to KNX bus for controller status."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/23",
            group_address_controller_status_state="1/2/24",
        )
        await climate_mode.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(GroupAddress("1/2/24"), payload=GroupValueRead())

    async def test_sync_controller_mode(self) -> None:
        """Test sync function / sending group reads to KNX bus for controller mode."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_controller_mode="1/2/13",
            group_address_controller_mode_state="1/2/14",
        )
        await climate_mode.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(GroupAddress("1/2/14"), payload=GroupValueRead())

    async def test_sync_operation_mode_state(self) -> None:
        """Test sync function / sending group reads to KNX bus for multiple mode addresses."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/3",
            group_address_operation_mode_state="1/2/5",
            group_address_controller_status="1/2/4",
            group_address_controller_status_state="1/2/6",
            group_address_controller_mode="1/2/13",
            group_address_controller_mode_state="1/2/14",
        )
        await climate_mode.sync()
        assert xknx.telegrams.qsize() == 3

        telegrams = [xknx.telegrams.get_nowait() for _ in range(3)]
        assert telegrams == [
            Telegram(GroupAddress("1/2/5"), payload=GroupValueRead()),
            Telegram(GroupAddress("1/2/14"), payload=GroupValueRead()),
            Telegram(GroupAddress("1/2/6"), payload=GroupValueRead()),
        ]

    async def test_sync_heat_cool(self) -> None:
        """Test sync function / sending group reads to KNX bus for heat/cool."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_heat_cool="1/2/14",
            group_address_heat_cool_state="1/2/15",
        )
        await climate_mode.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(GroupAddress("1/2/15"), payload=GroupValueRead())

    async def test_sync_mode_from_climate(self) -> None:
        """Test sync function / propagating to mode."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx, "TestClimateMode", group_address_operation_mode_state="1/2/4"
        )
        climate = Climate(xknx, "TestClimate", mode=climate_mode)

        await climate.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(GroupAddress("1/2/4"), payload=GroupValueRead())

    async def test_sync_humidity(self) -> None:
        """Test sync function / sending group reads to KNX bus for humidity."""
        xknx = XKNX()
        climate = Climate(xknx, "TestClimate", group_address_humidity_state="1/2/16")
        await climate.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(GroupAddress("1/2/16"), payload=GroupValueRead())

    #
    # TEST PROCESS
    #
    async def test_process_temperature(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if temperature is processed correctly."""
        xknx = XKNX()
        climate = Climate(xknx, "TestClimate", group_address_temperature="1/2/3")

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTTemperature().to_knx(21.34)),
        )
        climate.process(telegram)
        assert climate.temperature.value == 21.34

    async def test_process_operation_mode(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if operation mode is processed correctly."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/5",
            group_address_controller_status="1/2/3",
        )
        for operation_mode in DPT_20102_MODES:
            telegram = Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTHVACMode.to_knx(operation_mode)),
            )
            climate_mode.process(telegram)
            assert climate_mode.operation_mode == operation_mode
        for operation_mode in DPT_20102_MODES:
            if operation_mode == HVACOperationMode.AUTO:
                continue
            telegram = Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(
                    DPTHVACStatus.to_knx(
                        HVACStatus(
                            mode=operation_mode,
                            dew_point=False,
                            heat_cool=HVACControllerMode.HEAT,
                            inactive=False,
                            frost_alarm=False,
                        )
                    )
                ),
            )
            climate_mode.process(telegram)
            assert climate_mode.operation_mode == operation_mode

    async def test_process_controller_mode(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if DPT20.105 controller mode is set correctly."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx, "TestClimate", group_address_controller_mode="1/2/5"
        )
        for controller_mode in DPTHVACContrMode.get_valid_values():
            telegram = Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTHVACContrMode.to_knx(controller_mode)),
            )
            climate_mode.process(telegram)
            assert climate_mode.controller_mode == controller_mode

    async def test_process_controller_status_wrong_payload(self) -> None:
        """Test process wrong telegram for controller status (wrong payload type)."""
        xknx = XKNX()
        updated_cb = Mock()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/5",
            group_address_controller_status="1/2/3",
            device_updated_cb=updated_cb,
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        with patch("logging.Logger.warning") as log_mock:
            climate_mode.process(telegram)
            log_mock.assert_called_once()
            updated_cb.assert_not_called()

    async def test_process_controller_status_payload_invalid_length(self) -> None:
        """Test process wrong telegram for controller status (wrong payload length)."""
        xknx = XKNX()
        updated_cb = Mock()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/5",
            group_address_controller_status="1/2/3",
            device_updated_cb=updated_cb,
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((23, 24))),
        )
        with patch("logging.Logger.warning") as log_mock:
            climate_mode.process(telegram)
            log_mock.assert_called_once()
            updated_cb.assert_not_called()

    async def test_process_operation_mode_wrong_payload(self) -> None:
        """Test process wrong telegram for operation mode (wrong payload type)."""
        xknx = XKNX()
        updated_cb = Mock()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/5",
            group_address_controller_status="1/2/3",
            device_updated_cb=updated_cb,
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        with patch("logging.Logger.warning") as log_mock:
            climate_mode.process(telegram)
            log_mock.assert_called_once()
            updated_cb.assert_not_called()

    async def test_process_operation_mode_payload_invalid_length(self) -> None:
        """Test process wrong telegram for operation mode (wrong payload length)."""
        xknx = XKNX()
        updated_cb = Mock()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/5",
            group_address_controller_status="1/2/3",
            device_updated_cb=updated_cb,
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray((23, 24))),
        )
        with patch("logging.Logger.warning") as log_mock:
            climate_mode.process(telegram)
            log_mock.assert_called_once()
            updated_cb.assert_not_called()

    async def test_process_callback_temp(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if callback is executed when receiving temperature."""

        xknx = XKNX()
        climate = Climate(xknx, "TestClimate", group_address_temperature="1/2/3")
        after_update_callback = Mock()
        climate.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTTemperature().to_knx(21.34)),
        )
        climate.process(telegram)
        after_update_callback.assert_called_with(climate)

    async def test_process_heat_cool(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if heat/cool is set correctly."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="i-op-mode",
            group_address_heat_cool="1/2/14",
            group_address_heat_cool_state="1/2/15",
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/14"),
            payload=GroupValueWrite(DPTBinary(False)),
        )
        climate_mode.process(telegram)
        assert climate_mode.controller_mode == HVACControllerMode.COOL

        telegram = Telegram(
            destination_address=GroupAddress("1/2/14"),
            payload=GroupValueWrite(DPTBinary(True)),
        )
        climate_mode.process(telegram)
        assert climate_mode.controller_mode == HVACControllerMode.HEAT

    async def test_process_humidity(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if humidity is processed correctly."""
        xknx = XKNX()
        climate = Climate(xknx, "TestClimate", group_address_humidity_state="1/2/16")
        after_update_callback = Mock()
        climate.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/16"),
            payload=GroupValueWrite(DPTHumidity.to_knx(45.6)),
        )
        climate.process(telegram)

        assert climate.humidity.value == 45.6
        after_update_callback.assert_called_with(climate)

    #
    # SUPPORTED OPERATION MODES
    #
    def test_supported_operation_modes(self) -> None:
        """Test get_supported_operation_modes with combined group address."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx, "TestClimate", group_address_operation_mode="1/2/5"
        )
        assert set(climate_mode.operation_modes) == {
            HVACOperationMode.AUTO,
            HVACOperationMode.COMFORT,
            HVACOperationMode.STANDBY,
            HVACOperationMode.ECONOMY,
            HVACOperationMode.BUILDING_PROTECTION,
        }

    def test_supported_modes_controller_status(self) -> None:
        """Test supported modes with HVAC status group address."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx, "TestClimate", group_address_controller_status="1/2/5"
        )
        assert set(climate_mode.operation_modes) == {
            HVACOperationMode.COMFORT,
            HVACOperationMode.STANDBY,
            HVACOperationMode.ECONOMY,
            HVACOperationMode.BUILDING_PROTECTION,
        }
        assert set(climate_mode.controller_modes) == {
            HVACControllerMode.HEAT,
            HVACControllerMode.COOL,
        }

    def test_supported_operation_modes_no_mode(self) -> None:
        """Test get_supported_operation_modes no operation_modes supported."""
        xknx = XKNX()
        climate_mode = ClimateMode(xknx, "TestClimate")
        assert not climate_mode.operation_modes

    def test_supported_operation_modes_with_separate_addresses(self) -> None:
        """Test get_supported_operation_modes with separated group addresses."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode_protection="1/2/5",
            group_address_operation_mode_economy="1/2/6",
            group_address_operation_mode_comfort="1/2/7",
        )

        assert set(climate_mode.operation_modes) == {
            HVACOperationMode.COMFORT,
            HVACOperationMode.ECONOMY,
            HVACOperationMode.BUILDING_PROTECTION,
            HVACOperationMode.STANDBY,
        }

    def test_supported_operation_modes_only_economy(self) -> None:
        """Test get_supported_operation_modes with only economy mode supported."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx, "TestClimate", group_address_operation_mode_economy="1/2/7"
        )
        # If one binary climate object is set, this mode and Standby are supported.
        # All binary modes off -> Standby according to MDT heating actuator
        assert set(climate_mode.operation_modes) == {
            HVACOperationMode.ECONOMY,
            HVACOperationMode.STANDBY,
        }

    def test_supported_operation_modes_heat_cool(self) -> None:
        """Test supported controller_modes with heat_cool address."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_heat_cool="1/2/14",
            group_address_heat_cool_state="1/2/15",
        )
        assert climate_mode.supports_controller_mode
        assert set(climate_mode.controller_modes) == {
            HVACControllerMode.HEAT,
            HVACControllerMode.COOL,
        }

    def test_supported_operation_modes_heat_cool_read_only(self) -> None:
        """Test supported controller_modes with heat_cool_state address."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_heat_cool_state="1/2/15",
        )
        assert climate_mode.supports_controller_mode
        assert climate_mode.controller_modes == []  # only writable modes
        assert set(climate_mode.gather_controller_modes(only_writable=False)) == {
            HVACControllerMode.HEAT,
            HVACControllerMode.COOL,
        }

    def test_custom_supported_operation_modes(self) -> None:
        """Test get_supported_operation_modes with custom mode."""
        modes = [HVACOperationMode.STANDBY, HVACOperationMode.ECONOMY]
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/7",
            operation_modes=modes,
        )
        assert climate_mode.operation_modes == modes

    def test_custom_supported_operation_modes_as_str(self) -> None:
        """Test get_supported_operation_modes with custom mode as str list."""
        str_modes = ["Standby", "Building Protection"]
        modes = [HVACOperationMode.STANDBY, HVACOperationMode.BUILDING_PROTECTION]
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode="1/2/7",
            operation_modes=str_modes,
        )
        assert climate_mode.operation_modes == modes

    def test_custom_supported_operation_modes_only_valid(self) -> None:
        """Test get_supported_operation_modes with custom mode as str list."""
        str_modes = [
            "Standby",
            "Building Protection",
            "Comfort",  # Comfort can't be set - no address set
        ]
        modes = [HVACOperationMode.STANDBY, HVACOperationMode.BUILDING_PROTECTION]
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_operation_mode_standby="1/2/7",
            group_address_operation_mode_protection="1/2/8",
            operation_modes=str_modes,
        )
        assert climate_mode.operation_modes == modes

    def test_custom_supported_controller_modes_as_str(self) -> None:
        """Test get_supported_operation_modes with custom mode as str list."""
        str_modes = ["Heat", "Cool", HVACControllerMode.NODEM]
        modes = [
            HVACControllerMode.HEAT,
            HVACControllerMode.COOL,
            HVACControllerMode.NODEM,
        ]
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            group_address_controller_mode="1/2/7",
            controller_modes=str_modes,
        )
        assert climate_mode.controller_modes == modes

    def test_custom_supported_controller_modes_when_controller_mode_unsupported(
        self,
    ) -> None:
        """Test get_supported_operation_modes with custom mode as str list."""
        str_modes = ["Heat", "Cool"]
        modes = []
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            "TestClimate",
            controller_modes=str_modes,
        )
        assert climate_mode.controller_modes == modes

    async def test_process_power_status(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if DPT20.105 controller mode is set correctly."""
        xknx = XKNX()
        climate = Climate(xknx, "TestClimate", group_address_on_off="1/2/2")
        telegram = Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        climate.process(telegram)
        assert climate.is_on is True

        climate_inv = Climate(
            xknx, "TestClimate", group_address_on_off="1/2/2", on_off_invert=True
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        climate_inv.process(telegram)
        assert climate_inv.is_on is False

    async def test_power_on_off(self) -> None:
        """Test turn_on and turn_off functions."""
        xknx = XKNX()
        climate = Climate(xknx, "TestClimate", group_address_on_off="1/2/2")
        xknx.devices.async_add(climate)

        await climate.turn_on()
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert climate.is_on is True
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(True)),
        )
        await climate.turn_off()
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert climate.is_on is False
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(False)),
        )

        climate_inv = Climate(
            xknx, "TestClimate", group_address_on_off="1/2/2", on_off_invert=True
        )
        xknx.devices.async_add(climate_inv)

        await climate_inv.turn_on()
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert climate_inv.is_on is True
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(False)),
        )
        await climate_inv.turn_off()
        _telegram = xknx.telegrams.get_nowait()
        xknx.devices.process(_telegram)
        assert climate_inv.is_on is False
        assert _telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(True)),
        )

    async def test_is_active(self) -> None:
        """Test is_active property."""
        xknx = XKNX()
        climate_active = Climate(
            xknx, "TestClimate1", group_address_active_state="1/1/1"
        )
        xknx.devices.async_add(climate_active)
        climate_command = Climate(
            xknx, "TestClimate2", group_address_command_value_state="2/2/2"
        )
        xknx.devices.async_add(climate_command)
        climate_active_command = Climate(
            xknx,
            "TestClimate3",
            group_address_active_state="1/1/1",
            group_address_command_value_state="2/2/2",
        )
        xknx.devices.async_add(climate_active_command)

        assert climate_active.is_active is None
        assert climate_command.is_active is None
        assert climate_active_command.is_active is None
        # set active to False
        xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/1/1"),
                payload=GroupValueWrite(DPTBinary(False)),
            )
        )
        assert climate_active.is_active is False
        assert climate_command.is_active is None
        assert climate_active_command.is_active is False
        # set command to 50%
        xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("2/2/2"),
                payload=GroupValueWrite(DPTArray((128,))),
            )
        )
        assert climate_active.is_active is False
        assert climate_command.is_active is True
        assert climate_active_command.is_active is False
        # set active to True
        xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/1/1"),
                payload=GroupValueWrite(DPTBinary(True)),
            )
        )
        assert climate_active.is_active is True
        assert climate_command.is_active is True
        assert climate_active_command.is_active is True
        # set command to 0%
        xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("2/2/2"),
                payload=GroupValueWrite(DPTArray((0,))),
            )
        )
        assert climate_active.is_active is True
        assert climate_command.is_active is False
        assert climate_active_command.is_active is True
        # only command initialized
        climate_active_command.active.value = None
        assert climate_active_command.is_active is False

    async def test_fan_speed(self) -> None:
        """Test fan speed functionality."""
        xknx = XKNX()
        climate_step = Climate(
            xknx,
            name="TestClimate",
            group_address_fan_speed="1/2/3",
            group_address_fan_speed_state="1/2/4",
            fan_speed_mode=FanSpeedMode.STEP,
        )
        xknx.devices.async_add(climate_step)
        climate_percent = Climate(
            xknx,
            name="TestClimate",
            group_address_fan_speed="1/2/5",
            group_address_fan_speed_state="1/2/6",
        )
        assert climate_percent.fan_speed_mode == FanSpeedMode.PERCENT
        xknx.devices.async_add(climate_percent)

        # Test initial state
        assert climate_step.current_fan_speed is None
        assert climate_percent.current_fan_speed is None

        xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray(2)),
            )
        )
        assert climate_step.current_fan_speed == 2

        # 140 is 55% as byte (0...255)
        xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTArray(140)),
            )
        )
        assert climate_percent.current_fan_speed == 55

        await climate_step.set_fan_speed(3)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(3)),
        )

        await climate_percent.set_fan_speed(45)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        # 115 is 45% as byte (0...255)
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray(115)),
        )

        xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/2/4"),
                payload=GroupValueWrite(DPTArray(2)),
            )
        )
        assert climate_step.current_fan_speed == 2

        # 140 is 55% as byte (0...255)
        xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/2/6"),
                payload=GroupValueWrite(DPTArray(140)),
            )
        )
        assert climate_percent.current_fan_speed == 55

    async def test_swing(self) -> None:
        """Test fan speed functionality."""
        xknx = XKNX()
        climate_swing = Climate(
            xknx,
            name="TestClimate",
            group_address_swing="1/2/3",
            group_address_swing_state="1/2/4",
        )
        xknx.devices.async_add(climate_swing)

        # Test initial state
        assert climate_swing.current_swing is None

        xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTBinary(True)),
            )
        )
        assert climate_swing.current_swing is True

        await climate_swing.set_swing(False)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(False)),
        )

    async def test_horizontal_swing(self) -> None:
        """Test fan speed functionality."""
        xknx = XKNX()
        climate_horizontal_swing = Climate(
            xknx,
            name="TestClimate",
            group_address_horizontal_swing="1/2/3",
            group_address_horizontal_swing_state="1/2/4",
        )
        xknx.devices.async_add(climate_horizontal_swing)

        # Test initial state
        assert climate_horizontal_swing.current_horizontal_swing is None

        xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTBinary(True)),
            )
        )
        assert climate_horizontal_swing.current_horizontal_swing is True

        await climate_horizontal_swing.set_horizontal_swing(False)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(False)),
        )
