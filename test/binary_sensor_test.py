import unittest
from unittest.mock import Mock
import asyncio
from xknx import XKNX, BinarySensor, Action, Switch, BinarySensorState
from xknx.knx import Telegram, DPTBinary

class TestBinarySensor(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX(loop=self.loop)
        binaryinput = BinarySensor(xknx, 'TestInput', '1/2/3')

        self.assertEqual(binaryinput.state, BinarySensorState.OFF)

        telegram_on = Telegram()
        telegram_on.payload = DPTBinary(1)
        binaryinput.process(telegram_on)

        self.assertEqual(binaryinput.state, BinarySensorState.ON)

        telegram_off = Telegram()
        telegram_off.payload = DPTBinary(0)
        binaryinput.process(telegram_off)

        self.assertEqual(binaryinput.state, BinarySensorState.OFF)


    def test_process_significant_bit(self):
        xknx = XKNX(loop=self.loop)
        binaryinput = BinarySensor(xknx, 'TestInput', '1/2/3', significant_bit=3)

        self.assertEqual(binaryinput.state, BinarySensorState.OFF)

        # Wrong significant bit: 0000 1011 = 11
        telegram_on = Telegram()
        telegram_on.payload = DPTBinary(11)
        binaryinput.process(telegram_on)
        self.assertEqual(binaryinput.state, BinarySensorState.OFF)

        # Correct significant bit: 0000 1101 = 13
        telegram_on = Telegram()
        telegram_on.payload = DPTBinary(13)
        binaryinput.process(telegram_on)
        self.assertEqual(binaryinput.state, BinarySensorState.ON)

        # Resetting, significant bit: 0000 0011 = 3
        telegram_off = Telegram()
        telegram_off.payload = DPTBinary(3)
        binaryinput.process(telegram_off)
        self.assertEqual(binaryinput.state, BinarySensorState.OFF)


    def test_process_action(self):
        xknx = XKNX(loop=self.loop)
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        xknx.devices.add(switch)

        binary_sensor = BinarySensor(xknx, 'TestInput', group_address='1/2/3')
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
        binary_sensor.process(telegram_on)

        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinarySensorState.ON)
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            True)

        telegram_off = Telegram()
        telegram_off.payload = DPTBinary(0)
        binary_sensor.process(telegram_off)

        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinarySensorState.OFF)
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            False)

    #
    # TEST SWITCHED ON
    #
    def test_is_on(self):
        xknx = XKNX(loop=self.loop)
        binaryinput = BinarySensor(xknx, 'TestInput', '1/2/3')
        binaryinput.set_internal_state(BinarySensorState.ON)
        self.assertTrue(binaryinput.is_on())
        self.assertFalse(binaryinput.is_off())

    #
    # TEST SWITCHED OFF
    #
    def test_is_off(self):
        xknx = XKNX(loop=self.loop)
        binaryinput = BinarySensor(xknx, 'TestInput', '1/2/3')
        binaryinput.set_internal_state(BinarySensorState.OFF)
        self.assertFalse(binaryinput.is_on())
        self.assertTrue(binaryinput.is_off())


    #
    # TEST PROCESS CALLBACK
    #
    def test_process_callback(self):
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        switch = BinarySensor(xknx, 'TestInput', group_address='1/2/3')

        after_update_callback = Mock()
        switch.register_device_updated_cb(after_update_callback)

        telegram = Telegram()
        telegram.payload = DPTBinary(1)
        switch.process(telegram)

        after_update_callback.assert_called_with(switch)


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestBinarySensor)
unittest.TextTestRunner(verbosity=2).run(SUITE)
