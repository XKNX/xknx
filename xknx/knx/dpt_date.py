"""Implementation of the KNX date data point."""

import time

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTDate(DPTBase):
    """Abstraction for KNX 3 octet date (DPT 11.001)."""

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 3)

        day = raw[0] & 0x1F
        month = raw[1] & 0x0F
        year = raw[2] & 0x7F

        if not DPTDate._test_range(day, month, year):
            raise ConversionError("Cant parse DPTDate", raw=raw)

        if year >= 90:
            year += 1900
        else:
            year += 2000

        return {
            'day': day,
            'month': month,
            'year': year
        }

    @classmethod
    def to_knx(cls, values):
        """Serialize to KNX/IP raw data from dict with elements day,month,year."""
        def _knx_year(year):
            if year >= 2000 and year < 2090:
                return year-2000
            elif year >= 1990 and year < 2000:
                return year-1900
            raise ConversionError("Cant serialize DPTDate", year=year)

        if not isinstance(values, dict):
            raise ConversionError("Cant serialize DPTDate", values=values)
        day = values.get('day', 0)
        month = values.get('month', 0)
        year = _knx_year(values.get('year', 0))

        if not DPTDate._test_range(day, month, year):
            raise ConversionError("Cant serialize DPTDate", values=values)

        return day, month, year

    @classmethod
    def _current_date(cls):
        """Return current local date as struct."""
        localtime = time.localtime()
        day = localtime.tm_mday
        month = localtime.tm_mon
        year = localtime.tm_year
        return {
            'day': day,
            'month': month,
            'year': year
        }

    @classmethod
    def current_date_as_knx(cls):
        """Return current local date as KNX bytes."""
        return cls.to_knx(cls._current_date())

    @staticmethod
    def _test_range(day, month, year):
        """Test if the values are in the correct range."""
        if day < 1 or day > 31:
            return False
        if month < 1 or month > 12:
            return False
        if year < 0 or year > 99:
            return False
        return True
