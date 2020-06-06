"""Unit test for BinarySensor objects."""
import anyio
from unittest.mock import Mock, patch
import pytest

from xknx import XKNX
from xknx.devices import Action, BinarySensor, BinarySensorState, Switch
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram

from xknx._test import Testcase

class TestBinarySensor(Testcase):
    """Test class for BinarySensor objects."""

    @pytest.mark.anyio
    async def test_initialization_wrong_significant_bit(self):
        """Test initialization with wrong significant_bit parameter."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        with self.assertRaises(TypeError):
            BinarySensor(xknx, 'TestInput', '1/2/3', significant_bit="1")

    #
    # TEST PROCESS
    #
    @pytest.mark.anyio
    async def test_process(self):
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, 'TestInput', '1/2/3')

        self.assertEqual(binaryinput.state, BinarySensorState.OFF)

        telegram_on = Telegram()
        telegram_on.payload = DPTBinary(1)
        await binaryinput.process(telegram_on)

        self.assertEqual(binaryinput.state, BinarySensorState.ON)

        telegram_off = Telegram()
        telegram_off.payload = DPTBinary(0)
        await binaryinput.process(telegram_off)
        self.assertEqual(binaryinput.state, BinarySensorState.OFF)

    @pytest.mark.anyio
    async def test_process_reset_after(self):
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, 'TestInput', '1/2/3', reset_after=0.01)
        telegram_on = Telegram(payload=DPTBinary(1))
        await binaryinput.process(telegram_on)
        self.assertEqual(binaryinput.state, BinarySensorState.OFF)

    @pytest.mark.anyio
    async def test_process_significant_bit(self):
        """Test process / reading telegrams from telegram queue with specific significant bit set."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, 'TestInput', '1/2/3', significant_bit=3)

        self.assertEqual(binaryinput.state, BinarySensorState.OFF)

        # Wrong significant bit: 0000 1011 = 11
        telegram_on = Telegram()
        telegram_on.payload = DPTBinary(11)
        await binaryinput.process(telegram_on)
        self.assertEqual(binaryinput.state, BinarySensorState.OFF)

        # Correct significant bit: 0000 1101 = 13
        telegram_on = Telegram()
        telegram_on.payload = DPTBinary(13)
        await binaryinput.process(telegram_on)
        self.assertEqual(binaryinput.state, BinarySensorState.ON)

        # Resetting, significant bit: 0000 0011 = 3
        telegram_off = Telegram()
        telegram_off.payload = DPTBinary(3)
        await binaryinput.process(telegram_off)
        self.assertEqual(binaryinput.state, BinarySensorState.OFF)

    @pytest.mark.anyio
    async def test_process_action(self):
        """Test process / reading telegrams from telegram queue. Test if action is executed."""
        xknx = XKNX()
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        xknx.devices.add(switch)

        binary_sensor = BinarySensor(xknx, 'TestInput', group_address_state='1/2/3')
        action_on = Action(
            xknx,
            hook='on',
            target='TestOutlet',
            method='on')
        binary_sensor.actions.append(action_on)
        action_off = Action(
            xknx,
            hook='off',
            target='TestOutlet',
            method='off')
        binary_sensor.actions.append(action_off)
        xknx.devices.add(binary_sensor)

        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinarySensorState.OFF)
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            False)

        telegram_on = Telegram()
        telegram_on.payload = DPTBinary(1)
        await binary_sensor.process(telegram_on)

        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinarySensorState.ON)
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            True)

        telegram_off = Telegram()
        telegram_off.payload = DPTBinary(0)
        await binary_sensor.process(telegram_off)

        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinarySensorState.OFF)
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            False)

    @pytest.mark.anyio
    async def test_process_action_ignore_internal_state(self):
        """Test process / reading telegrams from telegram queue. Test if action is executed."""
        xknx = XKNX()
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        xknx.devices.add(switch)

        binary_sensor = BinarySensor(xknx, 'TestInput', group_address_state='1/2/5', ignore_internal_state=True)
        action_on = Action(
            xknx,
            hook='on',
            target='TestOutlet',
            method='on')
        binary_sensor.actions.append(action_on)
        xknx.devices.add(binary_sensor)

        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinarySensorState.OFF)
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            False)

        telegram_on = Telegram()
        telegram_on.payload = DPTBinary(1)
        await binary_sensor.process(telegram_on)

        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinarySensorState.ON)
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            True)

        await switch.set_off()
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            False)
        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinarySensorState.ON)

        await anyio.sleep(1)
        await binary_sensor.process(telegram_on)

        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinarySensorState.ON)
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            True)

    @pytest.mark.anyio
    async def test_process_wrong_payload(self):
        """Test process wrong telegram (wrong payload type)."""
        xknx = XKNX()
        binary_sensor = BinarySensor(xknx, 'Warning', group_address_state='1/2/3')
        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTArray((0x1, 0x2, 0x3)))
        with self.assertRaises(CouldNotParseTelegram):
            await binary_sensor.process(telegram)

    #
    # TEST SWITCHED ON
    #
    @pytest.mark.anyio
    async def test_is_on(self):
        """Test is_on() and is_off() of a BinarySensor with state 'on'."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, 'TestInput', '1/2/3')
        # pylint: disable=protected-access
        await binaryinput._set_internal_state(BinarySensorState.ON)
        self.assertTrue(binaryinput.is_on())
        self.assertFalse(binaryinput.is_off())

    #
    # TEST SWITCHED OFF
    #
    @pytest.mark.anyio
    async def test_is_off(self):
        """Test is_on() and is_off() of a BinarySensor with state 'off'."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, 'TestInput', '1/2/3')
        # pylint: disable=protected-access
        await binaryinput._set_internal_state(BinarySensorState.OFF)
        self.assertFalse(binaryinput.is_on())
        self.assertTrue(binaryinput.is_off())

    #
    # TEST PROCESS CALLBACK
    #
    @pytest.mark.anyio
    async def test_process_callback(self):
        """Test after_update_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()
        switch = BinarySensor(xknx, 'TestInput', group_address_state='1/2/3')

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        switch.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram()
        telegram.payload = DPTBinary(1)
        await switch.process(telegram)
        after_update_callback.assert_called_with(switch)

    #
    # TEST COUNTER
    #
    @pytest.mark.anyio
    async def test_counter(self):
        """Test counter functionality."""
        xknx = XKNX()
        switch = BinarySensor(xknx, 'TestInput', group_address_state='1/2/3')
        with patch('time.time') as mock_time:
            mock_time.return_value = 1517000000.0
            self.assertEqual(switch.bump_and_get_counter(BinarySensorState.ON), 1)

            mock_time.return_value = 1517000000.1
            self.assertEqual(switch.bump_and_get_counter(BinarySensorState.ON), 2)

            mock_time.return_value = 1517000000.2
            self.assertEqual(switch.bump_and_get_counter(BinarySensorState.OFF), 1)

            mock_time.return_value = 1517000000.3
            self.assertEqual(switch.bump_and_get_counter(BinarySensorState.ON), 3)

            mock_time.return_value = 1517000000.4
            self.assertEqual(switch.bump_and_get_counter(BinarySensorState.OFF), 2)

            mock_time.return_value = 1517000002.0  # TIME OUT ...
            self.assertEqual(switch.bump_and_get_counter(BinarySensorState.ON), 1)

            mock_time.return_value = 1517000004.1  # TIME OUT ...
            self.assertEqual(switch.bump_and_get_counter(BinarySensorState.OFF), 1)

    #
    # STATE ADDRESSES
    #
    @pytest.mark.anyio
    async def test_state_addresses(self):
        """Test binary sensor returns state address as list."""
        xknx = XKNX()
        binary_sensor = BinarySensor(
            xknx,
            'TestInput',
            group_address_state='1/2/4')
        self.assertEqual(binary_sensor.state_addresses(), [GroupAddress('1/2/4')])

        binary_sensor2 = BinarySensor(
            xknx,
            'TestInput')
        self.assertEqual(binary_sensor2.state_addresses(), [])

        binary_sensor_passive = BinarySensor(
            xknx,
            'TestInput',
            group_address_state='1/2/5',
            sync_state=False)
        self.assertEqual(binary_sensor_passive.state_addresses(), [])
