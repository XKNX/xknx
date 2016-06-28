
#from .nameresolver import NameResolver,nameresolver_
from .address import Address
from .multicast import Multicast
from .telegram import Telegram
from .multicast import Multicast

class BinaryOutput:
    def __init__(self, group):
        self.group=group
        self.state = False

    def set_internal_state(self, state):
        if state != self.state:
            print("Setting state to %i" % state )
            self.state = state

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

    
