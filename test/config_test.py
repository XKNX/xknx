"""Unit test for Configuration logic."""
import unittest
import asyncio

from xknx import XKNX
from xknx.devices import Light, Switch, Cover, Climate, Time, \
    BinarySensor, Action, Sensor, Notification


# pylint: disable=too-many-public-methods,invalid-name
class TestConfig(unittest.TestCase):
    """Test class for Configuration logic."""

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
    def test_config_light(self):
        """Test reading Light from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Living-Room.Light_1'],
            Light(xknx,
                  'Living-Room.Light_1',
                  group_address_switch='1/6/7',
                  device_updated_cb=xknx.devices.device_updated))

    def test_config_light_state(self):
        """Test reading Light with dimming address from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Office.Light_1'],
            Light(xknx,
                  'Office.Light_1',
                  group_address_switch='1/7/4',
                  group_address_switch_state='1/7/5',
                  group_address_brightness='1/7/6',
                  group_address_brightness_state='1/7/7',
                  device_updated_cb=xknx.devices.device_updated))

    def test_config_switch(self):
        """Test reading Switch from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Livingroom.Outlet_2'],
            Switch(xknx,
                   'Livingroom.Outlet_2',
                   group_address='1/3/2',
                   device_updated_cb=xknx.devices.device_updated))

    def test_config_cover(self):
        """Test reading Cover from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Livingroom.Shutter_2'],
            Cover(xknx,
                  'Livingroom.Shutter_2',
                  group_address_long='1/4/5',
                  group_address_short='1/4/6',
                  group_address_position_feedback='1/4/7',
                  group_address_position='1/4/8',
                  travel_time_down=50,
                  travel_time_up=60,
                  device_updated_cb=xknx.devices.device_updated))

    def test_config_climate_temperature(self):
        """Test reading Climate object from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Kitchen.Climate'],
            Climate(xknx,
                    'Kitchen.Climate',
                    group_address_temperature='1/7/1',
                    device_updated_cb=xknx.devices.device_updated))

    def test_config_climate_target_temperature(self):
        """Test reading Climate object with target_temperature_address and setpoint from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Children.Climate'],
            Climate(xknx,
                    'Children.Climate',
                    group_address_temperature='1/7/2',
                    group_address_setpoint='1/7/3',
                    group_address_target_temperature='1/7/4',
                    device_updated_cb=xknx.devices.device_updated))

    def test_config_climate_operation_mode(self):
        """Test reading Climate object with operation mode in one group address from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Office.Climate'],
            Climate(xknx,
                    'Office.Climate',
                    group_address_temperature='1/7/5',
                    group_address_operation_mode='1/7/6',
                    device_updated_cb=xknx.devices.device_updated))

    def test_config_climate_operation_mode2(self):
        """Test reading Climate object with operation mode in different group addresses  from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Attic.Climate'],
            Climate(xknx,
                    'Attic.Climate',
                    group_address_temperature='1/7/7',
                    group_address_operation_mode_protection='1/7/8',
                    group_address_operation_mode_night='1/7/9',
                    group_address_operation_mode_comfort='1/7/10',
                    device_updated_cb=xknx.devices.device_updated))

    def test_config_time(self):
        """Test reading Time object from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['General.Time'],
            Time(xknx,
                 'General.Time',
                 group_address='2/1/2',
                 device_updated_cb=xknx.devices.device_updated))

    def test_config_notification(self):
        """Test reading Time object from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['AlarmWindow'],
            Notification(
                xknx,
                'AlarmWindow',
                group_address='2/1/3',
                device_updated_cb=xknx.devices.device_updated))

    def test_config_binary_sensor(self):
        """Test reading BinarySensor from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Livingroom.Switch_1'],
            BinarySensor(xknx,
                         'Livingroom.Switch_1',
                         group_address='1/2/7',
                         actions=[
                             Action(xknx,
                                    target="Livingroom.Outlet_1",
                                    method="on"),
                             Action(xknx,
                                    target="Livingroom.Outlet_2",
                                    counter=2,
                                    method="on")],
                         device_updated_cb=xknx.devices.device_updated))

    def test_config_sensor_percent(self):
        """Test reading Sensor with value_type from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Heating.Valve1'],
            Sensor(xknx,
                   'Heating.Valve1',
                   group_address='2/0/0',
                   value_type='percent',
                   device_updated_cb=xknx.devices.device_updated))

    def test_config_sensor_no_value_type(self):
        """Test reading Sensor without value_type from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Some.Other.Value'],
            Sensor(xknx,
                   'Some.Other.Value',
                   group_address='2/0/2',
                   device_updated_cb=xknx.devices.device_updated))

    def test_config_sensor_binary_device_class(self):
        """Test reading Sensor with device_class from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['DiningRoom.Motion.Sensor'],
            BinarySensor(xknx,
                         'DiningRoom.Motion.Sensor',
                         group_address='3/0/1',
                         device_class='motion',
                         device_updated_cb=xknx.devices.device_updated))

    def test_config_sensor_binary_significant_bit(self):
        """Test reading Sensor with differing significant bit from config file."""
        xknx = XKNX(config='../xknx.yaml', loop=self.loop)
        self.assertEqual(
            xknx.devices['Kitchen.Presence'],
            BinarySensor(xknx,
                         'Kitchen.Presence',
                         group_address='3/0/2',
                         significant_bit=2,
                         device_class='motion',
                         device_updated_cb=xknx.devices.device_updated))


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestConfig)
unittest.TextTestRunner(verbosity=2).run(SUITE)
