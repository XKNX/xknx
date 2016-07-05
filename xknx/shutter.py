from .address import Address
from .multicast import Multicast
from .telegram import Telegram
from .device import Device

class Shutter(Device):
    def __init__(self, name, group_address_long, group_address_short, group_address_position):
        Device.__init__(self)
        self.name = name
        self.group_address_long = group_address_long
        self.group_address_short = group_address_short
        self.group_address_position = group_address_position

        # XXX replace with "has_group_address() function
        self.group_address = group_address_long

    def __str__(self):
        return "<Shutter group_address_long={0}, group_address_short={0}, group_address_position={0}, name={1}>".format(self.group_address_position,self.group_address_short,self.group_address_position,self.name)

    def send(self, group_address, payload):
        multicast = Multicast()
        telegram = Telegram()
        telegram.sender.set(Multicast.own_address_)
        telegram.group=group_address
        telegram.payload.append(payload)
        multicast.send(telegram)

    def set_down(self):
        self.send(self.group_address_long, 0x81)

    def set_up(self):
        self.send(self.group_address_long, 0x80)

    def set_short_down(self):
        self.send(self.group_address_short, 0x81)

    def set_short_up(self):
        self.send(self.group_address_short, 0x80)

#    def set_short_position(self,position):
#        self.send(self.group_address_position,position)

#    def request_state(self):
#        self.send(0x00)

