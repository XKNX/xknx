"""
Module TravelCalculator provides functionality for predicting the current position of a Cover.

E.g.:

* Given a Cover that takes 100 seconds to travel from top to bottom.
* Starting from position 90, directed to position 60 at time 0.
* At time 10 TravelCalculator will return position 80 (final position not reached).
* At time 20 TravelCalculator will return position 70 (final position not reached).
* At time 30 TravelCalculator will return position 60 (final position reached).
"""
from __future__ import annotations

from enum import Enum
import time


class TravelStatus(Enum):
    """Enum class for travel status."""

    DIRECTION_UP = 1
    DIRECTION_DOWN = 2
    STOPPED = 3


class TravelCalculator:
    """Class for calculating the current position of a cover."""

    def __init__(self, travel_time_down: float, travel_time_up: float) -> None:
        """Initialize TravelCalculator class."""
        self.last_known_position: int | None = None
        self.position_confirmed: bool = False

        self.travel_time_down = travel_time_down
        self.travel_time_up = travel_time_up

        self.travel_to_position: int | None = None
        self.travel_started_time: float = 0.0
        self.travel_direction = TravelStatus.STOPPED

        # 100 is closed, 0 is fully open
        self.position_closed: int = 100
        self.position_open: int = 0

    def set_position(self, position: int) -> None:
        """Set position and target of cover."""
        self.travel_to_position = position
        self.update_position(position)

    def update_position(self, position: int) -> None:
        """Update known position of cover."""
        self.last_known_position = position
        if position == self.travel_to_position:
            self.position_confirmed = True

    def stop(self) -> None:
        """Stop traveling."""
        stop_position = self.current_position()
        if stop_position is None:
            return
        self.last_known_position = stop_position
        self.travel_to_position = stop_position
        self.position_confirmed = False
        self.travel_direction = TravelStatus.STOPPED

    def start_travel(self, travel_to_position: int) -> None:
        """Start traveling to position."""
        if self.last_known_position is None:
            self.set_position(travel_to_position)
            return
        self.stop()
        self.travel_started_time = time.time()
        self.travel_to_position = travel_to_position
        self.position_confirmed = False

        self.travel_direction = (
            TravelStatus.DIRECTION_DOWN
            if travel_to_position > self.last_known_position
            else TravelStatus.DIRECTION_UP
        )

    def start_travel_up(self) -> None:
        """Start traveling up."""
        self.start_travel(self.position_open)

    def start_travel_down(self) -> None:
        """Start traveling down."""
        self.start_travel(self.position_closed)

    def current_position(self) -> int | None:
        """Return current (calculated or known) position."""
        if not self.position_confirmed:
            return self._calculate_position()
        return self.last_known_position

    def is_traveling(self) -> bool:
        """Return if cover is traveling."""
        return self.current_position() != self.travel_to_position

    def is_opening(self) -> bool:
        """Return if the cover is opening."""
        return (
            self.is_traveling() and self.travel_direction == TravelStatus.DIRECTION_UP
        )

    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        return (
            self.is_traveling() and self.travel_direction == TravelStatus.DIRECTION_DOWN
        )

    def position_reached(self) -> bool:
        """Return if cover has reached designated position."""
        return self.current_position() == self.travel_to_position

    def is_open(self) -> bool:
        """Return if cover is (fully) open."""
        return self.current_position() == self.position_open

    def is_closed(self) -> bool:
        """Return if cover is (fully) closed."""
        return self.current_position() == self.position_closed

    def _calculate_position(self) -> int | None:
        """Return calculated position."""
        if self.travel_to_position is None or self.last_known_position is None:
            return self.last_known_position
        relative_position = self.travel_to_position - self.last_known_position

        def position_reached_or_exceeded(relative_position: int) -> bool:
            """Return if designated position was reached."""
            if (
                relative_position <= 0
                and self.travel_direction == TravelStatus.DIRECTION_DOWN
            ):
                return True
            if (
                relative_position >= 0
                and self.travel_direction == TravelStatus.DIRECTION_UP
            ):
                return True
            return False

        if position_reached_or_exceeded(relative_position):
            return self.travel_to_position

        travel_time = self._calculate_travel_time(relative_position)
        if time.time() > self.travel_started_time + travel_time:
            return self.travel_to_position

        progress = (time.time() - self.travel_started_time) / travel_time
        position = self.last_known_position + relative_position * progress
        return int(position)

    def _calculate_travel_time(self, relative_position: int) -> float:
        """Calculate time to travel to relative position."""
        travel_direction = (
            TravelStatus.DIRECTION_UP
            if relative_position < 0
            else TravelStatus.DIRECTION_DOWN
        )
        travel_time_full = (
            self.travel_time_up
            if travel_direction == TravelStatus.DIRECTION_UP
            else self.travel_time_down
        )
        travel_range = self.position_closed - self.position_open

        return travel_time_full * abs(relative_position) / travel_range

    def __eq__(self, other: object | None) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__
