import time
from .device import Device
from .address import Address
from .dpt_float import DPTTemperature
from .exception import CouldNotParseTelegram
from .dpt import DPTArray


class Thermostat(Device):


    def __init__(self,
                 xknx,
                 name,
                 group_address=None):

        Device.__init__(self, xknx, name)

        if isinstance(group_address, str):
            group_address = Address(group_address)

        self.group_address = group_address
        self.last_set = None
        self.temperature = None


    @classmethod
    def from_config(cls, xknx, name, config):
        group_address = \
            config.get('group_address')

        return cls(xknx,
                   name,
                   group_address=group_address)


    def has_group_address(self, group_address):
        return self.group_address == group_address


    def process(self, telegram):
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 2:
            raise CouldNotParseTelegram()

        self.temperature = DPTTemperature().from_knx(
            (telegram.payload.value[0],
             telegram.payload.value[1]))
        self.last_set = time.time()

        self.after_update()

    def __str__(self):
        return "<Thermostat name={0}, group_address={1}, " \
               "temperature={2}, last_set={3}>" \
               .format(self.name,
                       self.group_address,
                       self.temperature,
                       self.last_set)


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
