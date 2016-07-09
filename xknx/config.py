import yaml
from .address import Address
from .binaryoutput import BinaryOutput
from .binaryinput import BinaryInput
from .device import Device
from .switch import Switch
from .dimmer import Dimmer
from .outlet import Outlet
from .shutter import Shutter
from .nameresolver import NameResolver,nameresolver_
import time

class Config:

    @staticmethod
    def read( file='xknx.yaml'):
        print("Reading {0}".format(file))
        with open(file, 'r') as f:
            doc = yaml.load(f)
            Config.parse(doc)

    @staticmethod
    def parse(doc):
        for group in doc["groups"]:
            if group.startswith("dimmer"):
                for entry in doc["groups"][group]:
                    dimmer = Dimmer(entry, doc["groups"][group][entry])
                    nameresolver_.devices.append(dimmer)
            if group.startswith("outlet"):
                for entry in doc["groups"][group]:
                    outlet = Outlet(entry, doc["groups"][group][entry])
                    nameresolver_.devices.append(outlet)
            if group.startswith("switch"):
                for entry in doc["groups"][group]:
                    switch = Switch(entry, doc["groups"][group][entry])
                    nameresolver_.devices.append(switch)
            if group.startswith("shutter"):
                for entry in doc["groups"][group]:
                    shutter = Shutter(entry, doc["groups"][group][entry])
                    nameresolver_.devices.append(shutter)

