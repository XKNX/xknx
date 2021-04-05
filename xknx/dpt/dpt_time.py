"""Implementation of Basic KNX Time."""
from __future__ import annotations

import time

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTTime(DPTBase):
    """
    Abstraction for KNX 3 Octet Time.

    DPT 10.001
    """

    payload_length = 3

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> time.struct_time:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)

        weekday = (raw[0] & 0xE0) >> 5
        hours = raw[0] & 0x1F
        minutes = raw[1] & 0x3F
        seconds = raw[2] & 0x3F

        if not DPTTime._test_range(weekday, hours, minutes, seconds):
            raise ConversionError("Could not parse DPTTime", raw=raw)

        try:
            if weekday == 0:
                # struct_time has no concept of "no day"; default to monday (for %w this is 1)
                weekday = 1
            elif weekday == 7:
                # in knx Sunday is 7; in strftime %w its 0
                weekday = 0
            # strptime conversion used for catching exceptions; filled with default values
            return time.strptime(
                f"{hours} {minutes} {seconds} {weekday}", "%H %M %S %w"
            )
        except ValueError:
            raise ConversionError("Could not parse DPTTime", raw=raw)

    @classmethod
    def to_knx(cls, value: time.struct_time) -> tuple[int, int, int]:
        """Serialize to KNX/IP raw data from dict with elements weekday,hours,minutes,seconds."""
        if not isinstance(value, time.struct_time):
            raise ConversionError(
                "Could not serialize DPTTime - time.struct_time expected", value=value
            )

        _default_time = time.strptime("", "")
        weekday = 0
        # if 0 year, 1 month, 2 day, 6 weekday, 7 yearday, 8 dst are equal to default assume "any weekday" (0)
        for index in [0, 1, 2, 6, 7, 8]:
            if value[index] is not _default_time[index]:
                weekday = value.tm_wday + 1
                break

        return (weekday << 5 | value.tm_hour, value.tm_min, value.tm_sec)

    @staticmethod
    def _test_range(weekday: int, hours: int, minutes: int, seconds: int) -> bool:
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
