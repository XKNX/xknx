import unittest
from unittest.mock import Mock
import asyncio
from xknx import XKNX, Sensor
from xknx.knx import Telegram, Address, TelegramType, DPTArray, DPTBinary

class TestSensor(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    #
    # STR FUNCTIONS
    #
    def test_str_array(self):
        xknx = XKNX(loop=self.loop, start=False)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3')
        sensor.state = DPTArray((0x01, 0x02, 0x03))

        self.assertEqual(sensor.resolve_state(), "0x01,0x02,0x03")


    def test_str_binary(self):
        xknx = XKNX(loop=self.loop, start=False)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3')
        sensor.state = DPTBinary(5)

        self.assertEqual(sensor.resolve_state(), "101")


    def test_str_scaling(self):
        xknx = XKNX(loop=self.loop, start=False)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3',
            value_type="percent")
        sensor.state = DPTArray((0x40,))

        self.assertEqual(sensor.resolve_state(), "25")
        self.assertEqual(sensor.unit_of_measurement(), "%")

    def test_not_binary(self):
        xknx = XKNX(loop=self.loop, start=False)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3',
            value_type="percent")
        self.assertFalse(sensor.is_binary())
        self.assertFalse(sensor.binary_state())
        # Even after setting a binary value,
        # binary state should not return true
        sensor.state = DPTBinary(5)
        self.assertFalse(sensor.binary_state())

    def test_binary(self):
        xknx = XKNX(loop=self.loop, start=False)
        sensor = Sensor(
            xknx,
            'DiningRoom.Motion.Sensor',
            group_address='3/0/1',
            value_type='binary',
            device_class='motion')
        self.assertEqual(sensor.significant_bit, 1)
        self.assertTrue(sensor.is_binary())

        # No sensor set, binary_state should resolve to False
        self.assertFalse(sensor.binary_state())

        # First bit is set
        sensor.state = DPTBinary(5)
        self.assertTrue(sensor.binary_state())

        # State with the wrong bit set
        sensor.state = DPTBinary(8)
        self.assertFalse(sensor.binary_state())

        # Shifting significant bit to 4th position
        sensor.significant_bit = 4
        sensor.state = DPTBinary(8)
        self.assertTrue(sensor.binary_state())
        sensor.state = DPTBinary(7)
        self.assertFalse(sensor.binary_state())


    #
    # SYNC
    #
    def test_sync(self):
        xknx = XKNX(loop=self.loop, start=False)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3')

        self.loop.run_until_complete(asyncio.Task(sensor.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/3'), TelegramType.GROUP_READ))

    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX(loop=self.loop, start=False)
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
        xknx = XKNX(loop=self.loop, start=False)
        sensor = Sensor(
            xknx,
            'TestSensor',
            group_address='1/2/3')

        after_update_callback = Mock()
        sensor.register_device_updated_cb(after_update_callback)

        telegram = Telegram(Address('1/2/3'))
        telegram.payload = DPTArray((0x01, 0x02, 0x03))
        sensor.process(telegram)

        after_update_callback.assert_called_with(sensor)



SUITE = unittest.TestLoader().loadTestsFromTestCase(TestSensor)
unittest.TextTestRunner(verbosity=2).run(SUITE)
