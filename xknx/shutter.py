from .address import Address
from .multicast import Multicast
from .telegram import Telegram
from .device import Device

class Shutter(Device):
    def __init__(self, name, config):
        Device.__init__(self)
        self.name = name
        self.group_address_long = config["group_address_long"]
        self.group_address_short = config["group_address_short"]
        self.group_address_position = config["group_address_position"]

    def has_group_address(self, group_address):
        return ( self.group_address_long == group_address ) or (self.group_address_short == group_address ) or (self.group_address_position == group_address )


    def __str__(self):
        return "<Shutter group_address_long={0}, group_address_short={1}, group_address_position={2}, name={3}>".format(self.group_address_long,self.group_address_short,self.group_address_position,self.name)

    def send(self, group_address, payload):
        multicast = Multicast()
        telegram = Telegram()
        telegram.sender.set(Multicast.own_address)
        telegram.group_address=group_address
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

    def do(self,action):
        if(action=="up"):
            self.set_up()
        elif(action=="short_up"):
            self.set_short_up()
        elif(action=="down"):
            self.set_down()
        elif(action=="short_down"):
            self.set_short_down()        
        else:
            print("{0}: Could not understand action {1}".format(self.get_name(), action))

#    def request_state(self):
#        #self.send(self.group_address_long,0x00)
#        self.send(self.group_address_position,0x00)
#
#    def process(self,telegram):
#        print("FNORD {0}".format(len(telegram.payload)))
#        print(self)
#
#    def set_short_position(self,position):
#        self.send(self.group_address_position,position)

#    def request_state(self):
#        self.send(0x00)

