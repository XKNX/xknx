import yaml
from .switch import Switch
from .thermostat import Thermostat
from .time import Time
from .light import Light
from .outlet import Outlet
from .shutter import Shutter
from .address import Address, AddressType

class Config:

    def __init__(self, xknx):
        self.xknx = xknx


    def read(self, file='xknx.yaml'):
        print("Reading {0}".format(file))
        with open(file, 'r') as filehandle:
            doc = yaml.load(filehandle)
            self.parse_general(doc)
            self.parse_groups(doc)


    def parse_general(self, doc):
        if "general" in doc:
            if "own_address" in doc["general"]:
                self.xknx.globals.own_address = \
                    Address(doc["general"]["own_address"],
                            AddressType.PHYSICAL)
            if "own_ip" in doc["general"]:
                self.xknx.globals.own_ip = doc["general"]["own_ip"]


    def parse_groups(self, doc):
        for group in doc["groups"]:
            if group.startswith("light"):
                self.parse_group_light(doc["groups"][group])
            elif group.startswith("outlet"):
                self.parse_group_outlet(doc["groups"][group])
            elif group.startswith("switch"):
                self.parse_group_switch(doc["groups"][group])
            elif group.startswith("shutter"):
                self.parse_group_shutter(doc["groups"][group])
            elif group.startswith("thermostat"):
                self.parse_group_thermostat(doc["groups"][group])
            elif group.startswith("time"):
                self.parse_group_time(doc["groups"][group])


    def parse_group_light(self, entries):
        for entry in entries:
            light = Light(self.xknx,
                          entry,
                          entries[entry])
            self.xknx.devices.devices.append(light)


    def parse_group_outlet(self, entries):
        for entry in entries:
            outlet = Outlet(self.xknx,
                            entry,
                            entries[entry])
            self.xknx.devices.devices.append(outlet)


    def parse_group_switch(self, entries):
        for entry in entries:
            switch = Switch(self.xknx,
                            entry,
                            entries[entry])
            self.xknx.devices.devices.append(switch)


    def parse_group_shutter(self, entries):
        for entry in entries:
            shutter = Shutter(self.xknx,
                              entry,
                              entries[entry])
            self.xknx.devices.devices.append(shutter)


    def parse_group_thermostat(self, entries):
        for entry in entries:
            thermostat = Thermostat(self.xknx,
                                    entry,
                                    entries[entry])
            self.xknx.devices.devices.append(thermostat)


    def parse_group_time(self, entries):
        for entry in entries:
            time = Time(self.xknx,
                        entry,
                        entries[entry])
            self.xknx.devices.devices.append(time)
