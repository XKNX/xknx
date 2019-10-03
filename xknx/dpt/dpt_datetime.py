"""Implementation of the KNX datetime data point."""

import time

from xknx.exceptions import ConversionError

from .dpt import DPTBase, DPTWeekday


class DPTDateTime(DPTBase):
    """Abstraction for KNX 8 octet datetime (DPT 19.001)."""

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 8)

        year = raw[0] + 1900
        month = raw[1] & 0x0F
        day = raw[2] & 0x3F
        weekday = (raw[3] & 0xE0) >> 5
        hours = raw[3] & 0x1F
        minutes = raw[4] & 0x3F
        seconds = raw[5] & 0x3F

        if not DPTDateTime._test_range(year, month, day, weekday, hours, minutes, seconds):
            raise ConversionError("Could not parse DPTDateTime", raw=raw)

        return {
            'year': year,
            'month': month,
            'day': day,
            'weekday': DPTWeekday(weekday),
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds
        }

    @classmethod
    def to_knx(cls, values):
        """Serialize to KNX/IP raw data from dict with elements year,month,day,weekday,hours,minutes,seconds."""
        if not isinstance(values, dict):
            raise ConversionError("Cant serialize DPTDateTime", values=values)

        year = values.get('year', 1900)
        month = values.get('month', 1)
        day = values.get('day', 1)
        weekday = values.get('weekday', DPTWeekday.NONE).value
        hours = values.get('hours', 0)
        minutes = values.get('minutes', 0)
        seconds = values.get('seconds', 0)

        if not DPTDateTime._test_range(year, month, day, weekday, hours, minutes, seconds):
            raise ConversionError("Cant serialize DPTDateTime", values=values)

        return year - 1900, month, day, weekday << 5 | hours, minutes, seconds, 0, 0

    @classmethod
    def current_datetime_as_knx(cls):
        """Return current local datetime as KNX bytes."""
        return cls.to_knx(cls._current_datetime())

    @classmethod
    def _current_datetime(cls):
        """Return current local time as struct."""
        localtime = time.localtime()
        year = localtime.tm_year
        month = localtime.tm_mon
        day = localtime.tm_mday
        weekday = localtime.tm_wday + 1
        hours = localtime.tm_hour
        minutes = localtime.tm_min
        seconds = localtime.tm_sec
        return {
            'year': year,
            'month': month,
            'day': day,
            'weekday': DPTWeekday(weekday),
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds
        }

    @staticmethod
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-return-statements
    def _test_range(year, month, day, weekday, hours, minutes, seconds):
        """Test if the values are in the correct range."""
        if year < 1900 or year > 2155:
            return False
        if month < 1 or month > 12:
            return False
        if day < 1 or day > 31:
            return False
        if weekday < 0 or weekday > 7:
            return False
        if hours < 0 or hours > 23:
            return False
        if minutes < 0 or minutes > 59:
            return False
        if seconds < 0 or seconds > 59:
            return False
        return True
