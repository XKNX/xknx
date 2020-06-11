"""
Module for reading configfiles (xknx.yaml).

* it will parse the given file
* and add the found devices to the devies vector of XKNX.
"""

import yaml

from xknx.devices import device_types
from xknx.exceptions import XKNXException
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import PhysicalAddress


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
                doc = yaml.safe_load(filehandle)
                self.parse_general(doc)
                self.parse_connection(doc)
                self.parse_groups(doc)
        except FileNotFoundError as ex:
            self.xknx.logger.error("Error while reading %s: %s", file, ex)

    def parse_general(self, doc):
        """Parse the general section of xknx.yaml."""
        if "general" in doc:
            if "own_address" in doc["general"]:
                self.xknx.own_address = \
                    PhysicalAddress(doc["general"]["own_address"])
            if "rate_limit" in doc["general"]:
                self.xknx.rate_limit = \
                    doc["general"]["rate_limit"]

    def parse_connection(self, doc):
        """Parse the connection section of xknx.yaml."""
        if "connection" in doc \
                and hasattr(doc["connection"], '__iter__'):
            for conn, prefs in doc["connection"].items():
                try:
                    if conn == "tunneling":
                        conn_type = ConnectionType.TUNNELING
                    elif conn == "routing":
                        conn_type = ConnectionType.ROUTING
                    else:
                        conn_type = ConnectionType.AUTOMATIC
                    self._parse_connection_prefs(conn_type, prefs)
                except XKNXException as ex:
                    self.xknx.logger.error("Error while reading config file: Could not parse %s: %s", conn, ex)
                    raise ex

    def _parse_connection_prefs(self, conn_type: ConnectionType, prefs) -> None:
        connection_config = ConnectionConfig(connection_type=conn_type)
        if hasattr(prefs, '__iter__'):
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
        if "groups" in doc \
                and hasattr(doc["groups"], '__iter__'):
            for group in doc["groups"]:
                self.parse_group(doc, group)

    def parse_group(self, doc, group):
        """Parse a group entry of xknx.yaml."""
        entries = doc['groups'][group]
        try:
            for name,cls in device_types.items():
                if group.startswith(name):
                    self.parse_cls(cls, entries)
                    return
            self.xknx.logger.error("Error while reading config file: Unknown device type for %s", group)

        except XKNXException as ex:
            self.xknx.logger.error("Error while reading config file: Could not parse %s: %s", group, ex)

    def parse_cls(self, cls, entries):
        for name,entry in entries.items():
            dev = cls.from_config(self.xknx, name, entry)
            dev.add_to_xknx()

