from .address import Address
from .telegram import Telegram,TelegramType
from .dpt import DPT_Binary
from .exception import CouldNotParseTelegram
from .device import Device

class Outlet(Device):

    def __init__(self, xknx, name, config):
        self.group_address = Address(config["group_address"])
        Device.__init__(self, xknx, name)
        self.state = False


    def has_group_address(self, group_address):
        return self.group_address == group_address


    def set_internal_state(self, state):
        if state != self.state:
            self.state = state
            self.after_update_callback(self)


    def send(self, payload):
        telegram = Telegram()
        telegram.group_address=self.group_address
        telegram.payload = payload
        self.xknx.telegrams.put(telegram)

    def set_on(self):
        self.send( DPT_Binary(1) )
        self.set_internal_state(True)


    def set_off(self):
        self.send( DPT_Binary(0) )
        self.set_internal_state(False)


    def do(self,action):
        if(action=="on"):
            self.set_on()
        elif(action=="off"):
            self.set_off()
        else:
            print("{0}: Could not understand action {1}".format(self.get_name(), action))


    def request_state(self):
        telegram = Telegram(self.group_address, TelegramType.GROUP_READ)
        self.xknx.telegrams.put(telegram)

    def process(self,telegram):

        if not isinstance( telegram.payload, DPT_Binary ):
            raise CouldNotParseTelegram()

        if telegram.payload.value == 0 :
            self.set_internal_state(False)
        elif telegram.payload.value == 1 :
            self.set_internal_state(True)
        else:
            raise CouldNotParseTelegram()


    def __str__(self):
        return "<Outlet group_address={0}, name={1} internal_state={2}>".format(self.group_address,self.name,self.internal_state)

