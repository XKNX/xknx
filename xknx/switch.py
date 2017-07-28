from xknx.knx import Address, DPTBinary
from .exception import CouldNotParseTelegram
from .device import Device

class Switch(Device):

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 group_address_state=None,
                 device_updated_cb=None):
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name, device_updated_cb)

        if isinstance(group_address, (str, int)):
            group_address = Address(group_address)
        if isinstance(group_address_state, (str, int)):
            group_address_state = Address(group_address_state)

        self.group_address = group_address
        self.group_address_state = group_address_state
        self.state = False


    @classmethod
    def from_config(cls, xknx, name, config):
        group_address = \
            config.get('group_address')
        group_address_state = \
            config.get('group_address_state')

        return cls(xknx,
                   name,
                   group_address=group_address,
                   group_address_state=group_address_state)


    def has_group_address(self, group_address):
        return (self.group_address == group_address) or \
               (self.group_address_state == group_address)


    def set_internal_state(self, state):
        if state != self.state:
            self.state = state
            self.after_update()

    def set_on(self):
        self.send(self.group_address, DPTBinary(1))
        self.set_internal_state(True)


    def set_off(self):
        self.send(self.group_address, DPTBinary(0))
        self.set_internal_state(False)


    def do(self, action):
        if action == "on":
            self.set_on()
        elif action == "off":
            self.set_off()
        else:
            print("{0}: Could not understand action {1}" \
                .format(self.get_name(), action))

    def state_addresses(self):
        return [self.group_address_state or self.group_address,]


    def process(self, telegram):
        if not isinstance(telegram.payload, DPTBinary):
            raise CouldNotParseTelegram()

        if telegram.payload.value == 0:
            self.set_internal_state(False)
        elif telegram.payload.value == 1:
            self.set_internal_state(True)
        else:
            raise CouldNotParseTelegram()


    def __str__(self):
        return '<Switch name="{0}" group_address="{1}" ' \
               'group_address_state="{2}" state="{3}" />' \
            .format(self.name,
                    self.group_address,
                    self.group_address_state,
                    self.state)


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
