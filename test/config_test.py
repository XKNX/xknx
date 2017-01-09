import unittest

from xknx import XKNX, Config, Light, Outlet, Shutter, Thermostat, Time, \
    Switch, Action

class TestConfig(unittest.TestCase):

    #
    # XKNX Config
    #

    def test_config_light(self):
        xknx = XKNX()
        Config(xknx).read('../xknx.yaml')
        self.assertEqual(
            xknx.devices.device_by_name('Living-Room.Light_1'),
            Light(xknx,
                  'Living-Room.Light_1',
                  group_address_switch='1/6/7'))


    def test_config_ligh_dimm(self):
        xknx = XKNX()
        Config(xknx).read('../xknx.yaml')
        self.assertEqual(
            xknx.devices.device_by_name('Diningroom.Light_1'),
            Light(xknx,
                  'Diningroom.Light_1',
                  group_address_switch='1/6/4',
                  group_address_dimm='1/6/5',
                  group_address_brightness='1/6/6'))


    def test_config_outlet(self):
        xknx = XKNX()
        Config(xknx).read('../xknx.yaml')
        self.assertEqual(
            xknx.devices.device_by_name('Livingroom.Outlet_2'),
            Outlet(xknx,
                   'Livingroom.Outlet_2',
                   group_address='1/3/2'))


    def test_config_shutter(self):
        xknx = XKNX()
        Config(xknx).read('../xknx.yaml')
        self.assertEqual(
            xknx.devices.device_by_name('Livingroom.Shutter_2'),
            Shutter(xknx,
                    'Livingroom.Shutter_2',
                    group_address_long='1/4/5',
                    group_address_short='1/4/6',
                    group_address_position_feedback='1/4/7',
                    group_address_position='1/4/8',
                    travel_time_down=50,
                    travel_time_up=60))


    def test_config_temperature(self):
        xknx = XKNX()
        Config(xknx).read('../xknx.yaml')
        self.assertEqual(
            xknx.devices.device_by_name('Kitchen.Thermostat_1'),
            Thermostat(xknx,
                       'Kitchen.Thermostat_1',
                       group_address_temperature='1/7/1'))

    def test_config_setpoint(self):
        xknx = XKNX()
        Config(xknx).read('../xknx.yaml')
        self.assertEqual(
            xknx.devices.device_by_name('Livingroom.Thermostat_2'),
            Thermostat(xknx,
                       'Livingroom.Thermostat_2',
                       group_address_temperature='1/7/2',
                       group_address_setpoint='1/7/3'))

    def test_config_time(self):
        xknx = XKNX()
        Config(xknx).read('../xknx.yaml')
        self.assertEqual(
            xknx.devices.device_by_name('General.Time'),
            Time(xknx,
                 'General.Time',
                 group_address='2/1/2'))


    def test_config_switch(self):
        xknx = XKNX()
        Config(xknx).read('../xknx.yaml')
        self.assertEqual(
            xknx.devices.device_by_name('Livingroom.Switch_1'),
            Switch(xknx,
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
                              method="on")]))


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestConfig)
unittest.TextTestRunner(verbosity=2).run(SUITE)
