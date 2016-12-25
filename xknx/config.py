import yaml
from .xknx import XKNX
from .address import Address
from .binaryoutput import BinaryOutput
from .binaryinput import BinaryInput
from .device import Device
from .switch import Switch
from .thermostat import Thermostat
from .dimmer import Dimmer
from .outlet import Outlet
from .shutter import Shutter
from .devices import Devices
from .address import Address,AddressType
from .globals import Globals
import time


class Config:

    def __init__(self, xknx):
        self.xknx = xknx

    def read( self, file='xknx.yaml'):
        print("Reading {0}".format(file))
        with open(file, 'r') as f:
            doc = yaml.load(f)
            self.parse_general(doc)
            self.parse_groups(doc)

    def parse_general(seif, doc):
        if "general" in doc:
            if "own_address" in doc["general"]:
                Globals.set_own_address(Address(doc["general"]["own_address"],AddressType.PHYSICAL))
            if "own_ip" in doc["general"]:
                Globals.set_own_ip(doc["general"]["own_ip"])

    def parse_groups(self, doc):
        for group in doc["groups"]:
            if group.startswith("dimmer"):
                for entry in doc["groups"][group]:
                    dimmer = Dimmer(self.xknx, entry, doc["groups"][group][entry])
                    self.xknx.devices.devices.append(dimmer)
            if group.startswith("outlet"):
                for entry in doc["groups"][group]:
                    outlet = Outlet(self.xknx, entry, doc["groups"][group][entry])
                    self.xknx.devices.devices.append(outlet)
            if group.startswith("switch"):
                for entry in doc["groups"][group]:
                    switch = Switch(self.xknx, entry, doc["groups"][group][entry])
                    self.xknx.devices.devices.append(switch)
            if group.startswith("shutter"):
                for entry in doc["groups"][group]:
                    shutter = Shutter(self.xknx, entry, doc["groups"][group][entry])
                    self.xknx.devices.devices.append(shutter)

            if group.startswith("thermostat"):
                for entry in doc["groups"][group]:
                    thermostat = Thermostat(self.xknx, entry, doc["groups"][group][entry])
                    self.xknx.devices.devices.append(thermostat)
