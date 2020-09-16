"""Unit test for schema validation."""
import unittest

import voluptuous as vol
from xknx.config import BinarySensorSchema
import yaml


# pylint: disable=too-many-public-methods,invalid-name
class TestSchema(unittest.TestCase):
    """Test class for Schema logic."""

    #
    # Binary Sensor Test
    #
    def test_binary_sensor_schema_valid(self):
        """Test binary sensor section from config file."""

        # Replaces setting from xknx.yaml
        test_configs = [
            """
        name: "test_complete"
        friendly_name: ""
        address:
            state_address: "1/2/7"
            state_update: "expire 60"
            passive_state_addresses: ["8/8/8"]
        context_timeout: 1
        device_class: 'light'
        reset_after: 3000 # ms
        ignore_internal_state: False
        """,
            """
                   name: "test_no_friendly_name"
                   address:
                       state_address: "1/2/7"
                       state_update: "expire 60"
                       passive_state_addresses:
                   context_timeout: 1
                   device_class: 'light'
                   reset_after: 3000 # ms
                   ignore_internal_state: 0
                   """,
            """
                   name: "test_minimal"
                   friendly_name: ""
                   address:
                       state_address: "1/2/7"
                   ignore_internal_state: "on"
                   """,
            """
                   name: "livingroom_switch1"
                   friendly_name: ""
                   address:
                       state_address: "1/2/7"
                       state_update: "expire 60"
                       passive_state_addresses: ["8/8/8"]
                   context_timeout: 1
                   device_class: 'light'
                   reset_after: 3000 # ms
                   ignore_internal_state: "off"
                   """,
        ]
        for yaml_string in test_configs:
            config = yaml.safe_load(yaml_string)
            self.assertIsNotNone(BinarySensorSchema.SCHEMA(config))

    #
    # Binary Sensor Invalid Test
    #
    def test_binary_sensor_invalid(self):
        """Test binary sensor section from config file."""

        # Replaces setting from xknx.yaml
        test_configs = [
            """
        name: "test_complete"
        friendly_name: ""
        address:
            address: "2/2/2"
            state_update: "expire 60"
            passive_state_addresses: ["8/8/8"]
        context_timeout: 1
        device_class: 'light'
        reset_after: 3000 # ms
        ignore_internal_state: False
        """,
            """
                   name: "test_no_friendly_name"
                   context_timeout: 1
                   device_class: 'light'
                   reset_after: 3000 # ms
                   ignore_internal_state: False
                   """,
            """
                   name: "test_minimal"
                   friendly_name:
                   address:
                   """,
            """
                   name: "livingroom_switch1"
                   friendly_name: ["teer"]
                   address:
                       state_update: "expire 60"
                   """,
            """
                               name: "livingroom_switch1"
                               friendly_name: ""
                               address:
                                   state_address: "2/2/2/2"
                                   state_update: "expire 60"
                               """,
        ]
        for yaml_string in test_configs:
            config = yaml.safe_load(yaml_string)
            self.assertRaises(vol.Invalid, BinarySensorSchema.SCHEMA, config)
