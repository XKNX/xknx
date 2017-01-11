from .address import Address
from .telegram import Telegram, TelegramType
from .dpt import DPTBinary, DPTArray
from .dpt_scaling import DPTScaling
from .device import Device

class Sensor(Device):

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 value_type=None):

        Device.__init__(self, xknx, name)

        if isinstance(group_address, (str, int)):
            group_address = Address(group_address)

        self.group_address = group_address
        self.value_type = value_type
        self.state = None


    @classmethod
    def from_config(cls, xknx, name, config):
        group_address = \
            config.get('group_address')
        value_type = \
            config.get('value_type')

        return cls(xknx,
                   name,
                   group_address=group_address,
                   value_type=value_type)


    def has_group_address(self, group_address):
        return self.group_address == group_address


    def set_internal_state(self, state):
        if state != self.state:
            self.state = state
            self.after_update()


    def sync_state(self):
        telegram = Telegram(self.group_address, TelegramType.GROUP_READ)
        self.xknx.telegrams.put(telegram)


    def process(self, telegram):
        self.set_internal_state(telegram.payload)

        print(self)


    def unit_of_measurement(self):
        if self.value_type == 'percent':
            return "%"
        else:
            return None


    def state_str(self):
        if self.state is None:
            return None

        elif self.value_type == 'percent' and \
                isinstance(self.state, DPTArray) and \
                len(self.state.value) == 1:
            # TODO: Instanciate DPTScaling object with DPTArray class
            return "{0}".format(DPTScaling().from_knx(self.state.value))

        elif isinstance(self.state, DPTArray):
            return ','.join('0x%02x'%i for i in self.state.value)

        elif isinstance(self.state, DPTBinary):
            return "{0:b}".format(self.state.value)

        raise TypeError()


    def __str__(self):
        return '<Sensor name={0}, ' \
               'group_address={1}, ' \
               'state={2}, ' \
               'state_str={3}>' \
            .format(self.name,
                    self.group_address,
                    self.state,
                    self.state_str())


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
