from .device import Device
from .telegram import Telegram,TelegramType
from .address import Address
from .exception import CouldNotParseTelegram
from .dpt import DPT_Binary,DPT_Array
import time

class Dimmer(Device):
    def __init__(self, xknx, name, config):
        Device.__init__(self, xknx, name)
        self.group_address_switch = Address(config.get("group_address_switch"))
        self.group_address_dimm = Address(config.get("group_address_dimm"))
        self.group_address_dimm_feedback = Address(config.get("group_address_dimm_feedback"))
        self.group_address_state = Address(config.get("group_address_state"))
 
        self.state = False
        self.brightness = 0

    def has_group_address(self, group_address):
        return ( self.group_address_state == group_address ) or ( self.group_address_switch == group_address ) or (self.group_address_dimm == group_address ) or (self.group_address_dimm_feedback == group_address )

    def __str__(self):
        return "<Dimmer group_address_switch={0}, group_address_dimm={0}, group_address_dimm_feedback={2},name={3}>".format(self.group_address_switch,self.group_address_dimm,self.group_address_dimm_feedback,self.name)

    def set_internal_state(self, state):
        if state != self.state:
            self.state = state
            self.after_update_callback(self)

    def set_internal_brightness(self, brightness):
        if brightness != self.brightness:
            self.brightness = brightness
            self.after_update_callback(self)


    def send(self, group_address, payload = None):
        telegram = Telegram()
        telegram.group_address=group_address

        telegram.payload = payload
        self.xknx.telegrams.put(telegram)

    def set_on(self):
        self.send(self.group_address_switch, DPT_Binary(1) )
        self.set_internal_state(True)

    def set_off(self):
        self.send(self.group_address_switch, DPT_Binary(0) )
        self.set_internal_state(False)

    def set_brightness(self, brightness):
        self.send(self.group_address_dimm_feedback, DPT_Array(brightness) )
        self.set_internal_brightness(brightness)


    def sync_state(self):
        if not self.group_address_dimm_feedback.is_set():
            print("group_address_dimm_feedback not defined for device {0}".format(self.get_name()))
            return

        telegram_switch = Telegram(self.group_address_switch, TelegramType.GROUP_READ)
        self.xknx.telegrams.put(telegram_switch)
        telegram_dimm = Telegram(self.group_address_dimm_feedback, TelegramType.GROUP_READ)
        self.xknx.telegrams.put(telegram_dimm)


    def process(self,telegram):
        if telegram.group_address == self.group_address_switch or (telegram.group_address == self.group_address_state):
            self._process_state(telegram)
        elif telegram.group_address == self.group_address_dimm_feedback:
            self._process_dimm(telegram) 

    def _process_dimm(self,telegram):
        if not isinstance(telegram.payload, DPT_Array) or len(telegram.payload.value) != 1:
            raise CouldNotParseTelegram()

        self.set_internal_brightness(telegram.payload.value[0])

    def _process_state(self,telegram):

        if not isinstance( telegram.payload, DPT_Binary ):
            raise CouldNotParseTelegram()

        if telegram.payload.value == 0 :
            self.set_internal_state(False)
        elif telegram.payload.value == 1 :
            self.set_internal_state(True)
        else:
            raise CouldNotParseTelegram()

