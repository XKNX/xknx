import yaml
from .address import Address

class CouldNotResolve(Exception):
    def __init__(self, group_name):
        self.group_name = group_name

    def __str__(self):
        return "CouldNotResolve <name={0}>".format(self.group_name)

class NameResolver:

    def __init__(self):
        print("Initialization of NameResolver");

    def init(self, file='xknx.yaml'):
        print("Reading {0}".format(file))
        with open(file, 'r') as f:
            self.doc = yaml.load(f)

    def device_name( self, address ):
        if type(address) is Address:
            return self.device_name( address.str() )

        if address not in self.doc["devices"].keys():
            return 'unknown device ({0})'.format(address)

        return self.doc["devices"][address]


    def group_name( self, group ):
        if group not in self.doc["groups"].keys():
            return 'unknown group ({0})'.format(group)

        return self.doc["groups"][group]

    def group_id( self, group_name ):
        for entry in self.doc["groups"]:
            if self.doc["groups"][entry] == group_name:
                return entry

        raise CouldNotResolve(group_name)


nameresolver_ = NameResolver()
