import yaml
from .address import Address
from .binaryoutput import BinaryOutput
from .binaryinput import BinaryInput
from .device import Device
from .switch import Switch
from .dimmer import Dimmer
from .outlet import Outlet
from .shutter import Shutter
from .devices import Devices,devices_
from .globals import Globals
import time


class Config:

    @staticmethod
    def read( file='xknx.yaml'):
        print("Reading {0}".format(file))
        with open(file, 'r') as f:
            doc = yaml.load(f)
            Config.parse_general(doc)
            Config.parse_groups(doc)

    @staticmethod
    def parse_general(doc):
        if "general" in doc:
            if "own_address" in doc["general"]:
                Globals.set_own_address(doc["general"]["own_address"])
            if "own_ip" in doc["general"]:
                Globals.set_own_ip(doc["general"]["own_ip"])

    @staticmethod
    def parse_groups(doc):
        for group in doc["groups"]:
            if group.startswith("dimmer"):
                for entry in doc["groups"][group]:
                    dimmer = Dimmer(entry, doc["groups"][group][entry])
                    devices_.devices.append(dimmer)
            if group.startswith("outlet"):
                for entry in doc["groups"][group]:
                    outlet = Outlet(entry, doc["groups"][group][entry])
                    devices_.devices.append(outlet)
            if group.startswith("switch"):
                for entry in doc["groups"][group]:
                    switch = Switch(entry, doc["groups"][group][entry])
                    devices_.devices.append(switch)
            if group.startswith("shutter"):
                for entry in doc["groups"][group]:
                    shutter = Shutter(entry, doc["groups"][group][entry])
                    devices_.devices.append(shutter)

