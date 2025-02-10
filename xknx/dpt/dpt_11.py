"""Implementation of the KNX date data point."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import datetime
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class KNXDate(DPTComplexData):
    """Class for KNX Date."""

    year: int
    month: int
    day: int

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> KNXDate:
        """Init from a dictionary."""
        try:
            year = int(data["year"])
            month = int(data["month"])
            day = int(data["day"])
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for KNXDate: {err}") from err
        return cls(year=year, month=month, day=day)

    def as_dict(self) -> dict[str, int]:
        """Return object as dictionary."""
        return {
            "year": self.year,
            "month": self.month,
            "day": self.day,
        }

    def as_date(self) -> datetime.date:
        """Return datetime object."""
        return datetime.date(self.year, self.month, self.day)

    @classmethod
    def from_date(cls, date: datetime.date) -> KNXDate:
        """Return KNXDate object from a datetime.date object."""
        return cls(date.year, date.month, date.day)


class DPTDate(DPTComplex[KNXDate]):
    """Abstraction for KNX 3 octet date (DPT 11.001)."""

    data_type = KNXDate
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 11
    dpt_sub_number = 1
    value_type = "date"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> KNXDate:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)

        day = raw[0] & 0x1F
        month = raw[1] & 0x0F
        year = raw[2] & 0x7F
        if not DPTDate._test_range(day, month, year):
            raise ConversionError("Could not parse DPTDate", raw=raw)

        if year >= 90:
            year += 1900
        else:
            year += 2000

        return KNXDate(year, month, day)

    @classmethod
    def _to_knx(cls, value: KNXDate) -> DPTArray:
        """Serialize to KNX/IP raw data."""

        def _knx_year(year: int) -> int:
            if 2000 <= year < 2090:
                return year - 2000
            if 1990 <= year < 2000:
                return year - 1900
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}. Year out of range 1990..2089",
                year=year,
            )

        knx_year = _knx_year(value.year)

        if not DPTDate._test_range(value.day, value.month, knx_year):
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}. Value out of range", value=value
            )

        return DPTArray(
            (
                value.day,
                value.month,
                knx_year,
            )
        )

    @staticmethod
    def _test_range(day: int, month: int, knx_year: int) -> bool:
        """Test if the values are in the correct range."""
        return 1 <= day <= 31 and 1 <= month <= 12 and 0 <= knx_year <= 99
