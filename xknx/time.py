from .device import Device
from .address import Address
from .dpt_time import DPT_Time
from .telegram import Telegram
from .globals import Globals

import time


class Time(Device):
    def __init__(self, xknx, name, config):
        Device.__init__(self, xknx, name)
        self.group_address = Address(config["group_address"])

    def has_group_address(self, group_address):
        return self.group_address == group_address

    def broadcast_time(self):
        telegram = Telegram()
        telegram.sender = Globals.get_own_address()
        telegram.group_address=self.group_address

        telegram.payload.append(0x80)
        for byte in DPT_Time.current_time_as_knx():
            telegram.payload.append(byte)

        self.xknx.out_queue.put(telegram)

    def request_state(self):
        self.broadcast_time()

    def __str__(self):
        return "<Time group_address={0}, name={1}>".format(self.group_address,self.name)
