from enum import Enum
import time

class PositionType(Enum):
    UNKNOWN = 1
    CALCULATED = 2
    CONFIRMED = 3

class TravelStatus(Enum):
    DIRECTION_UP = 1
    DIRECTION_DOWN = 2
    STOPPED = 3


class TravelCalculator:


    def  __init__(self, travel_time_down, travel_time_up):
        self.position_type = PositionType.UNKNOWN
        self.last_known_position = 0

        self.travel_time_down = travel_time_down
        self.travel_time_up  = travel_time_up

        self.travel_to_position = 0
        self.travel_started_time = 0
        self.travel_direction = TravelStatus.STOPPED
        #TODO: Move to DPT Types class issue #10
        self.minimum_position_down = 256 # excluding
        self.maximum_position_up = 0

    def set_position(self, position):
        self.last_known_position = position
        self.travel_to_position = position
        self.position_type = PositionType.CONFIRMED

    def stop(self):
        self.last_known_position = self.current_position()
        self.travel_to_position = self.last_known_position
        self.position_type = PositionType.CALCULATED
        self.travel_direction = TravelStatus.STOPPED

    def start_travel(self, travel_to_position ):
        self.stop()

        self.travel_started_time = self.current_time()
        self.travel_to_position = travel_to_position
        self.position_type = PositionType.CALCULATED

        if travel_to_position < self.last_known_position:
            self.travel_direction = TravelStatus.DIRECTION_UP
        else:
            self.travel_direction = TravelStatus.DIRECTION_DOWN

    def start_travel_up(self):
        self.start_travel(self.maximum_position_up)

    def start_travel_down(self):
        self.start_travel(self.minimum_position_down)

    def current_position(self):
        if ( self.position_type == PositionType.CALCULATED ):
            return self._calculate_position()
        return self.last_known_position

    def is_travelling(self):
        return self.current_position() !=  self.travel_to_position

    def position_reached(self):
        return self.current_position() ==  self.travel_to_position

    def is_open(self):
        return self.current_position() == self.maximum_position_up

    def is_closed(self):
        return self.current_position() == self.minimum_position_down

    def _calculate_position(self):
        relative_position = self.travel_to_position - self.last_known_position

        def position_reached_or_exceeded(relative_position):
            if relative_position <= 0 and self.travel_direction == TravelStatus.DIRECTION_DOWN :
                return True
            if relative_position >= 0 and self.travel_direction == TravelStatus.DIRECTION_UP :
                return True
            return False

        if position_reached_or_exceeded(relative_position):
             return self.travel_to_position

        travel_time = self._calculate_travel_time( relative_position )
        if self.current_time() > self.travel_started_time + travel_time:
            return self.travel_to_position
        progress = (self.current_time()-self.travel_started_time)/travel_time
        position = self.last_known_position + relative_position * progress
        return int(position)

    def _calculate_travel_time(self, relative_position):
        travel_direction = \
                    TravelStatus.DIRECTION_UP \
                    if relative_position < 0 else \
                    TravelStatus.DIRECTION_DOWN
        travel_time_full = \
                    self.travel_time_up \
                    if travel_direction == TravelStatus.DIRECTION_UP else \
                    self.travel_time_down
        return travel_time_full * abs(relative_position) / (self.minimum_position_down-self.maximum_position_up)

    def current_time(self):
        # time_set_from_outside is  used within unit tests
        if hasattr(self, 'time_set_from_outside'):
            return self.time_set_from_outside
        return time.time()


