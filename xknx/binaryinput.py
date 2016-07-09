from .device import Device

from enum import Enum

class CouldNotParseSwitchTelegram(Exception):
    pass

class BinaryInputState(Enum):
    ON = 1
    OFF = 2

class BinaryInput(Device):
    def __init__(self, group_address):
        Device.__init__(self)
        self.group_address=group_address
        self.state=BinaryInputState.OFF

    def has_group_address(self, group_address):
        return self.group_address == group_address

    def set_internal_state(self, state):
        if state != self.state:
            print("Setting state to %s" % state )
            self.state = state

    def process_telegram(self,telegram):
        if len(telegram.payload) != 1:
            raise(CouldNotParseSwitchTelegram) 
        if telegram.payload[0] == 0x80 :
            return BinaryInputState.OFF
        if telegram.payload[0] == 0x81 :
            return BinaryInputState.ON
        raise(CouldNotParseSwitchTelegram)

    def process(self,telegram):
        self.set_internal_state( self.process_telegram( telegram ) )

    def is_on(self):
        return self.state == BinaryInputState.ON

    def is_off(self):
        return self.state == BinaryInputState.OFF
