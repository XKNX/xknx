"""
Module for reading config files (xknx.yaml).

* it will parse the given file
* and add the found devices to the devies vector of XKNX.
"""
from enum import Enum
import logging
import os
from typing import TYPE_CHECKING, Any, Dict

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

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Version(Enum):
    """The used xknx.yaml structure version."""

    VERSION_1 = 1
    VERSION_2 = 2


class ConfigV1:
    """Use old config style."""

    def __init__(self, xknx: "XKNX") -> None:
        """Initialize Config class."""
        self.xknx = xknx

    def parse(self, doc: Dict[str, Any]) -> None:
        """Parse the config and read ENV vars."""
        self.parse_general(doc)
        self.parse_connection(doc)
        self.parse_groups(doc)
        self.env_general()
        self.env_connection()

    def parse_general(self, doc: Dict[str, Any]) -> None:
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

    def env_general(self) -> None:
        """Get Env Vars for the general section."""
        own_address = os.getenv("XKNX_GENERAL_OWN_ADDRESS", default=None)
        if own_address:
            logger.debug("XKNX_GENERAL_OWN_ADDRESS overwrite from env")
            self.xknx.own_address = IndividualAddress(own_address)
        rate_limit = os.getenv("XKNX_GENERAL_RATE_LIMIT", default=None)
        if rate_limit:
            logger.debug("XKNX_GENERAL_RATE_LIMIT overwrite from env")
            self.xknx.rate_limit = int(rate_limit)
        multicast_group = os.getenv("XKNX_GENERAL_MULTICAST_GROUP", default=None)
        if multicast_group:
            logger.debug("XKNX_GENERAL_MULTICAST_GROUP overwrite from env")
            self.xknx.multicast_group = multicast_group
        multicast_port = os.getenv("XKNX_GENERAL_MULTICAST_PORT", default=None)
        if multicast_port:
            logger.debug("XKNX_GENERAL_MULTICAST_PORT overwrite from env")
            self.xknx.multicast_port = int(multicast_port)

    def parse_connection(self, doc: Dict[str, Any]) -> None:
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

    def _parse_connection_prefs(
        self, conn_type: ConnectionType, prefs: Dict[str, Any]
    ) -> None:
        connection_config = ConnectionConfig(connection_type=conn_type)
        if hasattr(prefs, "__iter__"):
            for pref, value in prefs.items():
                if pref == "gateway_ip":
                    connection_config.gateway_ip = value
                elif pref == "gateway_port":
                    connection_config.gateway_port = value
                elif pref == "local_ip":
                    connection_config.local_ip = value
                elif pref == "route_back":
                    connection_config.route_back = value
        self.xknx.connection_config = connection_config

    def env_connection(self) -> None:
        """Read config from env vars."""
        gateway_ip = os.getenv("XKNX_CONNECTION_GATEWAY_IP", default=None)
        if gateway_ip:
            logger.debug("XKNX_CONNECTION_GATEWAY_IP overwrite from env")
            self.xknx.connection_config.gateway_ip = gateway_ip
        gateway_port = os.getenv("XKNX_CONNECTION_GATEWAY_PORT", default=None)
        if gateway_port:
            logger.debug("XKNX_CONNECTION_GATEWAY_PORT overwrite from env")
            self.xknx.connection_config.gateway_port = int(gateway_port)
        local_ip = os.getenv("XKNX_CONNECTION_LOCAL_IP", default=None)
        if local_ip:
            logger.debug("XKNX_CONNECTION_LOCAL_IP overwrite from env")
            self.xknx.connection_config.local_ip = local_ip
        route_back = os.getenv("XKNX_CONNECTION_ROUTE_BACK", default=None)
        if route_back:
            logger.debug("XKNX_CONNECTION_ROUTE_BACK overwrite from env")
            self.xknx.connection_config.route_back = route_back.lower() in [
                "true",
                "1",
                "y",
                "yes",
                "on",
            ]

    def parse_groups(self, doc: Dict[str, Any]) -> None:
        """Parse the group section of xknx.yaml."""
        if "groups" in doc and hasattr(doc["groups"], "__iter__"):
            for group in doc["groups"]:
                self.parse_group(doc, group)

    # pylint: disable=too-many-branches
    def parse_group(self, doc: Dict[str, Any], group: str) -> None:
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

    def parse_group_binary_sensor(self, entries: Dict[str, Any]) -> None:
        """Parse a binary_sensor section of xknx.yaml."""
        for entry in entries:
            BinarySensor.from_config(self.xknx, entry, entries[entry])

    def parse_group_climate(self, entries: Dict[str, Any]) -> None:
        """Parse a climate section of xknx.yaml."""
        for entry in entries:
            Climate.from_config(self.xknx, entry, entries[entry])

    def parse_group_cover(self, entries: Dict[str, Any]) -> None:
        """Parse a cover section of xknx.yaml."""
        for entry in entries:
            Cover.from_config(self.xknx, entry, entries[entry])

    def parse_group_datetime(self, entries: Dict[str, Any]) -> None:
        """Parse a datetime section of xknx.yaml."""
        for entry in entries:
            DateTime.from_config(self.xknx, entry, entries[entry])

    def parse_group_expose_sensor(self, entries: Dict[str, Any]) -> None:
        """Parse a exposed sensor section of xknx.yaml."""
        for entry in entries:
            ExposeSensor.from_config(self.xknx, entry, entries[entry])

    def parse_group_fan(self, entries: Dict[str, Any]) -> None:
        """Parse a fan section of xknx.yaml."""
        for entry in entries:
            Fan.from_config(self.xknx, entry, entries[entry])

    def parse_group_light(self, entries: Dict[str, Any]) -> None:
        """Parse a light section of xknx.yaml."""
        for entry in entries:
            Light.from_config(self.xknx, entry, entries[entry])

    def parse_group_notification(self, entries: Dict[str, Any]) -> None:
        """Parse a sensor section of xknx.yaml."""
        for entry in entries:
            Notification.from_config(self.xknx, entry, entries[entry])

    def parse_group_scene(self, entries: Dict[str, Any]) -> None:
        """Parse a scene section of xknx.yaml."""
        for entry in entries:
            Scene.from_config(self.xknx, entry, entries[entry])

    def parse_group_sensor(self, entries: Dict[str, Any]) -> None:
        """Parse a sensor section of xknx.yaml."""
        for entry in entries:
            Sensor.from_config(self.xknx, entry, entries[entry])

    def parse_group_switch(self, entries: Dict[str, Any]) -> None:
        """Parse a switch section of xknx.yaml."""
        for entry in entries:
            Switch.from_config(self.xknx, entry, entries[entry])

    def parse_group_weather(self, entries: Dict[str, Any]) -> None:
        """Parse a weather section of xknx.yaml."""
        for entry in entries:
            Weather.from_config(self.xknx, entry, entries[entry])
