import yaml
from .address import Address

class CouldNotResolve(Exception):
    def __init__(self, group_name):
        self.group_name = group_name

    def __str__(self):
        return "CouldNotResolve <name={0}>".format(self.group_name)

class Dimmer:
    def __init__(self, name, group_address):
        self.name = name
        self.group_address = group_address

    def __str__(self):
        return "<Dimmer group_address={0}, name={1}>".format(self.group_address,self.name)

class Outlet:
    def __init__(self, name, group_address):
        self.name = name
        self.group_address = group_address

    def __str__(self):
        return "<Outlet group_address={0}, name={1}>".format(self.group_address,self.name)

class Switch:
    def __init__(self, name, group_address):
        self.name = name
        self.group_address = group_address

    def __str__(self):
        return "<Switch group_address={0}, name={1}>".format(self.group_address,self.name)


class NameResolver:

    def __init__(self):
        print("Initialization of NameResolver")
        self.devices = []

    def init(self, file='xknx.yaml'):
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


    def device_name( self, address ):
        if type(address) is Address:
            return self.device_name( address.str() )

        if address not in self.doc["devices"].keys():
            return 'unknown device ({0})'.format(address)

        return self.doc["devices"][address]


    def group_name( self, group ):
        for device in self.devices:
            if device.group == group:
                return device.group_name

        if group not in self.doc["groups"].keys():
            return 'unknown group ({0})'.format(group)

        return self.doc["groups"][group]

    def group_id( self, group_name ):
        for device in self.devices:
            if device.name == group_name: 
                return device.group_address

        raise CouldNotResolve(group_name)


nameresolver_ = NameResolver()
