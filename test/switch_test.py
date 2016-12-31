import unittest

from xknx import XKNX,Switch,Action,Outlet,Telegram,DPT_Binary,BinaryInputState

class TestBinaryInput(unittest.TestCase):

    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX()
        outlet = Outlet(xknx, 'TestOutlet', {'group_address':'1/2/3'})
        xknx.devices.devices.append(outlet)

        switch = Switch(xknx, 'TestInput', {'group_address':'1/2/3'})
        action_on = Action(xknx, {'hook': 'on', 'target': 'TestOutlet', 'method': 'on'})
        switch.actions.append(action_on)
        action_off = Action(xknx, {'hook': 'off', 'target': 'TestOutlet', 'method': 'off'})
        switch.actions.append(action_off)
        xknx.devices.devices.append(switch)

        self.assertEqual( xknx.devices.device_by_name('TestInput').state, BinaryInputState.OFF )
        self.assertEqual( xknx.devices.device_by_name('TestOutlet').state, False )

        telegram_on = Telegram()
        telegram_on.payload = DPT_Binary(1)
        switch.process( telegram_on )

        self.assertEqual( xknx.devices.device_by_name('TestInput').state, BinaryInputState.ON )
        self.assertEqual( xknx.devices.device_by_name('TestOutlet').state, True )

        telegram_off = Telegram()
        telegram_off.payload = DPT_Binary(0)
        switch.process( telegram_off )

        self.assertEqual( xknx.devices.device_by_name('TestInput').state, BinaryInputState.OFF )
        self.assertEqual( xknx.devices.device_by_name('TestOutlet').state, False )

suite = unittest.TestLoader().loadTestsFromTestCase(TestBinaryInput)
unittest.TextTestRunner(verbosity=2).run(suite)
