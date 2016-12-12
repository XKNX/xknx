from .device import Device
from .multicast import Multicast
from .telegram import Telegram
from .globals import Globals
import time

class Dimmer(Device):
    def __init__(self, name, config):
        Device.__init__(self, name)
        self.group_address_switch = config["group_address_switch"]
        self.group_address_dimm = config["group_address_dimm"]
        self.group_address_dimm_feedback = config["group_address_dimm_feedback"]

        self.state = False
        self.brightness = 0

    def has_group_address(self, group_address):
            return ( self.group_address_switch == group_address ) or (self.group_address_dimm == group_address ) or (self.group_address_dimm_feedback == group_address )

    def __str__(self):
        return "<Dimmer group_address_switch={0}, group_address_dimm={0}, group_address_dimm_feedback={2},name={3}>".format(self.group_address_switch,self.group_address_dimm,self.group_address_dimm_feedback,self.name)

    def set_internal_state(self, state):
        brightness = 255 if True else 0

        if state != self.state or brightness != self.brightness:
            self.state = state
            self.brightness = brightness
            self.after_update_callback(self)


    def set_internal_brightness(self, brightness):
        state = True if brightness > 0 else False

        if state != self.state or brightness != self.brightness:
            self.state = state
            self.brightness = brightness
            self.after_update_callback(self)


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

    def set_on(self):
        self.send(self.group_address_switch, 0x81)
        self.set_internal_state(True)

    def set_off(self):
        self.send(self.group_address_switch, 0x80)
        self.set_internal_state(False)

    def set_brightness(self, brightness):
        self.send(self.group_address_dimm_feedback, [0x80,brightness] )
        self.set_internal_brightness(brightness)

    def request_state(self):
        if self.group_address_dimm_feedback is None:
            print("group_address_dimm_feedback not defined for device {0}".format(self.get_name()))
            return

        # We have to request both ..
        self.send(self.group_address_dimm_feedback,0x00)
        self.send(self.group_address_switch,0x00)

    def process(self,telegram):
        print("FEEDBACK")
