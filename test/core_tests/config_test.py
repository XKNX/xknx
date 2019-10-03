"""Unit test for Configuration logic."""
import asyncio
import unittest
from unittest.mock import patch

from xknx import XKNX
from xknx.core import Config
from xknx.devices import (
    Action, BinarySensor, Climate, ClimateMode, Cover, DateTime,
    DateTimeBroadcastType, ExposeSensor, Fan, Light, Notification, Scene,
    Sensor, Switch)
from xknx.exceptions import XKNXException
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import PhysicalAddress


# pylint: disable=too-many-public-methods,invalid-name
class TestConfig(unittest.TestCase):
    """Test class for Configuration logic."""

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)
        cls.xknx = XKNX(config='xknx.yaml', loop=cls.loop)

    @classmethod
    def tearDownClass(cls):
        """Tear down test class."""
        cls.loop.close()

    #
    # XKNX General Config
    #
    def test_config_general(self):
        """Test reading general section from config file."""
        self.assertEqual(TestConfig.xknx.own_address, PhysicalAddress('15.15.249'))
        self.assertEqual(TestConfig.xknx.rate_limit, 18)

    #
    # XKNX Connection Config
    #
    def test_config_connection(self):
        """Test connection section from config file."""
        import yaml
        # Default connection setting from xknx.yaml (auto:)
        self.assertEqual(
            TestConfig.xknx.connection_config,
            ConnectionConfig(connection_type=ConnectionType.AUTOMATIC))
        # Replaces setting from xknx.yaml
        test_configs = [
            ("""
            connection:
                tunneling:
                    local_ip: '192.168.1.2'
                    gateway_ip: 192.168.1.15
                    gateway_port: 6000
            """,
             ConnectionConfig(
                 connection_type=ConnectionType.TUNNELING,
                 local_ip="192.168.1.2",
                 gateway_ip="192.168.1.15",
                 gateway_port=6000)
             ),
            ("""
            connection:
                tunneling:
                    gateway_ip: '192.168.1.2'
            """,
             ConnectionConfig(
                 connection_type=ConnectionType.TUNNELING,
                 gateway_ip="192.168.1.2")
             ),
            ("""
            connection:
                routing:
                    local_ip: '192.168.1.2'
            """,
             ConnectionConfig(
                 connection_type=ConnectionType.ROUTING,
                 local_ip="192.168.1.2")
             ),
            ("""
            connection:
                routing:
            """,
             ConnectionConfig(connection_type=ConnectionType.ROUTING)
             )
        ]
        for yaml_string, expected_conn in test_configs:
            config = yaml.safe_load(yaml_string)
            Config(TestConfig.xknx).parse_connection(config)
            self.assertEqual(TestConfig.xknx.connection_config, expected_conn)

    def test_config_invalid_connection(self):
        """Test invalid connection section from config file."""
        import yaml
        test_configs = [
            ("""
            connection:
                tunneling:
                    local_ip: '192.168.1.2'
            """,
             XKNXException,
             "`gateway_ip` is required for tunneling connection."
             )
        ]
        for yaml_string, expected_exception, exception_message in test_configs:
            with self.assertRaises(expected_exception, msg=exception_message):
                config = yaml.safe_load(yaml_string)
                Config(TestConfig.xknx).parse_connection(config)

    #
    # XKNX Groups Config
    #

    def test_config_light(self):
        """Test reading Light from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Living-Room.Light_1'],
            Light(TestConfig.xknx,
                  'Living-Room.Light_1',
                  group_address_switch='1/6/9',
                  min_kelvin=2700,
                  max_kelvin=6000,
                  device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_light_state(self):
        """Test reading Light with dimming address from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Office.Light_1'],
            Light(TestConfig.xknx,
                  'Office.Light_1',
                  group_address_switch='1/7/4',
                  group_address_switch_state='1/7/5',
                  group_address_brightness='1/7/6',
                  group_address_brightness_state='1/7/7',
                  min_kelvin=2700,
                  max_kelvin=6000,
                  device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_light_color(self):
        """Test reading Light with with dimming and color address."""
        self.assertEqual(
            TestConfig.xknx.devices['Diningroom.Light_1'],
            Light(TestConfig.xknx,
                  'Diningroom.Light_1',
                  group_address_switch='1/6/4',
                  group_address_brightness='1/6/6',
                  group_address_color='1/6/7',
                  group_address_color_state='1/6/8',
                  min_kelvin=2700,
                  max_kelvin=6000,
                  device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_color_temperature(self):
        """Test reading Light with with dimming and color temperature address."""
        self.assertEqual(
            TestConfig.xknx.devices['Living-Room.Light_CT'],
            Light(TestConfig.xknx,
                  'Living-Room.Light_CT',
                  group_address_switch='1/6/11',
                  group_address_switch_state='1/6/10',
                  group_address_brightness='1/6/12',
                  group_address_brightness_state='1/6/13',
                  group_address_color_temperature='1/6/14',
                  group_address_color_temperature_state='1/6/15',
                  min_kelvin=2700,
                  max_kelvin=6000,
                  device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_tunable_white(self):
        """Test reading Light with with dimming and tunable white address."""
        self.assertEqual(
            TestConfig.xknx.devices['Living-Room.Light_TW'],
            Light(TestConfig.xknx,
                  'Living-Room.Light_TW',
                  group_address_switch='1/6/21',
                  group_address_switch_state='1/6/20',
                  group_address_brightness='1/6/22',
                  group_address_brightness_state='1/6/23',
                  group_address_tunable_white='1/6/24',
                  group_address_tunable_white_state='1/6/25',
                  min_kelvin=2700,
                  max_kelvin=6000,
                  device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_switch(self):
        """Test reading Switch from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Livingroom.Outlet_2'],
            Switch(TestConfig.xknx,
                   'Livingroom.Outlet_2',
                   group_address='1/3/2',
                   device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_fan(self):
        """Test reading Fan from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Kitchen.Fan_1'],
            Fan(TestConfig.xknx,
                'Kitchen.Fan_1',
                group_address_speed='1/3/21',
                group_address_speed_state='1/3/22',
                device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_cover(self):
        """Test reading Cover from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Livingroom.Shutter_2'],
            Cover(TestConfig.xknx,
                  'Livingroom.Shutter_2',
                  group_address_long='1/4/5',
                  group_address_short='1/4/6',
                  group_address_position_state='1/4/7',
                  group_address_position='1/4/8',
                  travel_time_down=50,
                  travel_time_up=60,
                  device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_cover_venetian(self):
        """Test reading Cover with angle from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Children.Venetian'],
            Cover(TestConfig.xknx,
                  'Children.Venetian',
                  group_address_long='1/4/14',
                  group_address_short='1/4/15',
                  group_address_position_state='1/4/17',
                  group_address_position='1/4/16',
                  group_address_angle='1/4/18',
                  group_address_angle_state='1/4/19',
                  device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_cover_venetian_with_inverted_position(self):
        """Test reading Cover with angle from config file with inverted position/angle."""
        self.assertEqual(
            TestConfig.xknx.devices['Children.Venetian2'],
            Cover(TestConfig.xknx,
                  'Children.Venetian2',
                  group_address_long='1/4/14',
                  group_address_short='1/4/15',
                  group_address_position_state='1/4/17',
                  group_address_position='1/4/16',
                  group_address_angle='1/4/18',
                  group_address_angle_state='1/4/19',
                  invert_position=True,
                  invert_angle=True,
                  device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_climate_temperature(self):
        """Test reading Climate object from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Kitchen.Climate'],
            Climate(TestConfig.xknx,
                    'Kitchen.Climate',
                    group_address_temperature='1/7/1',
                    device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_climate_target_temperature_and_setpoint_shift(self):
        """Test reading Climate object with target_temperature_address and setpoint shift from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Children.Climate'],
            Climate(TestConfig.xknx,
                    'Children.Climate',
                    group_address_temperature='1/7/2',
                    group_address_target_temperature='1/7/4',
                    group_address_setpoint_shift='1/7/3',
                    group_address_setpoint_shift_state='1/7/14',
                    setpoint_shift_step=0.1,
                    setpoint_shift_min=-10,
                    setpoint_shift_max=10,
                    device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_climate_operation_mode(self):
        """Test reading Climate object with operation mode in one group address from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Office.Climate'].mode,
            ClimateMode(TestConfig.xknx,
                        name=None,
                        group_address_operation_mode='1/7/6',
                        device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_climate_operation_mode2(self):
        """Test reading Climate object with operation mode in different group addresses  from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Attic.Climate'].mode,
            ClimateMode(TestConfig.xknx,
                        name=None,
                        group_address_operation_mode_protection='1/7/8',
                        group_address_operation_mode_night='1/7/9',
                        group_address_operation_mode_comfort='1/7/10',
                        device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_climate_operation_mode_state(self):
        """Test reading Climate object with status address for operation mode."""
        self.assertEqual(
            TestConfig.xknx.devices['Bath.Climate'].mode,
            ClimateMode(TestConfig.xknx,
                        name=None,
                        group_address_operation_mode='1/7/6',
                        group_address_operation_mode_state='1/7/7',
                        device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_climate_controller_status_state(self):
        """Test reading Climate object with addresses for controller status."""
        self.assertEqual(
            TestConfig.xknx.devices['Cellar.Climate'].mode,
            ClimateMode(TestConfig.xknx,
                        name=None,
                        group_address_controller_status='1/7/12',
                        group_address_controller_status_state='1/7/13',
                        device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_datetime(self):
        """Test reading DateTime objects from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['General.Time'],
            DateTime(
                TestConfig.xknx,
                'General.Time',
                group_address='2/1/1',
                broadcast_type=DateTimeBroadcastType.TIME,
                device_updated_cb=TestConfig.xknx.devices.device_updated))
        self.assertEqual(
            TestConfig.xknx.devices['General.DateTime'],
            DateTime(
                TestConfig.xknx,
                'General.DateTime',
                group_address='2/1/2',
                broadcast_type=DateTimeBroadcastType.DATETIME,
                device_updated_cb=TestConfig.xknx.devices.device_updated))
        self.assertEqual(
            TestConfig.xknx.devices['General.Date'],
            DateTime(
                TestConfig.xknx,
                'General.Date',
                group_address='2/1/3',
                broadcast_type=DateTimeBroadcastType.DATE,
                device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_notification(self):
        """Test reading DateTime object from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['AlarmWindow'],
            Notification(
                TestConfig.xknx,
                'AlarmWindow',
                group_address='2/7/1',
                group_address_state='2/7/2',
                device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_binary_sensor(self):
        """Test reading BinarySensor from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Livingroom.Switch_1'],
            BinarySensor(TestConfig.xknx,
                         'Livingroom.Switch_1',
                         group_address_state='1/2/7',
                         actions=[
                             Action(TestConfig.xknx,
                                    target="Livingroom.Outlet_1",
                                    method="on"),
                             Action(TestConfig.xknx,
                                    target="Livingroom.Outlet_2",
                                    counter=2,
                                    method="on")],
                         device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_sensor_percent(self):
        """Test reading percent Sensor from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Heating.Valve1'],
            Sensor(TestConfig.xknx,
                   'Heating.Valve1',
                   group_address_state='2/0/0',
                   value_type='percent',
                   sync_state=True,
                   device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_sensor_percent_passive(self):
        """Test passive percent Sensor from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Heating.Valve2'],
            Sensor(TestConfig.xknx,
                   'Heating.Valve2',
                   group_address_state='2/0/1',
                   value_type='percent',
                   sync_state=False,
                   device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_sensor_temperature_type(self):
        """Test reading temperature Sensor from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Kitchen.Temperature'],
            Sensor(TestConfig.xknx,
                   'Kitchen.Temperature',
                   group_address_state='2/0/2',
                   value_type='temperature',
                   device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_expose_sensor(self):
        """Test reading ExposeSensor from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Outside.Temperature'],
            ExposeSensor(
                TestConfig.xknx,
                'Outside.Temperature',
                group_address='2/0/3',
                value_type='temperature',
                device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_sensor_binary_device_class(self):
        """Test reading Sensor with device_class from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Kitchen.Motion.Sensor'],
            BinarySensor(TestConfig.xknx,
                         'Kitchen.Motion.Sensor',
                         group_address_state='3/0/0',
                         device_class='motion',
                         device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_sensor_binary_passive(self):
        """Test reading Sensor with sync_state False from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['DiningRoom.Motion.Sensor'],
            BinarySensor(TestConfig.xknx,
                         'DiningRoom.Motion.Sensor',
                         group_address_state='3/0/1',
                         sync_state=False,
                         device_class='motion',
                         device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_sensor_binary_significant_bit(self):
        """Test reading Sensor with differing significant bit from config file."""
        self.assertEqual(
            TestConfig.xknx.devices['Kitchen.Presence'],
            BinarySensor(TestConfig.xknx,
                         'Kitchen.Presence',
                         group_address_state='3/0/2',
                         significant_bit=2,
                         device_class='motion',
                         device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_scene(self):
        """Test reading Scene from config file."""
        self.assertEqual(
            TestConfig.xknx.devices["Romantic"],
            Scene(
                TestConfig.xknx,
                "Romantic",
                group_address='7/0/1',
                scene_number=23,
                device_updated_cb=TestConfig.xknx.devices.device_updated))

    def test_config_file_not_found(self):
        """Test error message when reading a non exisiting config file."""
        with patch('logging.Logger.error') as mock_err:
            XKNX(config='xknx_does_not_exist.yaml', loop=self.loop)
            self.assertEqual(mock_err.call_count, 1)

    def test_config_file_error(self):
        """Test error message when reading an errornous config file."""
        with patch('logging.Logger.error') as mock_err, \
                patch('xknx.core.Config.parse_group_light') as mock_parse:
            mock_parse.side_effect = XKNXException()
            XKNX(config='xknx.yaml', loop=self.loop)
            self.assertEqual(mock_err.call_count, 1)
