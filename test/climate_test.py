"""Unit test for Climate objects."""
import asyncio
import unittest
from unittest.mock import Mock

from xknx import XKNX
from xknx.devices import Climate
from xknx.exceptions import DeviceIllegalValue
from xknx.knx import (GroupAddress, DPTArray, DPTBinary, DPTControllerStatus,
                      DPT2ByteFloat, DPTHVACMode, DPTTemperature, DPTValue1Count,
                      HVACOperationMode, Telegram, TelegramType)


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
        self.assertFalse(climate.supports_operation_mode)

    def test_support_target_temperature(self):
        """Test supports_target__temperature flag."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature='1/2/3')

        self.assertFalse(climate.temperature.initialized)
        self.assertTrue(climate.target_temperature.initialized)
        self.assertFalse(climate.supports_operation_mode)

    def test_support_operation_mode(self):
        """Test supports_supports_operation_mode flag. One group address for all modes."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/4')

        self.assertFalse(climate.temperature.initialized)
        self.assertFalse(climate.target_temperature.initialized)
        self.assertTrue(climate.supports_operation_mode)

    def test_support_operation_mode2(self):
        """Test supports_supports_operation_mode flag. Splitted group addresses for each mode."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_operation_mode_protection='1/2/4')

        self.assertFalse(climate.temperature.initialized)
        self.assertFalse(climate.target_temperature.initialized)
        self.assertTrue(climate.supports_operation_mode)

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
            group_address_operation_mode='1/2/5',
            group_address_operation_mode_protection='1/2/6',
            group_address_operation_mode_night='1/2/7',
            group_address_operation_mode_comfort='1/2/8')

        self.assertTrue(climate.has_group_address(GroupAddress('1/2/1')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/2')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/4')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/5')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/6')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/7')))
        self.assertTrue(climate.has_group_address(GroupAddress('1/2/8')))
        self.assertFalse(climate.has_group_address(GroupAddress('1/2/9')))

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
            group_address_setpoint_shift_state='1/2/4',
            group_address_operation_mode='1/2/5')

        after_update_callback = Mock()

        @asyncio.coroutine
        def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        climate.register_device_updated_cb(async_after_update_callback)

        self.loop.run_until_complete(asyncio.Task(
            climate.set_operation_mode(HVACOperationMode.COMFORT)))
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

        self.loop.run_until_complete(asyncio.Task(
            climate.set_operation_mode(HVACOperationMode.COMFORT)))
        after_update_callback.assert_not_called()
        after_update_callback.reset_mock()

        self.loop.run_until_complete(asyncio.Task(
            climate.set_operation_mode(HVACOperationMode.FROST_PROTECTION)))
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

        self.loop.run_until_complete(asyncio.Task(
            climate.target_temperature.set(23.00)))
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

        self.loop.run_until_complete(asyncio.Task(
            climate.setpoint_shift.set(-2)))
        after_update_callback.assert_called_with(climate)
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
            group_address_setpoint_shift='1/2/3',
            group_address_operation_mode='1/2/4')

        after_update_callback = Mock()

        @asyncio.coroutine
        def async_after_update_callback(device):
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

        telegram = Telegram(GroupAddress('1/2/4'), payload=DPTArray(1))
        self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))
        after_update_callback.assert_called_with(climate)
        after_update_callback.reset_mock()

    #
    # TEST SET OPERATION MODE
    #
    def test_set_operation_mode(self):
        """Test set_operation_mode."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1',
            group_address_operation_mode='1/2/4')

        for operation_mode in HVACOperationMode:
            self.loop.run_until_complete(asyncio.Task(climate.set_operation_mode(operation_mode)))
            self.assertEqual(xknx.telegrams.qsize(), 1)
            telegram = xknx.telegrams.get_nowait()
            self.assertEqual(
                telegram,
                Telegram(
                    GroupAddress('1/2/4'),
                    payload=DPTArray(DPTHVACMode.to_knx(operation_mode))))

    def test_set_operation_mode_not_supported(self):
        """Test set_operation_mode but not supported."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1')
        with self.assertRaises(DeviceIllegalValue):
            self.loop.run_until_complete(asyncio.Task(climate.set_operation_mode(HVACOperationMode.AUTO)))

    def test_set_operation_mode_with_controller_status(self):
        """Test set_operation_mode with controller status adddressedefined."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1',
            group_address_controller_status='1/2/4')

        for operation_mode in HVACOperationMode:
            if operation_mode == HVACOperationMode.AUTO:
                continue
            self.loop.run_until_complete(asyncio.Task(climate.set_operation_mode(operation_mode)))
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
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1',
            group_address_target_temperature='1/2/2',
            group_address_operation_mode='1/2/4',
            group_address_operation_mode_protection='1/2/5',
            group_address_operation_mode_night='1/2/6',
            group_address_operation_mode_comfort='1/2/7')

        self.loop.run_until_complete(asyncio.Task(climate.set_operation_mode(HVACOperationMode.COMFORT)))
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
        self.loop.run_until_complete(asyncio.Task(climate2.setpoint_shift.set(4)))
        self.assertFalse(climate2.initialized_for_setpoint_shift_calculations)

        climate3 = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3')
        self.loop.run_until_complete(asyncio.Task(climate3.setpoint_shift.set(4)))
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

        self.loop.run_until_complete(asyncio.Task(climate.setpoint_shift.set(4)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(4)))

        self.loop.run_until_complete(asyncio.Task(climate.target_temperature.set(23.00)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(23.00))))

        # First change
        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(24.00)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(6)))
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(24.00))))
        self.assertEqual(climate.target_temperature.value, 24.00)

        # Second change
        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(23.50)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(5)))
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(23.50))))
        self.assertEqual(climate.target_temperature.value, 23.50)

        # Test max target temperature
        self.assertEqual(climate.target_temperature_max, 24.00)

        # third change - limit exceeded, setting to max
        with self.assertRaises(DeviceIllegalValue):
            self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(24.50)))

    def test_target_temperature_down(self):
        """Test decrease target temperature."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3')

        self.loop.run_until_complete(asyncio.Task(climate.setpoint_shift.set(1)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(1)))

        self.loop.run_until_complete(asyncio.Task(climate.target_temperature.set(23.00)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(23.00))))

        # First change
        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(21.00)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(0xFD)))  # -3
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(21.00))))
        self.assertEqual(climate.target_temperature.value, 21.00)

        # Second change
        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(19.50)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(0xFA)))  # -3
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(19.50))))
        self.assertEqual(climate.target_temperature.value, 19.50)

        # Test min target temperature
        self.assertEqual(climate.target_temperature_min, 19.50)

        # third change - limit exceeded, setting to max
        with self.assertRaises(DeviceIllegalValue):
            self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(19.00)))

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
            setpoint_shift_max=20,
            setpoint_shift_min=-20)

        self.loop.run_until_complete(asyncio.Task(climate.setpoint_shift.set(10)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(10)))

        self.loop.run_until_complete(asyncio.Task(climate.target_temperature.set(23.00)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(23.00))))

        self.loop.run_until_complete(asyncio.Task(climate.set_target_temperature(24.00)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/3'), payload=DPTArray(20)))
        self.assertEqual(
            xknx.telegrams.get_nowait(),
            Telegram(GroupAddress('1/2/2'), payload=DPTArray(DPT2ByteFloat().to_knx(24.00))))
        self.assertEqual(climate.target_temperature.value, 24.00)

        # Test max/min target temperature
        self.assertEqual(climate.target_temperature_max, 24.00)
        self.assertEqual(climate.target_temperature_min, 20.00)

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
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/3',
            group_address_controller_status='1/2/4')
        self.loop.run_until_complete(asyncio.Task(climate.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ))
        telegram2 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram2,
            Telegram(GroupAddress('1/2/4'), TelegramType.GROUP_READ))

    def test_sync_operation_mode_state(self):
        """Test sync function / sending group reads to KNX bus for operation mode with explicit state addresses."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/3',
            group_address_operation_mode_state='1/2/5',
            group_address_controller_status='1/2/4',
            group_address_controller_status_state='1/2/6')
        self.loop.run_until_complete(asyncio.Task(climate.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(GroupAddress('1/2/5'), TelegramType.GROUP_READ))
        telegram2 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram2,
            Telegram(GroupAddress('1/2/6'), TelegramType.GROUP_READ))

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
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_operation_mode='1/2/5',
            group_address_controller_status='1/2/3')
        for operation_mode in HVACOperationMode:
            telegram = Telegram(GroupAddress('1/2/5'))
            telegram.payload = DPTArray(DPTHVACMode.to_knx(operation_mode))
            self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))
            self.assertEqual(climate.operation_mode, operation_mode)
        for operation_mode in HVACOperationMode:
            if operation_mode == HVACOperationMode.AUTO:
                continue
            telegram = Telegram(GroupAddress('1/2/3'))
            telegram.payload = DPTArray(DPTControllerStatus.to_knx(operation_mode))
            self.loop.run_until_complete(asyncio.Task(climate.process(telegram)))
            self.assertEqual(climate.operation_mode, operation_mode)

    def test_process_callback_temp(self):
        """Test process / reading telegrams from telegram queue. Test if callback is executed when receiving temperature."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/3')

        after_update_callback = Mock()

        @asyncio.coroutine
        def async_after_update_callback(device):
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
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1',
            group_address_operation_mode='1/2/5')
        self.assertEqual(
            climate.get_supported_operation_modes(),
            [HVACOperationMode.AUTO,
             HVACOperationMode.COMFORT,
             HVACOperationMode.STANDBY,
             HVACOperationMode.NIGHT,
             HVACOperationMode.FROST_PROTECTION])

    def test_supported_operation_modes_controller_status(self):
        """Test get_supported_operation_modes with combined group address."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1',
            group_address_controller_status='1/2/5')
        self.assertEqual(
            climate.get_supported_operation_modes(),
            [HVACOperationMode.COMFORT,
             HVACOperationMode.STANDBY,
             HVACOperationMode.NIGHT,
             HVACOperationMode.FROST_PROTECTION])

    def test_supported_operation_modes_no_mode(self):
        """Test get_supported_operation_modes no operation_modes supported."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1')
        self.assertEqual(
            climate.get_supported_operation_modes(), [])

    def test_supported_operation_modes_with_separate_addresses(self):
        """Test get_supported_operation_modes with separated group addresses."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1',
            group_address_operation_mode_protection='1/2/5',
            group_address_operation_mode_night='1/2/6',
            group_address_operation_mode_comfort='1/2/7')
        self.assertEqual(
            climate.get_supported_operation_modes(),
            [HVACOperationMode.COMFORT,
             HVACOperationMode.STANDBY,
             HVACOperationMode.NIGHT,
             HVACOperationMode.FROST_PROTECTION])

    def test_supported_operation_modes_only_night(self):
        """Test get_supported_operation_modes with only night mode supported."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='1/2/1',
            group_address_operation_mode_night='1/2/7')
        self.assertEqual(
            climate.get_supported_operation_modes(),
            [HVACOperationMode.STANDBY,
             HVACOperationMode.NIGHT])
