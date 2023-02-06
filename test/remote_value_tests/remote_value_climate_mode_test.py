"""Unit test for RemoteValueClimateMode objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.dpt.dpt_hvac_mode import HVACControllerMode, HVACOperationMode
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import (
    RemoteValueBinaryHeatCool,
    RemoteValueBinaryOperationMode,
    RemoteValueControllerMode,
    RemoteValueOperationMode,
)
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueOperationMode:
    """Test class for RemoteValueOperationMode objects."""

    def test_to_knx_operation_mode(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueOperationMode(
            xknx, climate_mode_type=RemoteValueOperationMode.ClimateModeType.HVAC_MODE
        )
        assert remote_value.to_knx(HVACOperationMode.COMFORT) == DPTArray((0x01,))

    def test_to_knx_controller_mode(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueControllerMode(xknx)
        assert remote_value.to_knx(HVACControllerMode.HEAT) == DPTArray((0x01,))

    def test_to_knx_binary(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx, operation_mode=HVACOperationMode.COMFORT
        )
        assert remote_value.to_knx(HVACOperationMode.COMFORT) == DPTBinary(True)
        assert remote_value.to_knx(HVACOperationMode.NIGHT) == DPTBinary(False)

    def test_from_knx_binary_error(self):
        """Test from_knx function with invalid payload."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx, operation_mode=HVACOperationMode.COMFORT
        )
        with pytest.raises(CouldNotParseTelegram):
            remote_value.from_knx(DPTArray((0x9, 0xF)))

    def test_to_knx_heat_cool(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryHeatCool(
            xknx, controller_mode=HVACControllerMode.HEAT
        )
        assert remote_value.to_knx(HVACControllerMode.HEAT) == DPTBinary(True)
        assert remote_value.to_knx(HVACControllerMode.COOL) == DPTBinary(False)

    def test_to_knx_heat_cool_error(self):
        """Test to_knx function with wrong controller mode."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryHeatCool(
            xknx, controller_mode=HVACControllerMode.HEAT
        )
        with pytest.raises(ConversionError):
            remote_value.to_knx(HVACOperationMode.STANDBY)

    def test_from_knx_operation_mode(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueOperationMode(
            xknx, climate_mode_type=RemoteValueOperationMode.ClimateModeType.HVAC_MODE
        )
        assert remote_value.from_knx(DPTArray((0x02,))) == HVACOperationMode.STANDBY

    def test_from_knx_controller_mode(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueControllerMode(xknx)
        assert (
            remote_value.from_knx(DPTArray((0x02,)))
            == HVACControllerMode.MORNING_WARMUP
        )

    def test_from_knx_binary_heat_cool(self):
        """Test from_knx function with invalid payload."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryHeatCool(
            xknx, controller_mode=HVACControllerMode.HEAT
        )
        with pytest.raises(CouldNotParseTelegram):
            remote_value.from_knx(DPTArray((0x9, 0xF)))

    def test_from_knx_operation_mode_error(self):
        """Test from_knx function with invalid payload."""
        xknx = XKNX()
        with pytest.raises(ConversionError):
            RemoteValueOperationMode(xknx, climate_mode_type=None)

    def test_from_knx_binary(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx, operation_mode=HVACOperationMode.COMFORT
        )
        assert remote_value.from_knx(DPTBinary(True)) == HVACOperationMode.COMFORT
        assert remote_value.from_knx(DPTBinary(False)) is None

    def test_from_knx_heat_cool(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryHeatCool(
            xknx, controller_mode=HVACControllerMode.HEAT
        )
        assert remote_value.from_knx(DPTBinary(True)) == HVACControllerMode.HEAT
        assert remote_value.from_knx(DPTBinary(False)) == HVACControllerMode.COOL

    def test_from_knx_unsupported_operation_mode(self):
        """Test from_knx function with unsupported operation."""
        xknx = XKNX()
        with pytest.raises(ConversionError):
            RemoteValueBinaryHeatCool(xknx, controller_mode=HVACControllerMode.NODEM)

    def test_from_knx_unknown_operation_mode(self):
        """Test from_knx function with unsupported operation."""
        xknx = XKNX()
        with pytest.raises(ConversionError):
            RemoteValueBinaryHeatCool(xknx, controller_mode=None)

    def test_to_knx_error_operation_mode(self):
        """Test to_knx function with wrong parameter."""
        xknx = XKNX()
        remote_value = RemoteValueOperationMode(
            xknx, climate_mode_type=RemoteValueOperationMode.ClimateModeType.HVAC_MODE
        )
        with pytest.raises(ConversionError):
            remote_value.to_knx(256)
        with pytest.raises(ConversionError):
            remote_value.to_knx("256")
        with pytest.raises(ConversionError):
            remote_value.to_knx(HVACControllerMode.HEAT)

    def test_to_knx_error_controller_mode(self):
        """Test to_knx function with wrong parameter."""
        xknx = XKNX()
        remote_value = RemoteValueControllerMode(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(256)
        with pytest.raises(ConversionError):
            remote_value.to_knx("256")
        with pytest.raises(ConversionError):
            remote_value.to_knx(HVACOperationMode.NIGHT)

    def test_to_knx_error_binary(self):
        """Test to_knx function with wrong parameter."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx, operation_mode=HVACOperationMode.NIGHT
        )
        with pytest.raises(ConversionError):
            remote_value.to_knx(256)
        with pytest.raises(ConversionError):
            remote_value.to_knx(True)
        with pytest.raises(ConversionError):
            remote_value.to_knx(HVACControllerMode.HEAT)

    async def test_set_operation_mode(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueOperationMode(
            xknx,
            group_address=GroupAddress("1/2/3"),
            climate_mode_type=RemoteValueOperationMode.ClimateModeType.HVAC_MODE,
        )
        await remote_value.set(HVACOperationMode.NIGHT)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x03,))),
        )
        await remote_value.set(HVACOperationMode.FROST_PROTECTION)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x04,))),
        )

    async def test_set_controller_mode(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueControllerMode(
            xknx, group_address=GroupAddress("1/2/3")
        )
        await remote_value.set(HVACControllerMode.COOL)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x03,))),
        )
        await remote_value.set(HVACControllerMode.NIGHT_PURGE)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x04,))),
        )

    async def test_set_binary(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx,
            group_address=GroupAddress("1/2/3"),
            operation_mode=HVACOperationMode.STANDBY,
        )
        await remote_value.set(HVACOperationMode.STANDBY)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(True)),
        )
        await remote_value.set(HVACOperationMode.FROST_PROTECTION)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(False)),
        )

    async def test_process_operation_mode(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueOperationMode(
            xknx,
            group_address=GroupAddress("1/2/3"),
            climate_mode_type=RemoteValueOperationMode.ClimateModeType.HVAC_MODE,
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x00,))),
        )
        await remote_value.process(telegram)
        assert remote_value.value == HVACOperationMode.AUTO

    async def test_process_controller_mode(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueControllerMode(
            xknx, group_address=GroupAddress("1/2/3")
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x00,))),
        )
        await remote_value.process(telegram)
        assert remote_value.value == HVACControllerMode.AUTO

    async def test_process_binary(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx,
            group_address=GroupAddress("1/2/3"),
            operation_mode=HVACOperationMode.FROST_PROTECTION,
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(True)),
        )
        await remote_value.process(telegram)
        assert remote_value.value == HVACOperationMode.FROST_PROTECTION

    async def test_to_process_error_operation_mode(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueOperationMode(
            xknx,
            group_address=GroupAddress("1/2/3"),
            climate_mode_type=RemoteValueOperationMode.ClimateModeType.HVAC_MODE,
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65))),
        )
        assert await remote_value.process(telegram) is False

        assert remote_value.value is None

    async def test_to_process_error_binary_operation_mode(self):
        """Test processing invalid payload."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx,
            group_address="1/2/3",
            operation_mode=HVACOperationMode.COMFORT,
        )
        invalid_telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(
                DPTArray((1,)),
            ),
        )
        assert await remote_value.process(telegram=invalid_telegram) is False

    async def test_to_process_error_controller_mode(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueControllerMode(
            xknx, group_address=GroupAddress("1/2/3")
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65))),
        )
        assert await remote_value.process(telegram) is False

        assert remote_value.value is None

    async def test_to_process_error_heat_cool(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryHeatCool(
            xknx,
            group_address=GroupAddress("1/2/3"),
            controller_mode=HVACControllerMode.COOL,
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x01,))),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65))),
        )
        assert await remote_value.process(telegram) is False

        assert remote_value.value is None
