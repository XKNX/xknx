"""Implementation of Basic KNX Time."""

import time

from xknx.exceptions import ConversionError

from .dpt import DPTBase, DPTWeekday


class DPTTime(DPTBase):
    """
    Abstraction for KNX 3 Octet Time.

    DPT 10.001
    """

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 3)

        weekday = (raw[0] & 0xE0) >> 5
        hours = raw[0] & 0x1F
        minutes = raw[1] & 0x3F
        seconds = raw[2] & 0x3F

        if not DPTTime._test_range(weekday, hours, minutes, seconds):
            raise ConversionError("Cant parse DPTTime", raw=raw)

        return {'weekday': DPTWeekday(weekday),
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds}

    @classmethod
    def to_knx(cls, values):
        """Serialize to KNX/IP raw data from dict with elements weekday,hours,minutes,seconds."""
        if not isinstance(values, dict):
            raise ConversionError("Cant serialize DPTTime", values=values)
        weekday = values.get('weekday', DPTWeekday.NONE).value
        hours = values.get('hours', 0)
        minutes = values.get('minutes', 0)
        seconds = values.get('seconds', 0)

        if not DPTTime._test_range(weekday, hours, minutes, seconds):
            raise ConversionError("Cant serialize DPTTime", values=values)

        return weekday << 5 | hours, minutes, seconds

    @classmethod
    def _current_time(cls):
        """Return current local time as struct."""
        localtime = time.localtime()
        weekday = localtime.tm_wday + 1
        hours = localtime.tm_hour
        minutes = localtime.tm_min
        seconds = localtime.tm_sec
        return {'weekday': DPTWeekday(weekday),
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds}

    @classmethod
    def current_time_as_knx(cls):
        """Return current local time as KNX bytes."""
        return cls.to_knx(cls._current_time())

    @staticmethod
    def _test_range(weekday, hours, minutes, seconds):
        """Test if values are in the correct value range."""
        if weekday < 0 or weekday > 7:
            return False
        if hours < 0 or hours > 23:
            return False
        if minutes < 0 or minutes > 59:
            return False
        if seconds < 0 or seconds > 59:
            return False
        return True
