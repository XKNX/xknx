from .address import Address
from .multicast import Multicast
from .telegram import Telegram
from .device import Device

class BinaryOutput(Device):

    def __init__(self, group_address):
        Device.__init__(self)
        self.group_address=group_address
        self.state = False

    def has_group_address(self, group_address):
        return self.group_address == group_address


    def set_internal_state(self, state):
        if state != self.state:
            print("Setting state to %i" % state )
            self.state = state

    def send(self, payload):
        multicast = Multicast()
        telegram = Telegram()
        telegram.sender.set(Multicast.own_address_)
        telegram.group_address=self.group_address
        telegram.payload.append(payload)
        multicast.send(telegram)

    def set_on(self):
        self.send(0x81)

    def set_off(self):
        self.send(0x80)

    def request_state(self):
        self.send(0x00)

    def process(self,telegram):

        if len(telegram.payload) != 1:
            print("Could not parse telegram for binary output %s" % telegram ) 
            return

        elif telegram.payload[0] == 0x40 :
            self.set_internal_state(False)

        elif telegram.payload[0] == 0x41 :
            self.set_internal_state(True)

    
