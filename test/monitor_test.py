import unittest
from unittest.mock import Mock

from xknx import XKNX, Monitor, Telegram, \
    DPTArray, DPTBinary, Address, TelegramType

class TestMonitor(unittest.TestCase):

    #
    # STR FUNCTIONS
    #
    def test_str_array(self):
        xknx = XKNX()
        monitor = Monitor(
            xknx,
            'TestMonitor',
            group_address='1/2/3')
        monitor.state = DPTArray((0x01, 0x02, 0x03))

        self.assertEqual(monitor.state_str(), "0x01,0x02,0x03")


    def test_str_binary(self):
        xknx = XKNX()
        monitor = Monitor(
            xknx,
            'TestMonitor',
            group_address='1/2/3')
        monitor.state = DPTBinary(5)

        self.assertEqual(monitor.state_str(), "101")


    def test_str_scaling(self):
        xknx = XKNX()
        monitor = Monitor(
            xknx,
            'TestMonitor',
            group_address='1/2/3',
            value_type="percent")
        monitor.state = DPTArray((0x40,))

        self.assertEqual(monitor.state_str(), "25 %")

    #
    # SYNC STATE
    #
    def test_sync_state(self):
        xknx = XKNX()
        monitor = Monitor(
            xknx,
            'TestMonitor',
            group_address='1/2/3')

        monitor.sync_state()

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/3'), TelegramType.GROUP_READ))

    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX()
        monitor = Monitor(
            xknx,
            'TestMonitor',
            group_address='1/2/3')

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray((0x01, 0x02, 0x03))
        monitor.process(telegram)

        self.assertEqual(monitor.state, DPTArray((0x01, 0x02, 0x03)))


    def test_process_callback(self):
        # pylint: disable=no-self-use
        xknx = XKNX()
        monitor = Monitor(
            xknx,
            'TestMonitor',
            group_address='1/2/3')

        after_update_callback = Mock()
        monitor.after_update_callback = after_update_callback

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray((0x01, 0x02, 0x03))
        monitor.process(telegram)

        after_update_callback.assert_called_with(monitor)



SUITE = unittest.TestLoader().loadTestsFromTestCase(TestMonitor)
unittest.TextTestRunner(verbosity=2).run(SUITE)
