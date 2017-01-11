import unittest
from unittest.mock import Mock

from xknx import XKNX, Sensor, Telegram, \
    DPTArray, DPTBinary, Address, TelegramType

class TestSensor(unittest.TestCase):

    #
    # STR FUNCTIONS
    #
    def test_str_array(self):
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3')
        sensor.state = DPTArray((0x01, 0x02, 0x03))

        self.assertEqual(sensor.state_str(), "0x01,0x02,0x03")


    def test_str_binary(self):
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3')
        sensor.state = DPTBinary(5)

        self.assertEqual(sensor.state_str(), "101")


    def test_str_scaling(self):
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3',
            value_type="percent")
        sensor.state = DPTArray((0x40,))

        self.assertEqual(sensor.state_str(), "25")
        self.assertEqual(sensor.unit_of_measurement(), "%")

    #
    # SYNC STATE
    #
    def test_sync_state(self):
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3')

        sensor.sync_state()

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/3'), TelegramType.GROUP_READ))

    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3')

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray((0x01, 0x02, 0x03))
        sensor.process(telegram)

        self.assertEqual(sensor.state, DPTArray((0x01, 0x02, 0x03)))


    def test_process_callback(self):
        # pylint: disable=no-self-use
        xknx = XKNX()
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3')

        after_update_callback = Mock()
        sensor.after_update_callback = after_update_callback

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray((0x01, 0x02, 0x03))
        sensor.process(telegram)

        after_update_callback.assert_called_with(sensor)



SUITE = unittest.TestLoader().loadTestsFromTestCase(TestSensor)
unittest.TextTestRunner(verbosity=2).run(SUITE)
