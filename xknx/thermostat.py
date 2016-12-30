from .device import Device
from .address import Address
from .dpt_float import DPT_Temperature
from .exception import CouldNotParseTelegram
from .dpt import DPT_Array

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
        if not isinstance(telegram.payload, DPT_Array) or len(telegram.payload.value) != 2:
            raise CouldNotParseTelegram()

        self.temperature = DPT_Temperature().from_knx(( telegram.payload.value[0] , telegram.payload.value[1] ))

        self.after_update_callback(self)

    def __str__(self):
        return "<Thermostat group_address={0}, name={1}>".format(self.group_address,self.name)
