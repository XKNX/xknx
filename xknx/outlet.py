from .address import Address
from .telegram import Telegram
from .device import Device

class Outlet(Device):

    def __init__(self, xknx, name, config):
        self.group_address = Address(config["group_address"])
        Device.__init__(self, xknx, name)
        self.state = False


    def has_group_address(self, group_address):
        return self.group_address == group_address


    def set_internal_state(self, state):
        if state != self.state:
            self.state = state
            self.after_update_callback(self)


    def send(self, payload):
        telegram = Telegram()
        telegram.sender = self.xknx.globals.own_address
        telegram.group_address=self.group_address
        telegram.payload.append(payload)
        self.xknx.out_queue.put(telegram)  


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

        if telegram.payload[0] == 0x40 :
            self.set_internal_state(False)
        elif telegram.payload[0] == 0x41 :
            self.set_internal_state(True)
        else:
            print("Could not parse payload for binary output %s".format( telegram.payload[0] ))



    def __str__(self):
        return "<Outlet group_address={0}, name={1}>".format(self.group_address,self.name)

