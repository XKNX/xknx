import unittest
from unittest.mock import Mock
import asyncio
from xknx import XKNX, Switch, Action, Outlet, BinaryInputState
from xknx.knx import Telegram, DPTBinary

class TestBinaryInput(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()


    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX(loop=self.loop, start=False)
        outlet = Outlet(xknx, 'TestOutlet', group_address='1/2/3')
        xknx.devices.add(outlet)

        switch = Switch(xknx, 'TestInput', group_address='1/2/3')
        action_on = Action(
            xknx,
            hook='on',
            target='TestOutlet',
            method='on')
        switch.actions.append(action_on)
        action_off = Action(
            xknx,
            hook='off',
            target='TestOutlet',
            method='off')
        switch.actions.append(action_off)
        xknx.devices.add(switch)

        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinaryInputState.OFF)
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            False)

        telegram_on = Telegram()
        telegram_on.payload = DPTBinary(1)
        switch.process(telegram_on)

        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinaryInputState.ON)
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            True)

        telegram_off = Telegram()
        telegram_off.payload = DPTBinary(0)
        switch.process(telegram_off)

        self.assertEqual(
            xknx.devices['TestInput'].state,
            BinaryInputState.OFF)
        self.assertEqual(
            xknx.devices['TestOutlet'].state,
            False)


    def test_process_callback(self):
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop, start=False)
        switch = Switch(xknx, 'TestInput', group_address='1/2/3')

        after_update_callback = Mock()
        switch.after_update_callback = after_update_callback

        telegram = Telegram()
        telegram.payload = DPTBinary(1)
        switch.process(telegram)

        after_update_callback.assert_called_with(switch)


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestBinaryInput)
unittest.TextTestRunner(verbosity=2).run(SUITE)
