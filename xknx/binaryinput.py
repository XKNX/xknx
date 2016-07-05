from .device import Device


class CouldNotParseSwitchTelegram(Exception):
    pass

class BinaryInput(Device):
    def __init__(self, group_address):
        Device.__init__(self)
        self.group_address=group_address
        self.state=False

    def has_group_address(self, group_address):
        return self.group_address == group_address

    def set_internal_state(self, state):
        if state != self.state:
            print("Setting state to %i" % state )
            self.state = state

    def process(self,telegram):

        if len(telegram.payload) != 1:
            print("Could not parse telegram for binary input %s" % telegram )
            return

        elif telegram.payload[0] == 0x80 :
            self.set_internal_state(False)

        elif telegram.payload[0] == 0x81 :
            self.set_internal_state(True)


    def is_on(self):
        return self.state == True

    def is_off(self):
        return self.state == False
