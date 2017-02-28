from xknx.knx  import Address, Telegram, TelegramType, DPTBinary, DPTArray
from .device import Device
from .exception import CouldNotParseTelegram

class Light(Device):

    def __init__(self,
                 xknx,
                 name,
                 group_address_switch=None,
                 group_address_state=None,
                 group_address_dimm=None,
                 group_address_brightness=None):
        # pylint: disable=too-many-arguments

        Device.__init__(self, xknx, name)

        if isinstance(group_address_switch, (str, int)):
            group_address_switch = Address(group_address_switch)
        if isinstance(group_address_state, (str, int)):
            group_address_state = Address(group_address_state)
        if isinstance(group_address_dimm, (str, int)):
            group_address_dimm = Address(group_address_dimm)
        if isinstance(group_address_brightness, (str, int)):
            group_address_brightness = Address(group_address_brightness)

        self.group_address_switch = group_address_switch
        self.group_address_dimm = group_address_dimm
        self.group_address_brightness = group_address_brightness
        self.group_address_state = group_address_state
        self.state = False
        self.brightness = 0
        self.supports_dimming = \
            group_address_brightness is not None \
            or group_address_dimm is not None


    @classmethod
    def from_config(cls, xknx, name, config):
        group_address_switch = \
            config.get('group_address_switch')
        group_address_dimm = \
            config.get('group_address_dimm')
        group_address_brightness = \
            config.get('group_address_brightness')
        group_address_state = \
            config.get('group_address_state')

        return cls(xknx,
                   name,
                   group_address_switch=group_address_switch,
                   group_address_dimm=group_address_dimm,
                   group_address_brightness=group_address_brightness,
                   group_address_state=group_address_state)


    def has_group_address(self, group_address):
        return (self.group_address_state == group_address) or \
               (self.group_address_switch == group_address) or \
               (self.group_address_dimm == group_address) or \
               (self.group_address_brightness == group_address)


    def __str__(self):
        if not self.supports_dimming:
            return '<Light name={0}, ' \
                    'group_address_switch={1}, ' \
                    'group_address_state={2}, ' \
                    'state={3}>' \
                    .format(
                        self.name,
                        self.group_address_switch,
                        self.group_address_state,
                        self.state)

        return '<Light name={0}, ' \
                'group_address_switch={1}, ' \
                'group_address_state={2}, ' \
                'group_address_dimm={3}, ' \
                'group_address_brightness={4}, ' \
                'state={5}, brightness={6}>' \
                .format(
                    self.name,
                    self.group_address_switch,
                    self.group_address_state,
                    self.group_address_dimm,
                    self.group_address_brightness,
                    self.state,
                    self.brightness)


    def set_internal_state(self, state):
        if state != self.state:
            self.state = state
            self.after_update()

    def set_internal_brightness(self, brightness):
        if brightness != self.brightness:
            self.brightness = brightness
            self.after_update()


    def send(self, group_address, payload=None):
        telegram = Telegram()
        telegram.group_address = group_address

        telegram.payload = payload
        self.xknx.telegrams.put_nowait(telegram)

    def set_on(self):
        self.send(self.group_address_switch, DPTBinary(1))
        self.set_internal_state(True)

    def set_off(self):
        self.send(self.group_address_switch, DPTBinary(0))
        self.set_internal_state(False)

    def set_brightness(self, brightness):
        if not self.supports_dimming:
            return
        self.send(self.group_address_brightness, DPTArray(brightness))
        self.set_internal_brightness(brightness)

    def do(self, action):
        if action == "on":
            self.set_on()
        elif action == "off":
            self.set_off()
        elif action.startswith("brightness:"):
            self.set_brightness(int(action[11:]))
        else:
            print("{0}: Could not understand action {1}" \
                .format(self.get_name(), action))

    def sync_state(self):
        telegram_switch = Telegram(
            self.group_address_switch,
            TelegramType.GROUP_READ)
        self.xknx.telegrams.put_nowait(telegram_switch)

        if self.supports_dimming:
            telegram_dimm = Telegram(
                self.group_address_brightness,
                TelegramType.GROUP_READ)
            self.xknx.telegrams.put_nowait(telegram_dimm)

    def process(self, telegram):
        if telegram.group_address == self.group_address_switch or \
            telegram.group_address == self.group_address_state:
            self._process_state(telegram)
        elif self.supports_dimming and \
                telegram.group_address == self.group_address_brightness:
            self._process_dimm(telegram)


    def _process_dimm(self, telegram):
        if not isinstance(telegram.payload, DPTArray) or \
            len(telegram.payload.value) != 1:
            raise CouldNotParseTelegram()

        self.set_internal_brightness(telegram.payload.value[0])


    def _process_state(self, telegram):
        if not isinstance(telegram.payload, DPTBinary):
            raise CouldNotParseTelegram()
        if telegram.payload.value == 0:
            self.set_internal_state(False)
        elif telegram.payload.value == 1:
            self.set_internal_state(True)
        else:
            raise CouldNotParseTelegram()


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
