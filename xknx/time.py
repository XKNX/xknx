from xknx.knx import Address, Telegram, DPTArray, DPTTime
from .device import Device


class Time(Device):

    def __init__(self,
                 xknx,
                 name,
                 group_address=None):

        Device.__init__(self, xknx, name)

        if isinstance(group_address, (str, int)):
            group_address = Address(group_address)

        self.group_address = group_address


    @classmethod
    def from_config(cls, xknx, name, config):
        group_address = \
            config.get('group_address')

        return cls(xknx,
                   name,
                   group_address=group_address)


    def has_group_address(self, group_address):
        return self.group_address == group_address


    def broadcast_time(self):
        telegram = Telegram()
        telegram.group_address = self.group_address
        telegram.payload = DPTArray(DPTTime.current_time_as_knx())
        self.xknx.telegrams.put_nowait(telegram)

    def sync_state(self):
        self.broadcast_time()


    def __str__(self):
        return "<Time name={0}, group_address={1}>" \
            .format(self.name, self.group_address)


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
