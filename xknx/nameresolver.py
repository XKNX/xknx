import yaml
from .address import Address
from .binaryoutput import BinaryOutput
from .binaryinput import BinaryInput
from .device import Device
from .switch import Switch
from .dimmer import Dimmer
from .outlet import Outlet
from .shutter import Shutter
import time
import threading

class CouldNotResolveAddress(Exception):
    def __init__(self, group_address):
        self.group_address = group_address

    def __str__(self):
        return "CouldNotResolveAddress <name={0}>".format(self.group_address)

class CouldNotResolveName(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "CouldNotResolveName <name={0}>".format(self.name)


class NameResolver:

    def __init__(self):
        print("Initialization of NameResolver")
        self.devices = []

    def read_configuration(self, file='xknx.yaml'):
        print("Reading {0}".format(file))
        with open(file, 'r') as f:
            self.doc = yaml.load(f)

        for group in self.doc["groups"]:
            if group.startswith("dimmer"):
                for entry in self.doc["groups"][group]:
                    dimmer = Dimmer(entry, self.doc["groups"][group][entry])
                    self.devices.append(dimmer)
            if group.startswith("outlet"):
                for entry in self.doc["groups"][group]:
                    outlet = Outlet(entry, self.doc["groups"][group][entry])
                    self.devices.append(outlet)
            if group.startswith("switch"):
                for entry in self.doc["groups"][group]:
                    switch = Switch(entry, self.doc["groups"][group][entry])
                    self.devices.append(switch)
            if group.startswith("shutter"):
                for entry in self.doc["groups"][group]:
                    shutter = Shutter(entry, self.doc["groups"][group][entry]) 
                    self.devices.append(shutter)

    def device_by_group_address( self, group_address):
        for device in self.devices:
            if device.has_group_address(group_address):
                return device
        raise CouldNotResolveAddress(group_address)

    def device_by_name( self, name):
        for device in self.devices:
            if device.name == name:
                return device
        raise CouldNotResolveName(name)

    def get_outlets( self ):
        outlets = []
        for device in self.devices:
            if type(device) == Outlet:
                outlets.append(device)
        return outlets

    def get_devices( self ):
        return self.devices

    def update_thread_start(self,timeout):
        def worker(timeout):
            while True:
                devices = nameresolver_.get_devices()
                for device in self.devices:
                    device.request_state()
                time.sleep(timeout)
        t = threading.Thread(target=worker, args=(timeout,))
        t.start();

nameresolver_ = NameResolver()
