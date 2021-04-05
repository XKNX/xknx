"""Implementation of the KNX date data point."""
from __future__ import annotations

import time

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTDate(DPTBase):
    """Abstraction for KNX 3 octet date (DPT 11.001)."""

    payload_length = 3

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> time.struct_time:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)

        day = raw[0] & 0x1F
        month = raw[1] & 0x0F
        year = raw[2] & 0x7F

        if not DPTDate._test_range(day, month, year):
            raise ConversionError("Could not parse DPTDate", raw=raw)

        if year >= 90:
            year += 1900
        else:
            year += 2000

        try:
            # strptime conversion used for catching exceptions; filled with default values
            return time.strptime(f"{year} {month} {day}", "%Y %m %d")
        except ValueError:
            raise ConversionError("Could not parse DPTDate", raw=raw)

    @classmethod
    def to_knx(cls, value: time.struct_time) -> tuple[int, int, int]:
        """Serialize to KNX/IP raw data from time.struct_time."""

        def _knx_year(year: int) -> int:
            if 2000 <= year < 2090:
                return year - 2000
            if 1990 <= year < 2000:
                return year - 1900
            raise ConversionError("Could not serialize DPTDate", year=year)

        if not isinstance(value, time.struct_time):
            raise ConversionError("Could not serialize DPTDate", value=value)

        return (value.tm_mday, value.tm_mon, _knx_year(value.tm_year))

    @staticmethod
    def _test_range(day: int, month: int, year: int) -> bool:
        """Test if the values are in the correct range."""
        if day < 1 or day > 31:
            return False
        if month < 1 or month > 12:
            return False
        if year < 0 or year > 99:
            return False
        return True
