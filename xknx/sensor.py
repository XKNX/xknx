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
                 value_type=None,
                 sensor_class=None,
                 significant_bit=1):
        # pylint: disable=too-many-arguments

        Device.__init__(self, xknx, name)

        if isinstance(group_address, (str, int)):
            group_address = Address(group_address)
        if not isinstance(significant_bit, int):
            raise TypeError()

        self.group_address = group_address
        self.value_type = value_type
        self.sensor_class = sensor_class
        self.significant_bit = significant_bit
        self.state = None


    @classmethod
    def from_config(cls, xknx, name, config):
        group_address = \
            config.get('group_address')
        value_type = \
            config.get('value_type')
        sensor_class = \
            config.get('sensor_class')
        significant_bit = \
            config.get('significant_bit', 1)

        return cls(xknx,
                   name,
                   group_address=group_address,
                   value_type=value_type,
                   sensor_class=sensor_class,
                   significant_bit=significant_bit)


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

    def is_binary(self):
        return self.value_type == 'binary'


    def binary_state(self):
        if not self.is_binary() or \
                not isinstance(self.state, DPTBinary):
            return False

        return self.state.value & (1 << (self.significant_bit-1)) != 0


    def unit_of_measurement(self):
        if self.value_type == 'percent':
            return "%"
        else:
            return None


    def resolve_state(self):
        if self.state is None:
            return None

        elif self.value_type == 'percent' and \
                isinstance(self.state, DPTArray) and \
                len(self.state.value) == 1:
            # TODO: Instanciate DPTScaling object with DPTArray class
            return "{0}".format(DPTScaling().from_knx(self.state.value))


        elif self.value_type == 'binary':
            return self.binary_state()

        elif isinstance(self.state, DPTArray):
            return ','.join('0x%02x'%i for i in self.state.value)

        elif isinstance(self.state, DPTBinary):
            return "{0:b}".format(self.state.value)

        raise TypeError()


    def __str__(self):
        return '<Sensor name={0}, ' \
               'group_address={1}, ' \
               'state={2}, ' \
               'resolve_state={3}>' \
            .format(self.name,
                    self.group_address,
                    self.state,
                    self.resolve_state())


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
