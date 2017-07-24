import unittest
import asyncio
from xknx import XKNX, Switch, SwitchState
from xknx.knx import Telegram, DPTBinary

class TestSwitch(unittest.TestCase):

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
        binaryinput = Switch(xknx, 'TestInput', '1/2/3')

        self.assertEqual(binaryinput.state, SwitchState.OFF)

        telegram_on = Telegram()
        telegram_on.payload = DPTBinary(1)
        binaryinput.process(telegram_on)

        self.assertEqual(binaryinput.state, SwitchState.ON)

        telegram_off = Telegram()
        telegram_off.payload = DPTBinary(0)
        binaryinput.process(telegram_off)

        self.assertEqual(binaryinput.state, SwitchState.OFF)

    #
    # TEST SWITCHED ON
    #
    def test_is_on(self):
        xknx = XKNX(loop=self.loop)
        binaryinput = Switch(xknx, 'TestInput', '1/2/3')
        binaryinput.set_internal_state(SwitchState.ON)
        self.assertTrue(binaryinput.is_on())
        self.assertFalse(binaryinput.is_off())

    #
    # TEST SWITCHED OFF
    #
    def test_is_off(self):
        xknx = XKNX(loop=self.loop)
        binaryinput = Switch(xknx, 'TestInput', '1/2/3')
        binaryinput.set_internal_state(SwitchState.OFF)
        self.assertFalse(binaryinput.is_on())
        self.assertTrue(binaryinput.is_off())


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestSwitch)
unittest.TextTestRunner(verbosity=2).run(SUITE)
