"""
Module for reading config files (xknx.yaml).

* it will parse the given file
* and add the found devices to the devies vector of XKNX.
"""
from enum import Enum
import logging

from xknx.devices import (
    BinarySensor,
    Climate,
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

logger = logging.getLogger("xknx.log")


class Version(Enum):
    """The used xknx.yaml structure version."""

    VERSION_1 = 1
    VERSION_2 = 2


class ConfigV1:
    """Use old config style."""

    def __init__(self, xknx):
        """Initialize Config class."""
        self.xknx = xknx

    def parse(self, doc):
        """Parse the config."""
        self.parse_general(doc)
        self.parse_connection(doc)
        self.parse_groups(doc)

    def parse_general(self, doc):
        """Parse the general section of xknx.yaml."""
        if "general" in doc:
            if "own_address" in doc["general"]:
                self.xknx.own_address = IndividualAddress(doc["general"]["own_address"])
            if "rate_limit" in doc["general"]:
                self.xknx.rate_limit = doc["general"]["rate_limit"]
            if "multicast_group" in doc["general"]:
                self.xknx.multicast_group = doc["general"]["multicast_group"]
            if "multicast_port" in doc["general"]:
                self.xknx.multicast_port = doc["general"]["multicast_port"]

    def parse_connection(self, doc):
        """Parse the connection section of xknx.yaml."""
        if "connection" in doc and hasattr(doc["connection"], "__iter__"):
            for conn, prefs in doc["connection"].items():
                try:
                    if conn == "tunneling":
                        if prefs is None or "gateway_ip" not in prefs:
                            raise XKNXException(
                                "`gateway_ip` is required for tunneling connection."
                            )
                        conn_type = ConnectionType.TUNNELING
                    elif conn == "routing":
                        conn_type = ConnectionType.ROUTING
                    else:
                        conn_type = ConnectionType.AUTOMATIC
                    self._parse_connection_prefs(conn_type, prefs)
                except XKNXException as ex:
                    logger.error(
                        "Error while reading config file: Could not parse %s: %s",
                        conn,
                        ex,
                    )
                    raise ex

    def _parse_connection_prefs(self, conn_type: ConnectionType, prefs) -> None:
        connection_config = ConnectionConfig(connection_type=conn_type)
        if hasattr(prefs, "__iter__"):
            for pref, value in prefs.items():
                if pref == "gateway_ip":
                    connection_config.gateway_ip = value
                elif pref == "gateway_port":
                    connection_config.gateway_port = value
                elif pref == "local_ip":
                    connection_config.local_ip = value
        self.xknx.connection_config = connection_config

    def parse_groups(self, doc):
        """Parse the group section of xknx.yaml."""
        if "groups" in doc and hasattr(doc["groups"], "__iter__"):
            for group in doc["groups"]:
                self.parse_group(doc, group)

    # pylint: disable=too-many-branches
    def parse_group(self, doc, group):
        """Parse a group entry of xknx.yaml."""
        try:
            if group.startswith("binary_sensor"):
                self.parse_group_binary_sensor(doc["groups"][group])
            elif group.startswith("climate"):
                self.parse_group_climate(doc["groups"][group])
            elif group.startswith("cover"):
                self.parse_group_cover(doc["groups"][group])
            elif group.startswith("datetime"):
                self.parse_group_datetime(doc["groups"][group])
            elif group.startswith("expose_sensor"):
                self.parse_group_expose_sensor(doc["groups"][group])
            elif group.startswith("fan"):
                self.parse_group_fan(doc["groups"][group])
            elif group.startswith("light"):
                self.parse_group_light(doc["groups"][group])
            elif group.startswith("notification"):
                self.parse_group_notification(doc["groups"][group])
            elif group.startswith("scene"):
                self.parse_group_scene(doc["groups"][group])
            elif group.startswith("sensor"):
                self.parse_group_sensor(doc["groups"][group])
            elif group.startswith("switch"):
                self.parse_group_switch(doc["groups"][group])
            elif group.startswith("weather"):
                self.parse_group_weather(doc["groups"][group])
        except XKNXException as ex:
            logger.error(
                "Error while reading config file: Could not parse %s: %s", group, ex
            )

    def parse_group_binary_sensor(self, entries):
        """Parse a binary_sensor section of xknx.yaml."""
        for entry in entries:
            BinarySensor.from_config(self.xknx, entry, entries[entry])

    def parse_group_climate(self, entries):
        """Parse a climate section of xknx.yaml."""
        for entry in entries:
            Climate.from_config(self.xknx, entry, entries[entry])

    def parse_group_cover(self, entries):
        """Parse a cover section of xknx.yaml."""
        for entry in entries:
            Cover.from_config(self.xknx, entry, entries[entry])

    def parse_group_datetime(self, entries):
        """Parse a datetime section of xknx.yaml."""
        for entry in entries:
            DateTime.from_config(self.xknx, entry, entries[entry])

    def parse_group_expose_sensor(self, entries):
        """Parse a exposed sensor section of xknx.yaml."""
        for entry in entries:
            ExposeSensor.from_config(self.xknx, entry, entries[entry])

    def parse_group_fan(self, entries):
        """Parse a fan section of xknx.yaml."""
        for entry in entries:
            Fan.from_config(self.xknx, entry, entries[entry])

    def parse_group_light(self, entries):
        """Parse a light section of xknx.yaml."""
        for entry in entries:
            Light.from_config(self.xknx, entry, entries[entry])

    def parse_group_notification(self, entries):
        """Parse a sensor section of xknx.yaml."""
        for entry in entries:
            Notification.from_config(self.xknx, entry, entries[entry])

    def parse_group_scene(self, entries):
        """Parse a scene section of xknx.yaml."""
        for entry in entries:
            Scene.from_config(self.xknx, entry, entries[entry])

    def parse_group_sensor(self, entries):
        """Parse a sensor section of xknx.yaml."""
        for entry in entries:
            Sensor.from_config(self.xknx, entry, entries[entry])

    def parse_group_switch(self, entries):
        """Parse a switch section of xknx.yaml."""
        for entry in entries:
            Switch.from_config(self.xknx, entry, entries[entry])

    def parse_group_weather(self, entries):
        """Parse a weather section of xknx.yaml."""
        for entry in entries:
            Weather.from_config(self.xknx, entry, entries[entry])
