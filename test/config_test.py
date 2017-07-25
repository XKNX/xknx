import unittest
import asyncio

from xknx import XKNX, Light, Switch, Shutter, Thermostat, Time, \
    BinarySensor, Action, Sensor

# pylint: disable=too-many-public-methods,invalid-name
class TestConfig(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    #
    # XKNX Config
    #

    def test_config_light(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Living-Room.Light_1'],
            Light(xknx,
                  'Living-Room.Light_1',
                  group_address_switch='1/6/7',
                  device_updated_cb=xknx.devices.device_updated))


    def test_config_ligh_dimm(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Diningroom.Light_1'],
            Light(xknx,
                  'Diningroom.Light_1',
                  group_address_switch='1/6/4',
                  group_address_dimm='1/6/5',
                  group_address_brightness='1/6/6',
                  device_updated_cb=xknx.devices.device_updated))


    def test_config_switch(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Livingroom.Outlet_2'],
            Switch(xknx,
                   'Livingroom.Outlet_2',
                   group_address='1/3/2',
                   device_updated_cb=xknx.devices.device_updated))


    def test_config_shutter(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Livingroom.Shutter_2'],
            Shutter(xknx,
                    'Livingroom.Shutter_2',
                    group_address_long='1/4/5',
                    group_address_short='1/4/6',
                    group_address_position_feedback='1/4/7',
                    group_address_position='1/4/8',
                    travel_time_down=50,
                    travel_time_up=60,
                    device_updated_cb=xknx.devices.device_updated))


    def test_config_temperature(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Kitchen.Thermostat_1'],
            Thermostat(xknx,
                       'Kitchen.Thermostat_1',
                       group_address_temperature='1/7/1',
                       device_updated_cb=xknx.devices.device_updated))

    def test_config_setpoint(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Livingroom.Thermostat_2'],
            Thermostat(xknx,
                       'Livingroom.Thermostat_2',
                       group_address_temperature='1/7/2',
                       group_address_setpoint='1/7/3',
                       device_updated_cb=xknx.devices.device_updated))

    def test_config_time(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['General.Time'],
            Time(xknx,
                 'General.Time',
                 group_address='2/1/2',
                 device_updated_cb=xknx.devices.device_updated))


    def test_config_binary_sensor(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Livingroom.Switch_1'],
            BinarySensor(xknx,
                         'Livingroom.Switch_1',
                         group_address='1/2/7',
                         actions=[
                             Action(xknx,
                                    hook="on",
                                    target="Livingroom.Outlet_1",
                                    method="on"),
                             Action(xknx,
                                    hook="on",
                                    target="Livingroom.Outlet_2",
                                    method="on")],
                         device_updated_cb=xknx.devices.device_updated))



    def test_config_sensor_percent(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Heating.Valve1'],
            Sensor(xknx,
                   'Heating.Valve1',
                   group_address='2/0/0',
                   value_type='percent',
                   device_updated_cb=xknx.devices.device_updated))


    def test_config_sensor_no_value_type(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Some.Other.Value'],
            Sensor(xknx,
                   'Some.Other.Value',
                   group_address='2/0/2',
                   device_updated_cb=xknx.devices.device_updated))


    def test_config_sensor_binary_device_class(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['DiningRoom.Motion.Sensor'],
            BinarySensor(xknx,
                         'DiningRoom.Motion.Sensor',
                         group_address='3/0/1',
                         device_class='motion',
                         device_updated_cb=xknx.devices.device_updated))


    def test_config_sensor_binary_significant_bit(self):
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Kitchen.Thermostat.Presence'],
            BinarySensor(xknx,
                         'Kitchen.Thermostat.Presence',
                         group_address='3/0/2',
                         significant_bit=2,
                         device_class='motion',
                         device_updated_cb=xknx.devices.device_updated))



SUITE = unittest.TestLoader().loadTestsFromTestCase(TestConfig)
unittest.TextTestRunner(verbosity=2).run(SUITE)
