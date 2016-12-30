from .device import Device
from .dpt import DPT_Binary
from .exception import CouldNotParseTelegram

from enum import Enum

class BinaryInputState(Enum):
    ON = 1
    OFF = 2

class BinaryInput(Device):
    def __init__(self, xknx, name, group_address):
        Device.__init__(self, xknx, name)
        self.group_address=group_address
        self.state=BinaryInputState.OFF

    def has_group_address(self, group_address):
        return self.group_address == group_address

    def set_internal_state(self, state):
        if state != self.state:
            self.state = state


    def process(self, telegram ):
        if not isinstance( telegram.payload, DPT_Binary ):
            raise CouldNotParseTelegram()

        if telegram.payload.value == 0:
            self.set_internal_state( BinaryInputState.OFF )
        elif telegram.payload.value == 1:
            self.set_internal_state( BinaryInputState.ON )
        else:
            raise CouldNotParseTelegram()


    def is_on(self):
        return self.state == BinaryInputState.ON


    def is_off(self):
        return self.state == BinaryInputState.OFF
