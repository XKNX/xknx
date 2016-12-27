from .device import Device
from .address import Address
from .dpt import DPT_Float

import time


class Thermostat(Device):
    def __init__(self, xknx, name, config):
        Device.__init__(self, xknx, name)
        self.group_address = Address(config["group_address"])
        self.last_set = time.time();
        self.temperature = 0

    def has_group_address(self, group_address):
        return self.group_address == group_address

    def process(self,telegram):
        if len(telegram.payload) != 3:
            raise(CouldNotParseSwitchTelegram)

        self.temperature = DPT_Float.from_knx( telegram.payload[1] , telegram.payload[2] ) 

        self.after_update_callback(self)

    def __str__(self):
        return "<Thermostat group_address={0}, name={1}>".format(self.group_address,self.name)
