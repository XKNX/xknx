from .address import Address
from .multicast import Multicast
from .telegram import Telegram
from .device import Device
from .globals import Globals

class BinaryOutput(Device):

    def __init__(self, name, group_address):
        Device.__init__(self, name)
        self.group_address=group_address
        self.state = False

    def has_group_address(self, group_address):
        return self.group_address == group_address


    def set_internal_state(self, state):
        if state != self.state:
            self.state = state
            self.after_update_callback(self)

    def send(self, payload):
        multicast = Multicast()
        telegram = Telegram()
        telegram.sender.set(Globals.get_own_address())
        telegram.group_address=self.group_address
        telegram.payload.append(payload)
        multicast.send(telegram)

    def set_on(self):
        self.send(0x81)
        self.set_internal_state(True)

    def set_off(self):
        self.send(0x80)
        self.set_internal_state(False)

    def do(self,action):
        if(action=="on"):
            self.set_on()
        elif(action=="off"):
            self.set_off()
        else:
            print("{0}: Could not understand action {1}".format(self.get_name(), action))


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
