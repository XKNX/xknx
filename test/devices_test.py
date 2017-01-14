import unittest

from xknx import XKNX, Devices, Address, Light, Outlet, Sensor

# pylint: disable=too-many-public-methods,invalid-name
class TestDevices(unittest.TestCase):

    #
    # XKNX Config
    #

    def test_device_by_name(self):
        xknx = XKNX()
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)

        outlet1 = Outlet(xknx,
                         "TestOutlet_1",
                         group_address='1/2/3')
        devices.add(outlet1)

        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')
        devices.add(light2)

        outlet2 = Outlet(xknx,
                         "TestOutlet_2",
                         group_address='1/2/4')
        devices.add(outlet2)

        self.assertEqual(devices.device_by_name("Living-Room.Light_1"), light1)
        self.assertEqual(devices.device_by_name("Living-Room.Light_2"), light2)
        self.assertEqual(devices.device_by_name("TestOutlet_1"), outlet1)
        self.assertEqual(devices.device_by_name("TestOutlet_2"), outlet2)


    def test_device_by_group_address(self):
        xknx = XKNX()
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)

        sensor1 = Sensor(xknx,
                         'DiningRoom.Motion.Sensor',
                         group_address='3/0/1',
                         value_type='binary',
                         significant_bit=2)
        devices.add(sensor1)

        sensor2 = Sensor(xknx,
                         'DiningRoom.Motion.Sensor',
                         group_address='3/0/1',
                         value_type='binary',
                         significant_bit=3)
        devices.add(sensor2)

        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')
        devices.add(light2)

        self.assertEqual(
            tuple(devices.devices_by_group_address(Address('1/6/7'))),
            (light1,))
        self.assertEqual(
            tuple(devices.devices_by_group_address(Address('1/6/8'))),
            (light2,))
        self.assertEqual(
            tuple(devices.devices_by_group_address(Address('3/0/1'))),
            (sensor1, sensor2))

    def test_iter(self):
        xknx = XKNX()
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)

        sensor1 = Sensor(xknx,
                         'DiningRoom.Motion.Sensor',
                         group_address='3/0/1',
                         value_type='binary',
                         significant_bit=2)
        devices.add(sensor1)

        sensor2 = Sensor(xknx,
                         'DiningRoom.Motion.Sensor',
                         group_address='3/0/1',
                         value_type='binary',
                         significant_bit=3)
        devices.add(sensor2)

        light2 = Light(xknx,
                       'Living-Room.Light_2',
                       group_address_switch='1/6/8')

        devices.add(light2)

        self.assertEqual(
            tuple(devices.__iter__()),
            (light1, sensor1, sensor2, light2))


    def test_modification_of_device(self):
        """ This test should verify that devices only
        stores the references of an object and all
        accessing functions only return referecenes of
        the same object"""

        xknx = XKNX()
        devices = Devices()

        light1 = Light(xknx,
                       'Living-Room.Light_1',
                       group_address_switch='1/6/7')
        devices.add(light1)

        for device in devices:
            device.set_on()

        self.assertTrue(light1.state)

        device2 = devices.device_by_name("Living-Room.Light_1")
        device2.set_off()

        self.assertFalse(light1.state)

        for device in devices.devices_by_group_address(Address('1/6/7')):
            device.set_on()

        self.assertTrue(light1.state)



SUITE = unittest.TestLoader().loadTestsFromTestCase(TestDevices)
unittest.TextTestRunner(verbosity=2).run(SUITE)
