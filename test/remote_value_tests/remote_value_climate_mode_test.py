"""Unit test for RemoteValueClimateMode objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, HVACOperationMode
from xknx.dpt.dpt_hvac_mode import HVACControllerMode
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import (
    RemoteValueBinaryHeatCool,
    RemoteValueBinaryOperationMode,
    RemoteValueClimateMode,
)
from xknx.remote_value.remote_value_climate_mode import _RemoteValueBinaryClimateMode
from xknx.telegram import GroupAddress, Telegram


class TestRemoteValueDptValue1Ucount(unittest.TestCase):
    """Test class for RemoteValueDptValue1Ucount objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_to_knx_operation_mode(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueClimateMode(
            xknx, climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_MODE
        )
        self.assertEqual(
            remote_value.to_knx(HVACOperationMode.COMFORT), DPTArray((0x01,))
        )

    def test_to_knx_binary(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx, operation_mode=HVACOperationMode.COMFORT
        )
        self.assertEqual(
            remote_value.to_knx(HVACOperationMode.COMFORT), DPTBinary(True)
        )
        self.assertEqual(remote_value.to_knx(HVACOperationMode.NIGHT), DPTBinary(False))

    def test_from_knx_binary_error(self):
        """Test from_knx function with invalid payload."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx, operation_mode=HVACOperationMode.COMFORT
        )
        with self.assertRaises(CouldNotParseTelegram):
            remote_value.from_knx(DPTArray((0x9, 0xF)))

    def test_to_knx_heat_cool(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryHeatCool(
            xknx, controller_mode=HVACControllerMode.HEAT
        )
        self.assertEqual(remote_value.to_knx(HVACControllerMode.HEAT), DPTBinary(True))
        self.assertEqual(remote_value.to_knx(HVACControllerMode.COOL), DPTBinary(False))

    def test_to_knx_heat_cool_error(self):
        """Test to_knx function with wrong controller mode."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryHeatCool(
            xknx, controller_mode=HVACControllerMode.HEAT
        )
        with self.assertRaises(ConversionError):
            remote_value.to_knx(HVACOperationMode.STANDBY)

    def test_from_knx_operation_mode(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueClimateMode(
            xknx, climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_MODE
        )
        self.assertEqual(
            remote_value.from_knx(DPTArray((0x02,))), HVACOperationMode.STANDBY
        )

    def test_from_knx_binary_heat_cool(self):
        """Test from_knx function with invalid payload."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryHeatCool(
            xknx, controller_mode=HVACControllerMode.HEAT
        )
        with self.assertRaises(CouldNotParseTelegram):
            remote_value.from_knx(DPTArray((0x9, 0xF)))

    def test_from_knx_operation_mode_error(self):
        """Test from_knx function with invalid payload."""
        xknx = XKNX()
        with self.assertRaises(ConversionError):
            RemoteValueClimateMode(xknx, climate_mode_type=None)

    def test_from_knx_binary(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx, operation_mode=HVACOperationMode.COMFORT
        )
        self.assertEqual(
            remote_value.from_knx(DPTBinary(True)), HVACOperationMode.COMFORT
        )
        self.assertEqual(remote_value.from_knx(DPTBinary(False)), None)

    def test_from_knx_heat_cool(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryHeatCool(
            xknx, controller_mode=HVACControllerMode.HEAT
        )
        self.assertEqual(
            remote_value.from_knx(DPTBinary(True)), HVACControllerMode.HEAT
        )
        self.assertEqual(
            remote_value.from_knx(DPTBinary(False)), HVACControllerMode.COOL
        )

    def test_from_knx_unsupported_operation_mode(self):
        """Test from_knx function with unsupported operation."""
        xknx = XKNX()
        with self.assertRaises(ConversionError):
            RemoteValueBinaryHeatCool(xknx, controller_mode=HVACControllerMode.NODEM)

    def test_from_knx_unknown_operation_mode(self):
        """Test from_knx function with unsupported operation."""
        xknx = XKNX()
        with self.assertRaises(ConversionError):
            RemoteValueBinaryHeatCool(xknx, controller_mode=None)

    def test_supported_operation_modes_not_implemented(self):
        """Test from_knx function with unsupported operation."""
        xknx = XKNX()
        with self.assertRaises(NotImplementedError):
            _RemoteValueBinaryClimateMode.supported_operation_modes()

    def test_to_knx_error_operation_mode(self):
        """Test to_knx function with wrong parameter."""
        xknx = XKNX()
        remote_value = RemoteValueClimateMode(
            xknx, climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_MODE
        )
        with self.assertRaises(ConversionError):
            remote_value.to_knx(256)
        with self.assertRaises(ConversionError):
            remote_value.to_knx("256")

    def test_to_knx_error_binary(self):
        """Test to_knx function with wrong parameter."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx, operation_mode=HVACOperationMode.NIGHT
        )
        with self.assertRaises(ConversionError):
            remote_value.to_knx(256)
        with self.assertRaises(ConversionError):
            remote_value.to_knx(True)

    def test_set_operation_mode(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueClimateMode(
            xknx,
            group_address=GroupAddress("1/2/3"),
            climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_MODE,
        )
        self.loop.run_until_complete(remote_value.set(HVACOperationMode.NIGHT))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram, Telegram(GroupAddress("1/2/3"), payload=DPTArray((0x03,)))
        )
        self.loop.run_until_complete(
            remote_value.set(HVACOperationMode.FROST_PROTECTION)
        )
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram, Telegram(GroupAddress("1/2/3"), payload=DPTArray((0x04,)))
        )

    def test_set_binary(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx,
            group_address=GroupAddress("1/2/3"),
            operation_mode=HVACOperationMode.STANDBY,
        )
        self.loop.run_until_complete(remote_value.set(HVACOperationMode.STANDBY))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram, Telegram(GroupAddress("1/2/3"), payload=DPTBinary(True))
        )
        self.loop.run_until_complete(
            remote_value.set(HVACOperationMode.FROST_PROTECTION)
        )
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram, Telegram(GroupAddress("1/2/3"), payload=DPTBinary(False))
        )

    def test_process_operation_mode(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueClimateMode(
            xknx,
            group_address=GroupAddress("1/2/3"),
            climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_MODE,
        )
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"), payload=DPTArray((0x00,))
        )
        self.loop.run_until_complete(remote_value.process(telegram))
        self.assertEqual(remote_value.value, HVACOperationMode.AUTO)

    def test_process_binary(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryOperationMode(
            xknx,
            group_address=GroupAddress("1/2/3"),
            operation_mode=HVACOperationMode.FROST_PROTECTION,
        )
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"), payload=DPTBinary(True)
        )
        self.loop.run_until_complete(remote_value.process(telegram))
        self.assertEqual(remote_value.value, HVACOperationMode.FROST_PROTECTION)

    def test_to_process_error_operation_mode(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueClimateMode(
            xknx,
            group_address=GroupAddress("1/2/3"),
            climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_MODE,
        )
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"), payload=DPTBinary(1)
            )
            self.loop.run_until_complete(remote_value.process(telegram))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray(
                    (
                        0x64,
                        0x65,
                    )
                ),
            )
            self.loop.run_until_complete(remote_value.process(telegram))

    def test_to_process_error_heat_cool(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueBinaryHeatCool(
            xknx,
            group_address=GroupAddress("1/2/3"),
            controller_mode=HVACControllerMode.COOL,
        )
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"), payload=DPTArray((0x01,))
            )
            self.loop.run_until_complete(remote_value.process(telegram))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray(
                    (
                        0x64,
                        0x65,
                    )
                ),
            )
            self.loop.run_until_complete(remote_value.process(telegram))
