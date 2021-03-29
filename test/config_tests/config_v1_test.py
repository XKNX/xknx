"""Unit test for Configuration logic."""
import asyncio
import os
from unittest.mock import Mock, patch

import pytest
from xknx import XKNX
from xknx.config import ConfigV1
from xknx.devices import (
    Action,
    BinarySensor,
    Climate,
    ClimateMode,
    Cover,
    DateTime,
    ExposeSensor,
    Fan,
    Light,
    Notification,
    Scene,
    Sensor,
    Switch,
    Weather,
)
from xknx.exceptions import XKNXException
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import IndividualAddress
import yaml


# pylint: disable=too-many-public-methods,invalid-name
class TestConfig:
    """Test class for Configuration logic."""

    @classmethod
    def setup_class(cls):
        """Set up test class."""
        # patch creation of asyncio.Task in DateTime devices (would leave open tasks every time xknx.yaml is read)
        cls.datetime_patcher = patch(
            "xknx.devices.DateTime._create_broadcast_task", return_value=None
        )
        cls.datetime_patcher.start()

        cls.xknx = XKNX(config="xknx.yaml")

    @classmethod
    def teardown_class(cls):
        """Tear down test class."""
        cls.datetime_patcher.stop()

    #
    # XKNX General Config
    #
    def test_config_general(self):
        """Test reading general section from config file."""
        assert TestConfig.xknx.own_address == IndividualAddress("15.15.249")
        assert TestConfig.xknx.rate_limit == 18
        assert TestConfig.xknx.multicast_group == "224.1.2.3"
        assert TestConfig.xknx.multicast_port == 1337

    #
    # XKNX Connection Config
    #
    def test_config_connection(self):
        """Test connection section from config file."""

        # Default connection setting from xknx.yaml (auto:)
        assert TestConfig.xknx.connection_config == ConnectionConfig(
            connection_type=ConnectionType.AUTOMATIC
        )
        # Replaces setting from xknx.yaml
        test_configs = [
            (
                """
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
                    gateway_port=6000,
                ),
            ),
            (
                """
            connection:
                tunneling:
                    gateway_ip: '192.168.1.2'
            """,
                ConnectionConfig(
                    connection_type=ConnectionType.TUNNELING, gateway_ip="192.168.1.2"
                ),
            ),
            (
                """
            connection:
                routing:
                    local_ip: '192.168.1.2'
            """,
                ConnectionConfig(
                    connection_type=ConnectionType.ROUTING, local_ip="192.168.1.2"
                ),
            ),
            (
                """
            connection:
                routing:
            """,
                ConnectionConfig(connection_type=ConnectionType.ROUTING),
            ),
        ]
        for yaml_string, expected_conn in test_configs:
            config = yaml.safe_load(yaml_string)
            ConfigV1(TestConfig.xknx).parse_connection(config)
            assert TestConfig.xknx.connection_config == expected_conn

    def test_config_invalid_connection(self):
        """Test invalid connection section from config file."""

        test_configs = [
            (
                """
            connection:
                tunneling:
                    local_ip: '192.168.1.2'
            """,
                XKNXException,
                "`gateway_ip` is required for tunneling connection.",
            )
        ]
        for yaml_string, expected_exception, exception_message in test_configs:
            with pytest.raises(expected_exception):
                config = yaml.safe_load(yaml_string)
                ConfigV1(TestConfig.xknx).parse_connection(config)

    #
    # XKNX Groups Config
    #

    def test_config_light(self):
        """Test reading Light from config file."""
        assert TestConfig.xknx.devices["Living-Room.Light_1"] == Light(
            TestConfig.xknx,
            "Living-Room.Light_1",
            group_address_switch="1/6/9",
            min_kelvin=2700,
            max_kelvin=6000,
        )

    def test_config_light_state(self):
        """Test reading Light with dimming address from config file."""
        assert TestConfig.xknx.devices["Office.Light_1"] == Light(
            TestConfig.xknx,
            "Office.Light_1",
            group_address_switch="1/7/4",
            group_address_switch_state="1/7/5",
            group_address_brightness="1/7/6",
            group_address_brightness_state="1/7/7",
            min_kelvin=2700,
            max_kelvin=6000,
        )

    def test_config_light_color(self):
        """Test reading Light with with dimming and color address."""
        assert TestConfig.xknx.devices["Diningroom.Light_1"] == Light(
            TestConfig.xknx,
            "Diningroom.Light_1",
            group_address_switch="1/6/4",
            group_address_brightness="1/6/6",
            group_address_color="1/6/7",
            group_address_color_state="1/6/8",
            min_kelvin=2700,
            max_kelvin=6000,
        )

    def test_config_individual_rgb(self):
        """Test reading Light with with dimming and color address."""
        expected = Light(
            TestConfig.xknx,
            "Diningroom.Light_rgb",
            group_address_switch_white="1/6/4",
            group_address_switch_white_state="1/6/5",
            group_address_brightness_white="1/6/6",
            group_address_brightness_white_state="1/6/7",
            group_address_switch_red="1/6/14",
            group_address_switch_red_state="1/6/15",
            group_address_brightness_red="1/6/16",
            group_address_brightness_red_state="1/6/17",
            group_address_switch_green="1/6/24",
            group_address_switch_green_state="1/6/25",
            group_address_brightness_green="1/6/26",
            group_address_brightness_green_state="1/6/27",
            group_address_switch_blue="1/6/34",
            group_address_switch_blue_state="1/6/35",
            group_address_brightness_blue="1/6/36",
            group_address_brightness_blue_state="1/6/37",
            min_kelvin=Light.DEFAULT_MIN_KELVIN,
            max_kelvin=Light.DEFAULT_MAX_KELVIN,
        )
        result = TestConfig.xknx.devices["Diningroom.Light_rgb"]

        print(f"result: {result} \nexpected: {expected}")
        assert result == expected

    def test_config_color_temperature(self):
        """Test reading Light with with dimming and color temperature address."""
        assert TestConfig.xknx.devices["Living-Room.Light_CT"] == Light(
            TestConfig.xknx,
            "Living-Room.Light_CT",
            group_address_switch="1/6/11",
            group_address_switch_state="1/6/10",
            group_address_brightness="1/6/12",
            group_address_brightness_state="1/6/13",
            group_address_color_temperature="1/6/14",
            group_address_color_temperature_state="1/6/15",
            min_kelvin=2700,
            max_kelvin=6000,
        )

    def test_config_tunable_white(self):
        """Test reading Light with with dimming and tunable white address."""
        assert TestConfig.xknx.devices["Living-Room.Light_TW"] == Light(
            TestConfig.xknx,
            "Living-Room.Light_TW",
            group_address_switch="1/6/21",
            group_address_switch_state="1/6/20",
            group_address_brightness="1/6/22",
            group_address_brightness_state="1/6/23",
            group_address_tunable_white="1/6/24",
            group_address_tunable_white_state="1/6/25",
            min_kelvin=2700,
            max_kelvin=6000,
        )

    def test_config_switch(self):
        """Test reading Switch from config file."""
        assert TestConfig.xknx.devices["Livingroom.Outlet_2"] == Switch(
            TestConfig.xknx, "Livingroom.Outlet_2", group_address="1/3/2"
        )

    def test_config_fan(self):
        """Test reading Fan from config file."""
        assert TestConfig.xknx.devices["Kitchen.Fan_1"] == Fan(
            TestConfig.xknx,
            "Kitchen.Fan_1",
            group_address_speed="1/3/21",
            group_address_speed_state="1/3/22",
        )

    def test_config_cover(self):
        """Test reading Cover from config file."""
        assert TestConfig.xknx.devices["Livingroom.Shutter_2"] == Cover(
            TestConfig.xknx,
            "Livingroom.Shutter_2",
            group_address_long="1/4/5",
            group_address_short="1/4/6",
            group_address_position_state="1/4/7",
            group_address_position="1/4/8",
            travel_time_down=50,
            travel_time_up=60,
        )

    def test_config_cover_device_class(self):
        """Test reading cover with device_class from config file."""
        assert TestConfig.xknx.devices["Livingroom.Shutter_3"] == Cover(
            TestConfig.xknx,
            "Livingroom.Shutter_3",
            group_address_long="1/4/9",
            group_address_short="1/4/10",
            group_address_position_state="1/4/11",
            travel_time_down=50,
            travel_time_up=60,
            device_class="shutter",
        )

    def test_config_cover_venetian(self):
        """Test reading Cover with angle from config file."""
        assert TestConfig.xknx.devices["Children.Venetian"] == Cover(
            TestConfig.xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
            group_address_position_state="1/4/17",
            group_address_position="1/4/16",
            group_address_angle="1/4/18",
            group_address_angle_state="1/4/19",
        )

    def test_config_cover_venetian_with_inverted_position(self):
        """Test reading Cover with angle from config file with inverted position/angle."""
        assert TestConfig.xknx.devices["Children.Venetian2"] == Cover(
            TestConfig.xknx,
            "Children.Venetian2",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
            group_address_position_state="1/4/17",
            group_address_position="1/4/16",
            group_address_angle="1/4/18",
            group_address_angle_state="1/4/19",
            invert_position=True,
            invert_angle=True,
        )

    def test_config_climate_temperature(self):
        """Test reading Climate object from config file."""
        assert TestConfig.xknx.devices["Kitchen.Climate"] == Climate(
            TestConfig.xknx, "Kitchen.Climate", group_address_temperature="1/7/1"
        )

    def test_config_climate_target_temperature_and_setpoint_shift(self):
        """Test reading Climate object with target_temperature_address and setpoint shift from config file."""
        assert TestConfig.xknx.devices["Children.Climate"] == Climate(
            TestConfig.xknx,
            "Children.Climate",
            group_address_temperature="1/7/2",
            group_address_target_temperature="1/7/4",
            group_address_setpoint_shift="1/7/3",
            group_address_setpoint_shift_state="1/7/14",
            temperature_step=0.5,
            setpoint_shift_min=-10,
            setpoint_shift_max=10,
        )

    def test_config_climate_operation_mode(self):
        """Test reading Climate object with operation mode in one group address from config file."""
        assert TestConfig.xknx.devices["Office.Climate"].mode == ClimateMode(
            TestConfig.xknx,
            name="Office.Climate_mode",
            group_address_operation_mode="1/7/6",
        )

    def test_config_climate_operation_mode2(self):
        """Test reading Climate object with operation mode in different group addresses  from config file."""
        assert TestConfig.xknx.devices["Attic.Climate"].mode == ClimateMode(
            TestConfig.xknx,
            name="Attic.Climate_mode",
            group_address_operation_mode_protection="1/7/8",
            group_address_operation_mode_night="1/7/9",
            group_address_operation_mode_comfort="1/7/10",
        )

    def test_config_climate_operation_mode_state(self):
        """Test reading Climate object with status address for operation mode."""
        assert TestConfig.xknx.devices["Bath.Climate"].mode == ClimateMode(
            TestConfig.xknx,
            name="Bath.Climate_mode",
            group_address_operation_mode="1/7/6",
            group_address_operation_mode_state="1/7/7",
        )

    def test_config_climate_controller_status_state(self):
        """Test reading Climate object with addresses for controller status."""
        assert TestConfig.xknx.devices["Cellar.Climate"].mode == ClimateMode(
            TestConfig.xknx,
            name="Cellar.Climate_mode",
            group_address_controller_status="1/7/12",
            group_address_controller_status_state="1/7/13",
        )

    def test_config_datetime(self):
        """Test reading DateTime objects from config file."""
        assert TestConfig.xknx.devices["General.Time"] == DateTime(
            TestConfig.xknx,
            "General.Time",
            group_address="2/1/1",
            broadcast_type="TIME",
        )
        assert TestConfig.xknx.devices["General.DateTime"] == DateTime(
            TestConfig.xknx,
            "General.DateTime",
            group_address="2/1/2",
            broadcast_type="DATETIME",
        )
        assert TestConfig.xknx.devices["General.Date"] == DateTime(
            TestConfig.xknx,
            "General.Date",
            group_address="2/1/3",
            broadcast_type="DATE",
        )

    def test_config_notification(self):
        """Test reading DateTime object from config file."""
        assert TestConfig.xknx.devices["AlarmWindow"] == Notification(
            TestConfig.xknx,
            "AlarmWindow",
            group_address="2/7/1",
            group_address_state="2/7/2",
        )

    def test_config_binary_sensor(self):
        """Test reading BinarySensor from config file."""
        assert TestConfig.xknx.devices["Livingroom.Switch_1"] == BinarySensor(
            TestConfig.xknx,
            "Livingroom.Switch_1",
            group_address_state="1/2/7",
            actions=[
                Action(TestConfig.xknx, target="Livingroom.Outlet_1", method="on"),
                Action(
                    TestConfig.xknx,
                    target="Livingroom.Outlet_2",
                    counter=2,
                    method="on",
                ),
            ],
        )

    def test_config_sensor_percent(self):
        """Test reading percent Sensor from config file."""
        assert TestConfig.xknx.devices["Heating.Valve1"] == Sensor(
            TestConfig.xknx,
            "Heating.Valve1",
            group_address_state="2/0/0",
            value_type="percent",
            sync_state=True,
        )

    def test_config_sensor_percent_passive(self):
        """Test passive percent Sensor from config file."""
        assert TestConfig.xknx.devices["Heating.Valve2"] == Sensor(
            TestConfig.xknx,
            "Heating.Valve2",
            group_address_state="2/0/1",
            value_type="percent",
            sync_state=False,
        )

    def test_config_sensor_temperature_type(self):
        """Test reading temperature Sensor from config file."""
        assert TestConfig.xknx.devices["Kitchen.Temperature"] == Sensor(
            TestConfig.xknx,
            "Kitchen.Temperature",
            group_address_state="2/0/2",
            value_type="temperature",
        )

    def test_config_expose_sensor(self):
        """Test reading ExposeSensor from config file."""
        assert TestConfig.xknx.devices["Outside.Temperature"] == ExposeSensor(
            TestConfig.xknx,
            "Outside.Temperature",
            group_address="2/0/3",
            value_type="temperature",
        )

    def test_config_sensor_binary_device_class(self):
        """Test reading Sensor with device_class from config file."""
        assert TestConfig.xknx.devices["Kitchen.Motion.Sensor"] == BinarySensor(
            TestConfig.xknx,
            "Kitchen.Motion.Sensor",
            group_address_state="3/0/0",
            device_class="motion",
        )

    def test_config_sensor_binary_passive(self):
        """Test reading Sensor with sync_state False from config file."""
        assert TestConfig.xknx.devices["DiningRoom.Motion.Sensor"] == BinarySensor(
            TestConfig.xknx,
            "DiningRoom.Motion.Sensor",
            group_address_state="3/0/1",
            sync_state=False,
            device_class="motion",
        )

    def test_config_scene(self):
        """Test reading Scene from config file."""
        assert TestConfig.xknx.devices["Romantic"] == Scene(
            TestConfig.xknx, "Romantic", group_address="7/0/1", scene_number=23
        )

    def test_config_weather(self):
        """Test reading weather from config file."""
        assert TestConfig.xknx.devices["Remote"] == Weather(
            TestConfig.xknx,
            "Remote",
            group_address_temperature="7/0/0",
            group_address_brightness_south="7/0/1",
            group_address_brightness_west="7/0/2",
            group_address_brightness_east="7/0/3",
            group_address_wind_speed="7/0/4",
            group_address_wind_bearing="7/0/5",
            group_address_rain_alarm="7/0/6",
            group_address_frost_alarm="7/0/7",
            group_address_wind_alarm="7/0/8",
            group_address_day_night="7/0/9",
            group_address_air_pressure="7/0/10",
            group_address_humidity="7/0/11",
            create_sensors=False,
            sync_state=True,
        )

    def test_config_weather_create_sensor(self):
        """Test reading weather from config file."""
        assert isinstance(TestConfig.xknx.devices["Home_temperature"], Sensor)
        assert isinstance(TestConfig.xknx.devices["Home_wind_alarm"], BinarySensor)
        assert not TestConfig.xknx.devices.__contains__("Remote_wind_alarm")

    def test_config_file_error(self):
        """Test error message when reading an errornous config file."""
        with patch("logging.Logger.error") as mock_err, patch(
            "xknx.config.ConfigV1.parse_group_light"
        ) as mock_parse:
            mock_parse.side_effect = XKNXException()
            XKNX(config="xknx.yaml")
            assert mock_err.call_count == 1

    XKNX_GENERAL_OWN_ADDRESS = "1.2.3"
    XKNX_GENERAL_RATE_LIMIT = "20"
    XKNX_GENERAL_MULTICAST_GROUP = "1.2.3.4"
    XKNX_GENERAL_MULTICAST_PORT = "1111"

    def test_config_general_from_env(self):
        os.environ["XKNX_GENERAL_OWN_ADDRESS"] = self.XKNX_GENERAL_OWN_ADDRESS
        os.environ["XKNX_GENERAL_RATE_LIMIT"] = self.XKNX_GENERAL_RATE_LIMIT
        os.environ["XKNX_GENERAL_MULTICAST_GROUP"] = self.XKNX_GENERAL_MULTICAST_GROUP
        os.environ["XKNX_GENERAL_MULTICAST_PORT"] = self.XKNX_GENERAL_MULTICAST_PORT
        self.xknx = XKNX(config="xknx.yaml")
        del os.environ["XKNX_GENERAL_OWN_ADDRESS"]
        del os.environ["XKNX_GENERAL_RATE_LIMIT"]
        del os.environ["XKNX_GENERAL_MULTICAST_GROUP"]
        del os.environ["XKNX_GENERAL_MULTICAST_PORT"]
        assert str(self.xknx.own_address) == self.XKNX_GENERAL_OWN_ADDRESS
        assert self.xknx.rate_limit == int(self.XKNX_GENERAL_RATE_LIMIT)
        assert self.xknx.multicast_group == self.XKNX_GENERAL_MULTICAST_GROUP
        assert self.xknx.multicast_port == int(self.XKNX_GENERAL_MULTICAST_PORT)

    XKNX_CONNECTION_GATEWAY_IP = "192.168.12.34"
    XKNX_CONNECTION_GATEWAY_PORT = "1234"
    XKNX_CONNECTION_LOCAL_IP = "192.168.11.11"
    XKNX_CONNECTION_ROUTE_BACK = "true"

    def test_config_cnx_from_env(self):
        os.environ["XKNX_CONNECTION_GATEWAY_IP"] = self.XKNX_CONNECTION_GATEWAY_IP
        os.environ["XKNX_CONNECTION_GATEWAY_PORT"] = self.XKNX_CONNECTION_GATEWAY_PORT
        os.environ["XKNX_CONNECTION_LOCAL_IP"] = self.XKNX_CONNECTION_LOCAL_IP
        os.environ["XKNX_CONNECTION_ROUTE_BACK"] = self.XKNX_CONNECTION_ROUTE_BACK
        self.xknx = XKNX(config="xknx.yaml")
        del os.environ["XKNX_CONNECTION_GATEWAY_IP"]
        del os.environ["XKNX_CONNECTION_GATEWAY_PORT"]
        del os.environ["XKNX_CONNECTION_LOCAL_IP"]
        del os.environ["XKNX_CONNECTION_ROUTE_BACK"]
        assert self.xknx.connection_config.gateway_ip == self.XKNX_CONNECTION_GATEWAY_IP
        assert self.xknx.connection_config.gateway_port == int(
            self.XKNX_CONNECTION_GATEWAY_PORT
        )
        assert self.xknx.connection_config.local_ip == self.XKNX_CONNECTION_LOCAL_IP
        assert self.xknx.connection_config.route_back == bool(
            self.XKNX_CONNECTION_ROUTE_BACK
        )

    def test_config_cnx_route_back(self):
        os.environ["XKNX_CONNECTION_ROUTE_BACK"] = "true"
        self.xknx = XKNX(config="xknx.yaml")
        del os.environ["XKNX_CONNECTION_ROUTE_BACK"]
        assert self.xknx.connection_config.route_back is True
        os.environ["XKNX_CONNECTION_ROUTE_BACK"] = "yes"
        self.xknx = XKNX(config="xknx.yaml")
        del os.environ["XKNX_CONNECTION_ROUTE_BACK"]
        assert self.xknx.connection_config.route_back is True
        os.environ["XKNX_CONNECTION_ROUTE_BACK"] = "1"
        self.xknx = XKNX(config="xknx.yaml")
        del os.environ["XKNX_CONNECTION_ROUTE_BACK"]
        assert self.xknx.connection_config.route_back is True
        os.environ["XKNX_CONNECTION_ROUTE_BACK"] = "on"
        self.xknx = XKNX(config="xknx.yaml")
        del os.environ["XKNX_CONNECTION_ROUTE_BACK"]
        assert self.xknx.connection_config.route_back is True
        os.environ["XKNX_CONNECTION_ROUTE_BACK"] = "y"
        self.xknx = XKNX(config="xknx.yaml")
        del os.environ["XKNX_CONNECTION_ROUTE_BACK"]
        assert self.xknx.connection_config.route_back is True
        if "XKNX_CONNECTION_ROUTE_BACK" in os.environ:
            del os.environ["XKNX_CONNECTION_ROUTE_BACK"]
        self.xknx = XKNX(config="xknx.yaml")
        assert self.xknx.connection_config.route_back is False
        os.environ["XKNX_CONNECTION_ROUTE_BACK"] = "another_string"
        self.xknx = XKNX(config="xknx.yaml")
        del os.environ["XKNX_CONNECTION_ROUTE_BACK"]
        assert self.xknx.connection_config.route_back is False
        os.environ["XKNX_CONNECTION_ROUTE_BACK"] = ""
        self.xknx = XKNX(config="xknx.yaml")
        del os.environ["XKNX_CONNECTION_ROUTE_BACK"]
        assert self.xknx.connection_config.route_back is False
