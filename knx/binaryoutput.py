
from .nameresolver import NameResolver,nameresolver_
from .address import Address
from .multicast import Multicast
from .telegram import Telegram
from .multicast import Multicast

class BinaryOutput:
    def __init__(self, group):
        if type(group) is str:
            self.group=nameresolver_.group_id(group)
        else:
            self.group=group

    def send(self, payload):
        multicast = Multicast()
        telegram = Telegram()
        telegram.sender.set(Multicast.own_address_)
        telegram.group=self.group
        telegram.payload.append(payload)
        multicast.send(telegram)

    def set_on(self):
        self.send(0x81)

    def set_off(self):
        self.send(0x80)
