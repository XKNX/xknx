"""
Module for reading configfiles (xknx.yaml).

* it will parse the given file
* and add the found devices to the devies vector of XKNX.
"""

import yaml

from xknx.devices import (BinarySensor, Climate, Cover, DateTime, ExposeSensor,
                          Light, Notification, Scene, Sensor, Switch)
from xknx.exceptions import XKNXException
from xknx.knx import PhysicalAddress


class Config:
    """Class for parsing xknx.yaml."""

    def __init__(self, xknx):
        """Initialize Config class."""
        self.xknx = xknx

    def read(self, file='xknx.yaml'):
        """Read config."""
        self.xknx.logger.debug("Reading %s", file)
        try:
            with open(file, 'r') as filehandle:
                doc = yaml.load(filehandle)
                self.parse_general(doc)
                self.parse_groups(doc)
        except FileNotFoundError as ex:
            self.xknx.logger.error("Error while reading %s: %s", file, ex)

    def parse_general(self, doc):
        """Parse the general section of xknx.yaml."""
        if "general" in doc:
            if "own_address" in doc["general"]:
                self.xknx.own_address = \
                    PhysicalAddress(doc["general"]["own_address"])

    def parse_groups(self, doc):
        """Parse the group section of xknx.yaml."""
        for group in doc["groups"]:
            self.parse_group(doc, group)

    def parse_group(self, doc, group):
        """Parse a group entry of xknx.yaml."""
        try:
            if group.startswith("light"):
                self.parse_group_light(doc["groups"][group])
            elif group.startswith("switch"):
                self.parse_group_switch(doc["groups"][group])
            elif group.startswith("cover"):
                self.parse_group_cover(doc["groups"][group])
            elif group.startswith("climate"):
                self.parse_group_climate(doc["groups"][group])
            elif group.startswith("datetime"):
                self.parse_group_datetime(doc["groups"][group])
            elif group.startswith("sensor"):
                self.parse_group_sensor(doc["groups"][group])
            elif group.startswith("expose_sensor"):
                self.parse_group_expose_sensor(doc["groups"][group])
            elif group.startswith("binary_sensor"):
                self.parse_group_binary_sensor(doc["groups"][group])
            elif group.startswith("notification"):
                self.parse_group_notification(doc["groups"][group])
            elif group.startswith("scene"):
                self.parse_group_scene(doc["groups"][group])
        except XKNXException as ex:
            self.xknx.logger.error("Error while reading config file: Could not parse %s: %s", group, ex)

    def parse_group_light(self, entries):
        """Parse a light section of xknx.yaml."""
        for entry in entries:
            light = Light.from_config(
                self.xknx,
                entry,
                entries[entry])
            self.xknx.devices.add(light)

    def parse_group_switch(self, entries):
        """Parse a switch section of xknx.yaml."""
        for entry in entries:
            switch = Switch.from_config(
                self.xknx,
                entry,
                entries[entry])
            self.xknx.devices.add(switch)

    def parse_group_binary_sensor(self, entries):
        """Parse a binary_sensor section of xknx.yaml."""
        for entry in entries:
            binary_sensor = BinarySensor.from_config(
                self.xknx,
                entry,
                entries[entry])
            self.xknx.devices.add(binary_sensor)

    def parse_group_cover(self, entries):
        """Parse a cover section of xknx.yaml."""
        for entry in entries:
            cover = Cover.from_config(
                self.xknx,
                entry,
                entries[entry])
            self.xknx.devices.add(cover)

    def parse_group_climate(self, entries):
        """Parse a climate section of xknx.yaml."""
        for entry in entries:
            climate = Climate.from_config(
                self.xknx,
                entry,
                entries[entry])
            self.xknx.devices.add(climate)

    def parse_group_datetime(self, entries):
        """Parse a datetime section of xknx.yaml."""
        for entry in entries:
            datetime = DateTime.from_config(
                self.xknx,
                entry,
                entries[entry])
            self.xknx.devices.add(datetime)

    def parse_group_sensor(self, entries):
        """Parse a sensor section of xknx.yaml."""
        for entry in entries:
            sensor = Sensor.from_config(
                self.xknx,
                entry,
                entries[entry])
            self.xknx.devices.add(sensor)

    def parse_group_expose_sensor(self, entries):
        """Parse a exposed sensor section of xknx.yaml."""
        for entry in entries:
            expose_sensor = ExposeSensor.from_config(
                self.xknx,
                entry,
                entries[entry])
            self.xknx.devices.add(expose_sensor)

    def parse_group_notification(self, entries):
        """Parse a sensor section of xknx.yaml."""
        for entry in entries:
            notification = Notification.from_config(
                self.xknx,
                entry,
                entries[entry])
            self.xknx.devices.add(notification)

    def parse_group_scene(self, entries):
        """Parse a scene section of xknx.yaml."""
        for entry in entries:
            scene = Scene.from_config(
                self.xknx,
                entry,
                entries[entry])
            self.xknx.devices.add(scene)
