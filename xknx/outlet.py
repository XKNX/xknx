from xknx.knx import Address, Telegram, TelegramType, DPTBinary
from .exception import CouldNotParseTelegram
from .device import Device

class Outlet(Device):

    def __init__(self,
                 xknx,
                 name,
                 group_address=None):

        Device.__init__(self, xknx, name)

        if isinstance(group_address, (str, int)):
            group_address = Address(group_address)

        self.group_address = group_address
        self.state = False


    @classmethod
    def from_config(cls, xknx, name, config):
        group_address = \
            config.get('group_address')

        return cls(xknx,
                   name,
                   group_address=group_address)


    def has_group_address(self, group_address):
        return self.group_address == group_address


    def set_internal_state(self, state):
        if state != self.state:
            self.state = state
            self.after_update()


    def send(self, payload):
        telegram = Telegram()
        telegram.group_address = self.group_address
        telegram.payload = payload
        self.xknx.telegrams.put_nowait(telegram)


    def set_on(self):
        self.send(DPTBinary(1))
        self.set_internal_state(True)


    def set_off(self):
        self.send(DPTBinary(0))
        self.set_internal_state(False)


    def do(self, action):
        if action == "on":
            self.set_on()
        elif action == "off":
            self.set_off()
        else:
            print("{0}: Could not understand action {1}" \
                .format(self.get_name(), action))

    def sync_state(self):
        telegram = Telegram(self.group_address, TelegramType.GROUP_READ)
        self.xknx.telegrams.put_nowait(telegram)


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
        return "<Outlet name={0}, group_address={1}, state={2}>" \
            .format(self.name, self.group_address, self.state)


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
