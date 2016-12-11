from .address import Address
from .multicast import Multicast
from .telegram import Telegram
from .device import Device
from .globals import Globals

class Shutter(Device):
    def __init__(self, name, config):
        Device.__init__(self, name)
        self.group_address_long = config.get("group_address_long")
        self.group_address_short = config.get("group_address_short")
        self.group_address_position = config.get("group_address_position")
        self.group_address_position_feedback = config.get("group_address_position_feedback")

        self.position = 0

    def has_group_address(self, group_address):
        return ( self.group_address_long == group_address ) or (self.group_address_short == group_address ) or (self.group_address_position_feedback == group_address )


    def __str__(self):
        return "<Shutter group_address_long={0}, group_address_short={1}, group_address_position, group_address_position_feedback={2}, name={3}>".format(self.group_address_long,self.group_address_short,self.group_address_position, self.group_address_position_feedback,self.name)

    def send(self, group_address, payload):
        multicast = Multicast()
        telegram = Telegram()
        telegram.sender.set(Globals.get_own_address())
        telegram.group_address=group_address

        if isinstance(payload, list):
            for p in payload:
                telegram.payload.append(p)
        elif isinstance(payload, int):
                telegram.payload.append(payload)
        else:
            print("Cannot understand payload")

        multicast.send(telegram)

    def set_down(self):
        if self.group_address_long is None:
            print("group_address_long not defined for device {0}".format(self.get_name()))
            return
        self.send(self.group_address_long, 0x81)

    def set_up(self):
        if self.group_address_long is None:
            print("group_address_long not defined for device {0}".format(self.get_name()))
            return
        self.send(self.group_address_long, 0x80)

    def set_short_down(self):
        if self.group_address_short is None:
            print("group_address_short not defined for device {0}".format(self.get_name()))
            return
        self.send(self.group_address_short, 0x81)

    def set_short_up(self):
        if self.group_address_short is None:
            print("group_address_short not defined for device {0}".format(self.get_name()))
            return
        self.send(self.group_address_short, 0x80)

    def set_position(self, position):
        if self.group_address_position is None:
            print("group_address_position not defined for device {0}".format(self.get_name()))
            return
        self.send(self.group_address_position, [0x80, position])

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

    def request_state(self):
        if self.group_address_position_feedback is None:
            print("group_position not defined for device {0}".format(self.get_name()))
            return
        self.send(self.group_address_position_feedback,0x00)

    def process(self,telegram):
        if len(telegram.payload) != 2:
            raise(CouldNotParseSwitchTelegram)

        # telegram.payload[0] is 0x40 if state was requested, 0x80 if state of shutter was changed

        self.position = telegram.payload[1]

        self.after_update_callback(self)

    def is_open(self):
        if self.position is not None:
            if self.position == 255:
                return True
            else:
                return False
        else:
            return None

    def is_closed(self):
        if self.position is not None:
            if self.position == 0:
                return True
            else:
                return False
        else:
            return None
