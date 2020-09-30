"""Unit test for schema validation."""
import glob
import os
from typing import List
import unittest

from pytest import raises
import voluptuous as vol
from xknx.config import (
    BinarySensorSchema,
    ClimateSchema,
    ConnectionSchema,
    CoverSchema,
    DateTimeSchema,
    ExposeSchema,
    FanSchema,
    LightSchema,
    NotificationSchema,
    SceneSchema,
    SensorSchema,
    SwitchSchema,
    WeatherSchema,
    XKNXSchema,
)
import yaml

TEST_CONFIG_PATH = "test/config_tests/resources"

CONFIG_MAPPING = [
    ("binary_sensor", BinarySensorSchema.SCHEMA),
    ("climate", ClimateSchema.SCHEMA),
    ("connection", ConnectionSchema.SCHEMA),
    ("cover", CoverSchema.SCHEMA),
    ("datetime", DateTimeSchema.SCHEMA),
    ("expose", ExposeSchema.SCHEMA),
    ("fan", FanSchema.SCHEMA),
    ("light", LightSchema.SCHEMA),
    ("notification", NotificationSchema.SCHEMA),
    ("scene", SceneSchema.SCHEMA),
    ("sensor", SensorSchema.SCHEMA),
    ("switch", SwitchSchema.SCHEMA),
    ("weather", WeatherSchema.SCHEMA),
    ("xknx", XKNXSchema.SCHEMA),
]


# pylint: disable=too-many-public-methods,invalid-name
class TestSchema(unittest.TestCase):
    """Test class for Schema logic."""

    #
    # Get files in directory
    #
    @staticmethod
    def get_files(directory, valid=False) -> List:
        file_pattern = "invalid" if not valid else "valid"

        _list: List = glob.glob(
            f"{TEST_CONFIG_PATH}{os.sep}{directory}{os.sep}{file_pattern}*.yaml"
        )
        result = []
        for file in _list:
            with open(file) as filehandle:
                config = yaml.safe_load(filehandle)
                matcher = config.get("name", ".*")
                result.append((file, config, matcher))

        return result

    #
    # Test all valid schemas in the resources directory.
    #
    def test_schema_valid(self):
        """Test valid schemas from config file."""

        for entry, schema in CONFIG_MAPPING:
            _list = TestSchema.get_files(entry, True)
            for file, config, matcher in _list:
                #  print(f"Testing {file} from {entry}.")
                self.assertIsNotNone(schema(config))

    #
    # Test all invalid schemas in the resources directory
    #
    def test_schema_invalid(self):
        """Test invalid schemas from config file."""

        for entry, schema in CONFIG_MAPPING:
            _list = TestSchema.get_files(entry)
            for file, config, matches in _list:
                with raises(vol.Invalid, match=matches):
                    print(f"Testing {file} from {entry}.")
                    schema(config)
