from xknx.knx import Address, Telegram, TelegramType, DPTBinary, DPTArray
from .device import Device
from .travelcalculator import TravelCalculator
from .exception import CouldNotParseTelegram

class Shutter(Device):

    # Average typical travel time of a shutter
    DEFAULT_TRAVEL_TIME_DOWN = 22
    DEFAULT_TRAVEL_TIME_UP = 22

    def __init__(self,
                 xknx,
                 name,
                 group_address_long=None,
                 group_address_short=None,
                 group_address_position=None,
                 group_address_position_feedback=None,
                 travel_time_down=DEFAULT_TRAVEL_TIME_DOWN,
                 travel_time_up=DEFAULT_TRAVEL_TIME_UP):
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name)

        if isinstance(group_address_long, (str, int)):
            group_address_long = Address(group_address_long)
        if isinstance(group_address_short, (str, int)):
            group_address_short = Address(group_address_short)
        if isinstance(group_address_position, (str, int)):
            group_address_position = Address(group_address_position)
        if isinstance(group_address_position_feedback, (str, int)):
            group_address_position_feedback = \
                Address(group_address_position_feedback)

        self.group_address_long = group_address_long
        self.group_address_short = group_address_short
        self.group_address_position = group_address_position
        self.group_address_position_feedback = group_address_position_feedback
        self.travel_time_down = travel_time_down
        self.travel_time_up = travel_time_up

        self.travelcalculator = TravelCalculator(
            travel_time_down,
            travel_time_up)


    @classmethod
    def from_config(cls, xknx, name, config):
        group_address_long = \
            config.get('group_address_long')
        group_address_short = \
            config.get('group_address_short')
        group_address_position = \
            config.get('group_address_position')
        group_address_position_feedback = \
            config.get('group_address_position_feedback')
        travel_time_down = \
            config.get('travel_time_down', cls.DEFAULT_TRAVEL_TIME_DOWN)
        travel_time_up = \
            config.get('travel_time_up', cls.DEFAULT_TRAVEL_TIME_UP)

        return cls(xknx,
                   name,
                   group_address_long=group_address_long,
                   group_address_short=group_address_short,
                   group_address_position=group_address_position,
                   group_address_position_feedback=\
                        group_address_position_feedback,
                   travel_time_down=travel_time_down,
                   travel_time_up=travel_time_up)


    def has_group_address(self, group_address):
        return (self.group_address_long == group_address) \
            or (self.group_address_short == group_address) \
            or (self.group_address_position_feedback == group_address)


    def supports_direct_positioning(self):
        return self.group_address_position is not None


    def __str__(self):
        return "<Shutter name={0}, " \
                "group_address_long={1}, " \
                "group_address_short={2}, " \
                "group_address_position={3}, " \
                "group_address_position_feedback={4}, " \
                "travel_time_down={5}, " \
                "travel_time_up={6}>" \
                .format(
                    self.name,
                    self.group_address_long,
                    self.group_address_short,
                    self.group_address_position,
                    self.group_address_position_feedback,
                    self.travel_time_down,
                    self.travel_time_up)


    def send(self, group_address, payload):
        telegram = Telegram()
        telegram.group_address = group_address
        telegram.payload = payload
        self.xknx.telegrams.put_nowait(telegram)


    def set_down(self):
        if self.group_address_long is None:
            print("group_address_long not defined for device {0}" \
                .format(self.get_name()))
            return
        self.send(self.group_address_long, DPTBinary(1))
        self.travelcalculator.start_travel_down()


    def set_up(self):
        if self.group_address_long is None:
            print("group_address_long not defined for device {0}" \
                .format(self.get_name()))
            return
        self.send(self.group_address_long, DPTBinary(0))
        self.travelcalculator.start_travel_up()


    def set_short_down(self):
        if self.group_address_short is None:
            print("group_address_short not defined for device {0}" \
                .format(self.get_name()))
            return
        self.send(self.group_address_short, DPTBinary(1))


    def set_short_up(self):
        if self.group_address_short is None:
            print("group_address_short not defined for device {0}" \
                .format(self.get_name()))
            return
        self.send(self.group_address_short, DPTBinary(0))


    def stop(self):
        # Thats the KNX way of doing this. electrical engineers ... m-)
        self.set_short_down()
        self.travelcalculator.stop()


    def set_position(self, position):
        if not self.supports_direct_positioning():

            current_position = self.current_position()
            if position > current_position:
                self.send(self.group_address_long, DPTBinary(1))
            elif position < current_position:
                self.send(self.group_address_long, DPTBinary(0))
            self.travelcalculator.start_travel(position)
            return
        self.send(self.group_address_position, DPTArray(position))
        self.travelcalculator.start_travel(position)


    def auto_stop_if_necessary(self):
        # If device does not support auto_positioning,
        # we have to ttop the device when position is reached.
        # unless device was traveling to fully open
        # or fully closed state
        if (
                not self.supports_direct_positioning() and
                self.position_reached() and
                not self.is_open() and
                not self.is_closed()):
            self.stop()


    def do(self, action):
        if action == "up":
            self.set_up()
        elif action == "short_up":
            self.set_short_up()
        elif action == "down":
            self.set_down()
        elif action == "short_down":
            self.set_short_down()
        else:
            print("{0}: Could not understand action {1}" \
                .format(self.get_name(), action))


    def sync_state(self):
        if self.group_address_position_feedback is None:
            print("group_position not defined for device {0}" \
                .format(self.get_name()))
            return
        if self.travelcalculator.is_traveling():
            # Cover is traveling, requesting state will return false results
            return

        telegram = Telegram(
            self.group_address_position_feedback,
            TelegramType.GROUP_READ)
        self.xknx.telegrams.put_nowait(telegram)


    def process(self, telegram):
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 1:
            raise CouldNotParseTelegram()

        self.travelcalculator.set_position(telegram.payload.value[0])
        self.after_update()


    def current_position(self):
        return self.travelcalculator.current_position()


    def is_traveling(self):
        return self.travelcalculator.is_traveling()


    def position_reached(self):
        return self.travelcalculator.position_reached()


    def is_open(self):
        return self.travelcalculator.is_open()


    def is_closed(self):
        return self.travelcalculator.is_closed()


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
