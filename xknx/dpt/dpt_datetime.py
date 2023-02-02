"""Implementation of the KNX datetime data point."""
from __future__ import annotations

import time

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTDateTime(DPTBase):
    """Abstraction for KNX 8 octet datetime (DPT 19.001)."""

    payload_length = 8

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> time.struct_time:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)

        year = raw[0] + 1900
        month = raw[1] & 0x0F
        day = raw[2] & 0x3F
        weekday = (raw[3] & 0xE0) >> 5
        hours = raw[3] & 0x1F
        minutes = raw[4] & 0x3F
        seconds = raw[5] & 0x3F

        fault = raw[6] & 0x80
        # workingday_invalid = raw[6] & 0x20
        year_invalid = raw[6] & 0x10
        date_invalid = raw[6] & 0x08  # month, day
        weekday_invalid = raw[6] & 0x04
        time_invalid = raw[6] & 0x02  # hours, minutes, seconds

        if fault:
            raise ConversionError("DPTDateTime received corrupted data", raw=raw)

        try:
            if weekday == 0:
                # struct_time has no concept of "no/any day"
                weekday_invalid = True
            elif weekday == 7:
                # in knx Sunday is 7; in strftime %w its 0
                weekday = 0
            # string conversion used for catching exceptions and inferring invalid data
            _time_strings = []
            _time_formats = []
            if not year_invalid:
                _time_strings.append(str(year))
                _time_formats.append("%Y")
            if not date_invalid:
                _time_strings.extend([str(month), str(day)])
                _time_formats.extend(["%m", "%d"])
            if not time_invalid:
                _time_strings.extend([str(hours), str(minutes), str(seconds)])
                _time_formats.extend(["%H", "%M", "%S"])
            if not weekday_invalid:
                _time_strings.append(str(weekday))
                _time_formats.append("%w")
            time_string = " ".join(_time_strings)
            time_format = " ".join(_time_formats)

            return time.strptime(time_string, time_format)

        except ValueError:
            raise ConversionError("Could not parse DPTDateTime", raw=raw)

    @classmethod
    def to_knx(cls, value: time.struct_time) -> tuple[int, ...]:
        """Serialize to KNX/IP raw data from time.struct_time."""
        if not isinstance(value, time.struct_time):
            raise ConversionError("Could not serialize DPTDateTime", value=value)

        knx_year = (value.tm_year - 1900) & 0xFF
        month = value.tm_mon
        day = value.tm_mday
        weekday = value.tm_wday + 1
        hours = value.tm_hour
        minutes = value.tm_min
        seconds = value.tm_sec
        dst = value.tm_isdst == 1  # tm_isdst can be -1

        return (
            knx_year,
            month,
            day,
            weekday << 5 | hours,
            minutes,
            seconds,
            0x20 | dst,  # 0x20 working day not valid
            0x80,  # assume clock with ext. sync signal
        )
