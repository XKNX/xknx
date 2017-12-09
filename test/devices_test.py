"""Unit test for devices container within XKNX."""
import asyncio
import unittest

from xknx import XKNX
from xknx.devices import BinarySensor, Devices, Light, Switch
from xknx.knx import GroupAddress


# pylint: disable=too-many-public-methods,invalid-name
class TestDevices(unittest.TestCase):
    """Test class for devices container within XKNX."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # XKNX Config
    #
    def test_get_item(self):
        """Test get item by name or by index."""
        xknx = XKNX(loop=self.loop)
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)

        switch1 = Switch(xknx,
                         "TestOutlet_1",
                         group_address='1/2/3')
        devices.add(switch1)

        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')
        devices.add(light2)

        switch2 = Switch(xknx,
                         "TestOutlet_2",
                         group_address='1/2/4')
        devices.add(switch2)

        self.assertEqual(devices["Living-Room.Light_1"], light1)
        self.assertEqual(devices["TestOutlet_1"], switch1)
        self.assertEqual(devices["Living-Room.Light_2"], light2)
        self.assertEqual(devices["TestOutlet_2"], switch2)
        with self.assertRaises(KeyError):
            # pylint: disable=pointless-statement
            devices["TestOutlet_X"]

        self.assertEqual(devices[0], light1)
        self.assertEqual(devices[1], switch1)
        self.assertEqual(devices[2], light2)
        self.assertEqual(devices[3], switch2)
        with self.assertRaises(IndexError):
            # pylint: disable=pointless-statement
            devices[4]

    def test_device_by_group_address(self):
        """Test get devices by group address."""
        xknx = XKNX(loop=self.loop)
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)

        sensor1 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address='3/0/1',
                               significant_bit=2)
        devices.add(sensor1)

        sensor2 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address='3/0/1',
                               significant_bit=3)
        devices.add(sensor2)

        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')
        devices.add(light2)

        self.assertEqual(
            tuple(devices.devices_by_group_address(GroupAddress('1/6/7'))),
            (light1,))
        self.assertEqual(
            tuple(devices.devices_by_group_address(GroupAddress('1/6/8'))),
            (light2,))
        self.assertEqual(
            tuple(devices.devices_by_group_address(GroupAddress('3/0/1'))),
            (sensor1, sensor2))

    def test_iter(self):
        """Test __iter__() function."""
        xknx = XKNX(loop=self.loop)
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)

        sensor1 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address='3/0/1',
                               significant_bit=2)
        devices.add(sensor1)

        sensor2 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address='3/0/1',
                               significant_bit=3)
        devices.add(sensor2)

        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')

        devices.add(light2)

        self.assertEqual(
            tuple(devices.__iter__()),
            (light1, sensor1, sensor2, light2))

    def test_len(self):
        """Test len() function."""
        xknx = XKNX(loop=self.loop)
        devices = Devices()
        self.assertEqual(len(devices), 0)

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)
        self.assertEqual(len(devices), 1)

        sensor1 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address='3/0/1',
                               significant_bit=2)
        devices.add(sensor1)
        self.assertEqual(len(devices), 2)

        sensor2 = BinarySensor(xknx,
                               'DiningRoom.Motion.Sensor',
                               group_address='3/0/1',
                               significant_bit=3)
        devices.add(sensor2)
        self.assertEqual(len(devices), 3)

        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')
        devices.add(light2)
        self.assertEqual(len(devices), 4)

    def test_modification_of_device(self):
        """Test if devices object does store references and not copies of objects."""
        xknx = XKNX(loop=self.loop)
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)

        for device in devices:
            self.loop.run_until_complete(asyncio.Task(device.set_on()))

        self.assertTrue(light1.state)

        device2 = devices["Living-Room.Light_1"]
        self.loop.run_until_complete(asyncio.Task(device2.set_off()))

        self.assertFalse(light1.state)

        for device in devices.devices_by_group_address(GroupAddress('1/6/7')):
            self.loop.run_until_complete(asyncio.Task(device.set_on()))

        self.assertTrue(light1.state)


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestDevices)
unittest.TextTestRunner(verbosity=2).run(SUITE)
