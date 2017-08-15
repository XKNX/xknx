"""Implementation of Basic KNX Time."""

from enum import Enum
import time

from xknx.exceptions import ConversionError
from .dpt import DPTBase


class DPTWeekday(Enum):
    """Enum class for week days."""

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7
    NONE = 0


class DPTTime(DPTBase):
    """
    Abstraction for KNX 3 Octet Time.

    DPT 10.001
    """

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 3)

        day = (raw[0] & 0xE0) >> 5
        hours = raw[0] & 0x1F
        minutes = raw[1] & 0x3F
        seconds = raw[2] & 0x3F

        if not DPTTime._test_range(day, hours, minutes, seconds):
            raise ConversionError(raw)

        return {'day': DPTWeekday(day),
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds}

    @classmethod
    def to_knx(cls, values):
        """Serialize to KNX/IP raw data from dict with elements day,hours,minutes,seconds."""
        if not isinstance(values, dict):
            raise ConversionError(values)
        day = values.get('day', DPTWeekday.NONE).value
        hours = values.get('hours', 0)
        minutes = values.get('minutes', 0)
        seconds = values.get('seconds', 0)

        if not DPTTime._test_range(day, hours, minutes, seconds):
            raise ConversionError(values)

        return day << 5 | hours, minutes, seconds

    @classmethod
    def _current_time(cls):
        """Return current local time as struct."""
        localtime = time.localtime()
        day = localtime.tm_wday + 1
        hours = localtime.tm_hour
        minutes = localtime.tm_min
        seconds = localtime.tm_sec
        return {'day': DPTWeekday(day),
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds}

    @classmethod
    def current_time_as_knx(cls):
        """Return current local time as KNX bytes."""
        return cls.to_knx(cls._current_time())

    @staticmethod
    def _test_range(day, hours, minutes, seconds):
        """Test if values are in the correct value range."""
        if day < 0 or day > 7:
            return False
        if hours < 0 or hours > 23:
            return False
        if minutes < 0 or minutes > 59:
            return False
        if seconds < 0 or seconds > 59:
            return False
        return True
