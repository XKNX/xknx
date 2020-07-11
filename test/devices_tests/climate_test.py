"""Unit test for Climate objects."""
import asyncio
import unittest
from unittest.mock import Mock

from xknx import XKNX
from xknx.devices import Climate, ClimateMode
from xknx.dpt import (
    DPT2ByteFloat, DPTArray, DPTBinary, DPTControllerStatus, DPTHVACContrMode,
    DPTHVACMode, DPTTemperature, DPTValue1Count, HVACOperationMode)
from xknx.exceptions import CouldNotParseTelegram, DeviceIllegalValue
from xknx.telegram import GroupAddress, Telegram, TelegramType

DPT_20102_MODES = [HVACOperationMode.AUTO, HVACOperationMode.COMFORT,
                   HVACOperationMode.STANDBY, HVACOperationMode.NIGHT,
                   HVACOperationMode.FROST_PROTECTION]


class TestClimate(unittest.TestCase):
    """Test class for Climate objects."""

    # pylint: disable=invalid-name,too-many-public-methods
    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # SUPPORTS TEMPERATURE / SETPOINT
    #
    def test_support_temperature(self):
        """Test supports_temperature flag."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3')

        self.assertTrue(climate.temperature.initialized)
        self.assertFalse(climate.target_temperature.initialized)

    def test_support_target_temperature(self):
        """Test supports_target__temperature flag."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature='1/2/3')

        self.assertFalse(climate.temperature.initialized)
        self.assertTrue(climate.target_temperature.initialized)

    def test_support_operation_mode(self):
        """Test supports_supports_operation_mode flag. One group address for all modes."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/4')
        self.assertTrue(climate_mode.supports_operation_mode)

    def test_support_operation_mode2(self):
        """Test supports_supports_operation_mode flag. Splitted group addresses for each mode."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode_protection='1/2/4')
        self.assertTrue(climate_mode.supports_operation_mode)

    #
    # TEST HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test if has_group_address function works."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3',
            group_address_setpoint_shift_state='1/2/4',
            group_address_on_off='1/2/11',
            group_address_on_off_state='1/2/12')

        self.assertTrue(climate.has_group_address(GroupAddress('1/2/1')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/2')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/4')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/11')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/12')))
        self.assertFalse(climate.has_group_address(GroupAddress('1/2/99')))

    #
    # TEST HAS GROUP ADDRESS
    #
    def test_has_group_address_mode(self):
        """Test if has_group_address function works."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            name=None,
            group_address_operation_mode='1/2/5',
            group_address_operation_mode_protection='1/2/6',
            group_address_operation_mode_night='1/2/7',
            group_address_operation_mode_comfort='1/2/8',
            group_address_controller_mode='1/2/9',
            group_address_controller_mode_state='1/2/10')

        climate = Climate(xknx, name='TestClimate', mode=climate_mode)

        self.assertTrue(climate.has_group_address(GroupAddress('1/2/5')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/6')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/7')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/8')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/9')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/10')))
        self.assertFalse(climate.has_group_address(GroupAddress('1/2/99')))

    #
    # STATE ADDRESSES
    #
    def test_state_addresses(self):
        """Test state_addresses of Climate and ClimateMode."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            name=None,
            group_address_operation_mode='1/2/5',
            group_address_operation_mode_state='1/2/13',
            group_address_operation_mode_protection='1/2/6',
            group_address_operation_mode_night='1/2/7',
            group_address_operation_mode_comfort='1/2/8',
            group_address_controller_mode='1/2/9',
            group_address_controller_mode_state='1/2/10')
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3',
            group_address_setpoint_shift_state='1/2/4',
            group_address_on_off='1/2/11',
            group_address_on_off_state='1/2/12',
            mode=climate_mode)
        self.assertEqual(
            climate.state_addresses(),
            [GroupAddress("1/2/1"),
             GroupAddress("1/2/4"),
             GroupAddress("1/2/12"),
             GroupAddress("1/2/13"),
             GroupAddress("1/2/10")])

    #
    # TEST CALLBACK
    #
    def test_process_callback(self):
        """Test if after_update_callback is called after update of Climate object was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3',
            group_address_setpoint_shift_state='1/2/4')

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        climate.register_device_updated_cb(async_after_update_callback)

        self.loop.run_until_complete(asyncio.Task(
            climate.target_temperature.set(23.00)))
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

        self.loop.run_until_complete(asyncio.Task(
            climate.set_setpoint_shift(-2)))
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

    def test_process_callback_mode(self):
        """Test if after_update_callback is called after update of Climate object was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/5')

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        climate_mode.register_device_updated_cb(async_after_update_callback)

        self.loop.run_until_complete(asyncio.Task(
            climate_mode.set_operation_mode(HVACOperationMode.COMFORT)))
        after_update_callback.assert_called_with(climate_mode)
        after_update_callback.reset_mock()

        self.loop.run_until_complete(asyncio.Task(
            climate_mode.set_operation_mode(HVACOperationMode.COMFORT)))
        after_update_callback.assert_not_called()
        after_update_callback.reset_mock()

        self.loop.run_until_complete(asyncio.Task(
            climate_mode.set_operation_mode(HVACOperationMode.FROST_PROTECTION)))
        after_update_callback.assert_called_with(climate_mode)
        after_update_callback.reset_mock()

    def test_process_callback_updated_via_telegram(self):
        """Test if after_update_callback is called after update of Climate object."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3')

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        climate.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(GroupAddress('1/2/1'), payload=DPTArray(DPTTemperature.to_knx(23)))
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

        telegram = Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPTTemperature.to_knx(23)))
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTArray(DPTValue1Count.to_knx(-4)))
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

    def test_climate_mode_process_callback_updated_via_telegram(self):
        """Test if after_update_callback is called after update of ClimateMode object."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimateMode',
            group_address_operation_mode='1/2/4')

        after_update_callback = Mock()

        climate = Climate(xknx, 'TestClimate', mode=climate_mode)

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        climate_mode.register_device_updated_cb(async_after_update_callback)

        # Note: the climate object processes the telegram, but the cb
        # is called with the climate_mode object.
        telegram = Telegram(GroupAddress('1/2/4'), payload=DPTArray(1))
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))
        after_update_callback.assert_called_with(climate_mode)
        after_update_callback.reset_mock()

    #
    # TEST SET OPERATION MODE
    #
    def test_set_operation_mode(self):
        """Test set_operation_mode."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/4')

        for operation_mode in DPT_20102_MODES:
            self.loop.run_until_complete(asyncio.Task(climate_mode.set_operation_mode(operation_mode)))
            self.assertEqual(xknx.telegrams.qsize(), 1)
            telegram = xknx.telegrams.get_nowait()
            self.assertEqual(
                telegram,
                Telegram(
                    GroupAddress('1/2/4'),
                    payload=DPTArray(DPTHVACMode.to_knx(operation_mode))))

    def test_set_controller_operation_mode(self):
        """Test set_operation_mode with DPT20.105 controller."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_controller_mode='1/2/4')

        for _, operation_mode in DPTHVACContrMode.SUPPORTED_MODES.items():
            self.loop.run_until_complete(asyncio.Task(climate_mode.set_operation_mode(operation_mode)))
            self.assertEqual(xknx.telegrams.qsize(), 1)
            telegram = xknx.telegrams.get_nowait()
            self.assertEqual(
                telegram,
                Telegram(
                    GroupAddress('1/2/4'),
                    payload=DPTArray(DPTHVACContrMode.to_knx(operation_mode))))

    def test_set_operation_mode_not_supported(self):
        """Test set_operation_mode but not supported."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate')
        with self.assertRaises(DeviceIllegalValue):
            self.loop.run_until_complete(asyncio.Task(climate_mode.set_operation_mode(HVACOperationMode.AUTO)))

    def test_set_operation_mode_with_controller_status(self):
        """Test set_operation_mode with controller status adddressedefined."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_controller_status='1/2/4')

        for operation_mode in DPT_20102_MODES:
            if operation_mode == HVACOperationMode.AUTO:
                continue
            self.loop.run_until_complete(asyncio.Task(climate_mode.set_operation_mode(operation_mode)))
            self.assertEqual(xknx.telegrams.qsize(), 1)
            telegram = xknx.telegrams.get_nowait()
            self.assertEqual(
                telegram,
                Telegram(
                    GroupAddress('1/2/4'),
                    payload=DPTArray(DPTControllerStatus.to_knx(operation_mode))))

    def test_set_operation_mode_with_separate_addresses(self):
        """Test set_operation_mode with combined and separated group adddresses defined."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/4',
            group_address_operation_mode_protection='1/2/5',
            group_address_operation_mode_night='1/2/6',
            group_address_operation_mode_comfort='1/2/7')

        self.loop.run_until_complete(asyncio.Task(climate_mode.set_operation_mode(HVACOperationMode.COMFORT)))
        self.assertEqual(xknx.telegrams.qsize(), 4)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/4'),
                payload=DPTArray(1)))
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/5'),
                payload=DPTBinary(0)))
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/6'),
                payload=DPTBinary(0)))
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/7'),
                payload=DPTBinary(1)))

    #
    # TEST initialized_for_setpoint_shift_calculations
    #
    def test_initialized_for_setpoint_shift_calculations(self):
        """Test initialized_for_setpoint_shift_calculations method."""
        xknx = XKNX(loop=self.loop)
        climate1 = Climate(
            xknx,
            'TestClimate')
        self.assertFalse(climate1.initialized_for_setpoint_shift_calculations)

        climate2 = Climate(
            xknx,
            'TestClimate',
            group_address_setpoint_shift='1/2/3')
        self.assertFalse(climate2.initialized_for_setpoint_shift_calculations)
        self.loop.run_until_complete(asyncio.Task(climate2.set_setpoint_shift(4)))
        self.assertFalse(climate2.initialized_for_setpoint_shift_calculations)

        climate3 = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3')
        self.loop.run_until_complete(asyncio.Task(climate3.set_setpoint_shift(4)))
        self.assertFalse(climate3.initialized_for_setpoint_shift_calculations)
        self.loop.run_until_complete(asyncio.Task(climate3.target_temperature.set(23.00)))
        self.assertTrue(climate3.initialized_for_setpoint_shift_calculations)

    #
    # TEST for unitialized target_temperature_min/target_temperature_max
    #
    def test_uninitalized_for_target_temperature_min_max(self):
        """Test if target_temperature_min/target_temperature_max return non if not initialized."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate')
        self.assertEqual(climate.target_temperature_min, None)
        self.assertEqual(climate.target_temperature_max, None)

    #
    # TEST for unitialized target_temperature_min/target_temperature_max but with overridden max and min temperature
    #
    def test_uninitalized_for_target_temperature_min_max_can_be_overridden(self):
        """Test if target_temperature_min/target_temperature_max return overridden value if specified."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            min_temp='7',
            max_temp='35')
        self.assertEqual(climate.target_temperature_min, '7')
        self.assertEqual(climate.target_temperature_max, '35')

    #
    # TEST for overriden max and min temp do have precedence over setpoint shift calculations
    #
    def test_overridden_max_min_temperature_has_priority(self):
        """Test that the overridden min and max temp always have precedence over setpoint shift calculations."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3',
            max_temp='42',
            min_temp='3')
        self.loop.run_until_complete(asyncio.Task(climate.set_setpoint_shift(4)))
        self.assertFalse(climate.initialized_for_setpoint_shift_calculations)
        self.loop.run_until_complete(asyncio.Task(climate.target_temperature.set(23.00)))
        self.assertTrue(climate.initialized_for_setpoint_shift_calculations)

        self.assertEqual(climate.target_temperature_min, '3')
        self.assertEqual(climate.target_temperature_max, '42')

    #
    # TEST TARGET TEMPERATURE
    #
    def test_target_temperature_up(self):
        """Test increase target temperature."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3')

        self.loop.run_until_complete(asyncio.Task(climate.set_setpoint_shift(3)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            # DEFAULT_SETPOINT_SHIFT_STEP is 0.5 -> payload = setpoint_shift * 2
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(6)))

        self.loop.run_until_complete(asyncio.Task(climate.target_temperature.set(23.00)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(23.00))))
        self.assertEqual(climate.base_temperature, 20)

        # First change
        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(24.00)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(8)))
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(24.00))))
        self.assertEqual(climate.target_temperature.value, 24.00)

        # Second change
        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(23.50)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(7)))
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(23.50))))
        self.assertEqual(climate.target_temperature.value, 23.50)

        # Test max target temperature
        # Base (20) - setpoint_shift_max (6)
        self.assertEqual(climate.target_temperature_max, 26.00)

        # third change - limit exceeded, setting to max
        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(26.50)))
        self.assertEqual(climate.target_temperature_max, 26.00)
        self.assertEqual(climate.setpoint_shift, 6)

    def test_target_temperature_down(self):
        """Test decrease target temperature."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3')

        self.loop.run_until_complete(asyncio.Task(climate.set_setpoint_shift(1)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            # DEFAULT_SETPOINT_SHIFT_STEP is 0.5 -> payload = setpoint_shift * 2
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(2)))

        self.loop.run_until_complete(asyncio.Task(climate.target_temperature.set(23.00)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(23.00))))
        self.assertEqual(climate.base_temperature, 22.0)

        # First change
        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(20.50)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(0xFD)))  # -3
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(20.50))))
        self.assertEqual(climate.target_temperature.value, 20.50)

        # Second change
        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(19.00)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(0xFA)))  # -6
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(19.00))))
        self.assertEqual(climate.target_temperature.value, 19.00)

        # Test min target temperature
        # Base (22) - setpoint_shift_min (6)
        self.assertEqual(climate.target_temperature_min, 16.00)

        # third change - limit exceeded, setting to min
        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(15.50)))
        self.assertEqual(climate.target_temperature_min, 16.00)
        self.assertEqual(climate.setpoint_shift, -6)

    def test_target_temperature_modified_step(self):
        """Test increase target temperature with modified step size."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3',
            setpoint_shift_step=0.1,
            setpoint_shift_max=10,
            setpoint_shift_min=-10)

        self.loop.run_until_complete(asyncio.Task(climate.set_setpoint_shift(3)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            # setpoint_shift_step is 0.1 -> payload = setpoint_shift * 10
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(30)))

        self.loop.run_until_complete(asyncio.Task(climate.target_temperature.set(23.00)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(23.00))))
        self.assertEqual(climate.base_temperature, 20.00)
        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(24.00)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(40)))
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(24.00))))
        self.assertEqual(climate.target_temperature.value, 24.00)

        # Test max/min target temperature
        self.assertEqual(climate.target_temperature_max, 30.00)
        self.assertEqual(climate.target_temperature_min, 10.00)

    #
    # TEST BASE TEMPERATURE
    #
    def test_base_temperature(self):
        """Test base temperature."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature_state='1/2/1',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3')

        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(21.00)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(21.00))))
        self.assertFalse(climate.initialized_for_setpoint_shift_calculations)
        self.assertEqual(climate.base_temperature, None)

        # setpoint_shift initialized after target_temperature (no temperature change)
        self.loop.run_until_complete(asyncio.Task(climate.set_setpoint_shift(1)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            # DEFAULT_SETPOINT_SHIFT_STEP is 0.5 -> payload = setpoint_shift * 2
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(2)))
        self.assertTrue(climate.initialized_for_setpoint_shift_calculations)
        self.assertEqual(climate.base_temperature, 20.00)

        # setpoint_shift changed after initialisation
        self.loop.run_until_complete(asyncio.Task(climate.set_setpoint_shift(2)))
        # setpoint_shift and target_temperature are sent to the bus
        self.assertEqual(xknx.telegrams.qsize(), 2)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            # DEFAULT_SETPOINT_SHIFT_STEP is 0.5 -> payload = setpoint_shift * 2
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(4)))
        self.assertTrue(climate.initialized_for_setpoint_shift_calculations)
        self.assertEqual(climate.base_temperature, 20.00)
        self.assertEqual(climate.target_temperature.value, 22)

    #
    # TEST TEMPERATURE STEP
    #
    def test_temperature_step(self):
        """Test base temperature step."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature_state='1/2/1',
            group_address_target_temperature='1/2/2')

        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(21.00)))
        # default temperature_step for non setpoint_shift
        self.assertEqual(climate.temperature_step, 0.1)

        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature_state='1/2/1',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3')
        # default temperature_step for setpoint_shift
        self.assertEqual(climate.temperature_step, 0.5)

        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature_state='1/2/1',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3',
            setpoint_shift_step=0.3)
        self.assertEqual(climate.temperature_step, 0.3)

    #
    # TEST SYNC
    #
    def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3')
        self.loop.run_until_complete(asyncio.Task(climate.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ))

    def test_sync_operation_mode(self):
        """Test sync function / sending group reads to KNX bus for operation mode."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/3',
            group_address_operation_mode_state='1/2/4')
        self.loop.run_until_complete(asyncio.Task(climate_mode.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(GroupAddress('1/2/4'), TelegramType.GROUP_READ))

    def test_sync_controller_status(self):
        """Test sync function / sending group reads to KNX bus for controller status."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/23',
            group_address_controller_status_state='1/2/24')
        self.loop.run_until_complete(asyncio.Task(climate_mode.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(GroupAddress('1/2/24'), TelegramType.GROUP_READ))

    def test_sync_controller_mode(self):
        """Test sync function / sending group reads to KNX bus for controller mode."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_controller_mode='1/2/13',
            group_address_controller_mode_state='1/2/14')
        self.loop.run_until_complete(asyncio.Task(climate_mode.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(GroupAddress('1/2/14'), TelegramType.GROUP_READ))

    def test_sync_operation_mode_state(self):
        """Test sync function / sending group reads to KNX bus for multiple mode addresses."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/3',
            group_address_operation_mode_state='1/2/5',
            group_address_controller_status='1/2/4',
            group_address_controller_status_state='1/2/6',
            group_address_controller_mode='1/2/13',
            group_address_controller_mode_state='1/2/14')
        self.loop.run_until_complete(asyncio.Task(climate_mode.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 3)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(GroupAddress('1/2/5'), TelegramType.GROUP_READ))
        telegram2 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram2,
            Telegram(GroupAddress('1/2/6'), TelegramType.GROUP_READ))
        telegram3 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram3,
            Telegram(GroupAddress('1/2/14'), TelegramType.GROUP_READ))

    #
    # TEST PROCESS
    #
    def test_process_temperature(self):
        """Test process / reading telegrams from telegram queue. Test if temperature is processed correctly."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3')

        telegram = Telegram(GroupAddress('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))
        self.assertEqual(climate.temperature.value, 21.34)

    def test_process_operation_mode(self):
        """Test process / reading telegrams from telegram queue. Test if setpoint is processed correctly."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/5',
            group_address_controller_status='1/2/3')
        for operation_mode in DPT_20102_MODES:
            telegram = Telegram(GroupAddress('1/2/5'))
            telegram.payload = DPTArray(DPTHVACMode.to_knx(operation_mode))
            self.loop.run_until_complete(asyncio.Task(climate_mode.process(telegram)))
            self.assertEqual(climate_mode.operation_mode, operation_mode)
        for operation_mode in DPT_20102_MODES:
            if operation_mode == HVACOperationMode.AUTO:
                continue
            telegram = Telegram(GroupAddress('1/2/3'))
            telegram.payload = DPTArray(DPTControllerStatus.to_knx(operation_mode))
            self.loop.run_until_complete(asyncio.Task(climate_mode.process(telegram)))
            self.assertEqual(climate_mode.operation_mode, operation_mode)

    def test_process_controller_mode(self):
        """Test process / reading telegrams from telegram queue. Test if DPT20.105 controller mode is set correctly."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_controller_mode='1/2/5')
        for _, operation_mode in DPTHVACContrMode.SUPPORTED_MODES.items():
            telegram = Telegram(GroupAddress('1/2/5'))
            telegram.payload = DPTArray(DPTHVACContrMode.to_knx(operation_mode))
            self.loop.run_until_complete(asyncio.Task(climate_mode.process(telegram)))
            self.assertEqual(climate_mode.operation_mode, operation_mode)

    def test_process_controller_status_wrong_payload(self):
        """Test process wrong telegram for controller status (wrong payload type)."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/5',
            group_address_controller_status='1/2/3')
        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTBinary(1))
        with self.assertRaises(CouldNotParseTelegram):
            self.loop.run_until_complete(asyncio.Task(climate_mode.process(telegram)))

    def test_process_controller_status_payload_invalid_length(self):
        """Test process wrong telegram for controller status (wrong payload length)."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/5',
            group_address_controller_status='1/2/3')
        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTArray((23, 24)))
        with self.assertRaises(CouldNotParseTelegram):
            self.loop.run_until_complete(asyncio.Task(climate_mode.process(telegram)))

    def test_process_operation_mode_wrong_payload(self):
        """Test process wrong telegram for operation mode (wrong payload type)."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/5',
            group_address_controller_status='1/2/3')
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTBinary(1))
        with self.assertRaises(CouldNotParseTelegram):
            self.loop.run_until_complete(asyncio.Task(climate_mode.process(telegram)))

    def test_process_operation_mode_payload_invalid_length(self):
        """Test process wrong telegram for operation mode (wrong payload length)."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/5',
            group_address_controller_status='1/2/3')
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray((23, 24)))
        with self.assertRaises(CouldNotParseTelegram):
            self.loop.run_until_complete(asyncio.Task(climate_mode.process(telegram)))

    def test_process_callback_temp(self):
        """Test process / reading telegrams from telegram queue. Test if callback is executed when receiving temperature."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3')

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        climate.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(GroupAddress('1/2/3'))
        telegram.payload = DPTArray(DPTTemperature().to_knx(21.34))
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))
        after_update_callback.assert_called_with(climate)

    #
    # SUPPORTED OPERATION MODES
    #
    def test_supported_operation_modes(self):
        """Test get_supported_operation_modes with combined group address."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/5')
        self.assertEqual(
            climate_mode.operation_modes,
            [HVACOperationMode.AUTO,
             HVACOperationMode.COMFORT,
             HVACOperationMode.STANDBY,
             HVACOperationMode.NIGHT,
             HVACOperationMode.FROST_PROTECTION])

    def test_supported_operation_modes_controller_status(self):
        """Test get_supported_operation_modes with combined group address."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_controller_status='1/2/5')
        self.assertEqual(
            climate_mode.operation_modes,
            [HVACOperationMode.COMFORT,
             HVACOperationMode.STANDBY,
             HVACOperationMode.NIGHT,
             HVACOperationMode.FROST_PROTECTION])

    def test_supported_operation_modes_no_mode(self):
        """Test get_supported_operation_modes no operation_modes supported."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate')
        self.assertEqual(
            climate_mode.operation_modes, [])

    def test_supported_operation_modes_with_separate_addresses(self):
        """Test get_supported_operation_modes with separated group addresses."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode_protection='1/2/5',
            group_address_operation_mode_night='1/2/6',
            group_address_operation_mode_comfort='1/2/7')
        self.assertEqual(
            climate_mode.operation_modes,
            [HVACOperationMode.COMFORT,
             HVACOperationMode.STANDBY,
             HVACOperationMode.NIGHT,
             HVACOperationMode.FROST_PROTECTION])

    def test_supported_operation_modes_only_night(self):
        """Test get_supported_operation_modes with only night mode supported."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode_night='1/2/7')
        self.assertEqual(
            climate_mode.operation_modes,
            [HVACOperationMode.STANDBY,
             HVACOperationMode.NIGHT])

    def test_custom_supported_operation_modes(self):
        """Test get_supported_operation_modes with custom mode."""
        modes = [HVACOperationMode.STANDBY, HVACOperationMode.NIGHT]
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/7',
            operation_modes=modes)
        self.assertEqual(
            climate_mode.operation_modes, modes)

    def test_custom_supported_operation_modes_as_str(self):
        """Test get_supported_operation_modes with custom mode as str list."""
        str_modes = ['Standby', 'Frost Protection']
        modes = [HVACOperationMode.STANDBY, HVACOperationMode.FROST_PROTECTION]
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/7',
            operation_modes=str_modes)
        self.assertEqual(
            climate_mode.operation_modes, modes)

    def test_process_power_status(self):
        """Test process / reading telegrams from telegram queue. Test if DPT20.105 controller mode is set correctly."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_on_off='1/2/2')
        telegram = Telegram(GroupAddress('1/2/2'))
        telegram.payload = DPTBinary(1)
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))
        self.assertEqual(climate.is_on, True)

        climate_inv = Climate(
            xknx,
            'TestClimate',
            group_address_on_off='1/2/2',
            on_off_invert=True)
        telegram = Telegram(GroupAddress('1/2/2'))
        telegram.payload = DPTBinary(1)
        self.loop.run_until_complete(asyncio.Task(climate_inv.process(telegram)))
        self.assertEqual(climate_inv.is_on, False)

    def test_power_on_off(self):
        """Test turn_on and turn_off functions."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_on_off='1/2/2')
        self.loop.run_until_complete(asyncio.Task(climate.turn_on()))
        self.assertEqual(climate.is_on, True)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTBinary(True)))
        self.loop.run_until_complete(asyncio.Task(climate.turn_off()))
        self.assertEqual(climate.is_on, False)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTBinary(False)))

        climate_inv = Climate(
            xknx,
            'TestClimate',
            group_address_on_off='1/2/2',
            on_off_invert=True)
        self.loop.run_until_complete(asyncio.Task(climate_inv.turn_on()))
        self.assertEqual(climate_inv.is_on, True)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTBinary(False)))
        self.loop.run_until_complete(asyncio.Task(climate_inv.turn_off()))
        self.assertEqual(climate_inv.is_on, False)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTBinary(True)))
