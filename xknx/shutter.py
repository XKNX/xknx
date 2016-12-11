from .address import Address
from .multicast import Multicast
from .telegram import Telegram
from .device import Device
from .globals import Globals


class CouldNotParseShutterTelegram(Exception):
    pass
class Shutter(Device):
    def __init__(self, name, config):
        Device.__init__(self, name)
        self.group_address_long = config["group_address_long"]
        self.group_address_short = config["group_address_short"]
        self.group_address_position = config["group_address_position"]
        self.value_short = None
        self.value_long = None
     
    def has_group_address(self, group_address):
        return ( self.group_address_long == group_address ) or (self.group_address_short == group_address ) or (self.group_address_position == group_address )


    def __str__(self):
        return "<Shutter group_address_long={0}, group_address_short={1}, group_address_position={2}, name={3}>".format(self.group_address_long,self.group_address_short,self.group_address_position,self.name)

    def send(self, group_address, payload):
        multicast = Multicast()
        telegram = Telegram()
        telegram.sender.set(Globals.get_own_address())
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
    def process(self,telegram):
        self.process_telegram( telegram )
        print(self.value_short)      
        print(self.value_long)
#        print("FNORD {0}".format(len(telegram.payload)))
#        print(self)
#
#    def set_short_position(self,position):
#        self.send(self.group_address_position,position)

#    def request_state(self):
#        self.send(0x00)
    def set_value_async(self, name, value):
        if name == 'short' :
            self.value_short = value
        if name == 'long' :
            self.value_long = value
		
    def process_telegram(self,telegram):
        if len(telegram.payload) != 1:
          raise(CouldNotParseShutterTelegram) 
       
          if telegram.payload[0] == 0x80 :
            if telegram.group_address == self.group_address_short:
                self.value_short = 0
            elif telegram.group_address == self.group_address_long:
                self.value_long = 0
          if telegram.payload[0] == 0x81 :
            if telegram.group_address == self.group_address_short:
                self.value_short = 1
            elif telegram.group_address == self.group_address_long:
                self.value_long =1
          self.after_update_callback(self)
          return
        
        raise(CouldNotParseShutterTelegram)
