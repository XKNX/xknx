"""Implementation of the KNX datetime data point."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import datetime
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData, DPTEnumData
from .payload import DPTArray, DPTBinary


class KNXDayOfWeek(DPTEnumData):
    """Enum for the different KNX days."""

    ANY_DAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


@dataclass(slots=True)
class KNXDateTime(DPTComplexData):
    """
    Class for KNX DateTime.

    `year`, `day_of_week` and `working_day` may be None if invalid.
    `month` and `day` have to be both either int or None (invalid).
    `hour`, `minutes` and `seconds` all have to be either int or None (invalid).
    """

    year: int | None = None
    month: int | None = None
    day: int | None = None
    hour: int | None = None
    minutes: int | None = None
    seconds: int | None = None

    day_of_week: KNXDayOfWeek | None = None

    fault: bool = False
    working_day: bool | None = None
    dst: bool = False
    external_sync: bool = False
    source_reliable: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> KNXDateTime:
        """Init from a dictionary."""
        _data = {**data}
        if "day_of_week" in data:
            _data["day_of_week"] = KNXDayOfWeek.parse(data["day_of_week"])
        try:
            return cls(**_data)
        except TypeError as err:
            raise ValueError(f"Invalid value for KNXDateTime: {err}") from err

    def as_dict(self) -> dict[str, int | str]:
        """Create a JSON serializable dictionary."""
        _data = asdict(self)
        if self.day_of_week is not None:
            _data["day_of_week"] = self.day_of_week.name.lower()
        return _data

    def as_datetime(self) -> datetime.datetime:
        """Return datetime object."""
        try:
            return datetime.datetime(
                self.year,  # type: ignore[arg-type]
                self.month,  # type: ignore[arg-type]
                self.day,  # type: ignore[arg-type]
                self.hour,  # type: ignore[arg-type]
                self.minutes,  # type: ignore[arg-type]
                self.seconds,  # type: ignore[arg-type]
            )
        except (TypeError, ValueError) as err:
            raise ValueError(
                f"KNXDateTime not convertible to datetime object: {err}"
            ) from err

    @classmethod
    def from_datetime(cls, dt: datetime.datetime) -> KNXDateTime:
        """Return KNXDateTime object from a datetime.datetime object."""
        return cls(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minutes=dt.minute,
            seconds=dt.second,
        )


class DPTDateTime(DPTComplex[KNXDateTime]):
    """Abstraction for KNX 8 octet datetime (DPT 19.001)."""

    data_type = KNXDateTime
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 19
    dpt_sub_number = 1
    value_type = "datetime"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> KNXDateTime:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)

        year = raw[0] + 1900
        month = raw[1] & 0b00001111
        day = raw[2] & 0b00011111
        weekday = (raw[3] & 0b11100000) >> 5
        hour = raw[3] & 0b00011111
        minutes = raw[4] & 0b00111111
        seconds = raw[5] & 0b00111111

        fault = bool(raw[6] & 0b10000000)
        _working_day = bool(raw[6] & 0b01000000)
        _working_day_invalid = bool(raw[6] & 0b00100000)
        _year_invalid = bool(raw[6] & 0b00010000)
        _date_invalid = bool(raw[6] & 0b00001000)  # month, day
        _weekday_invalid = bool(raw[6] & 0b00000100)
        _time_invalid = bool(raw[6] & 0b00000010)  # hour, minutes, seconds
        dst = bool(raw[6] & 0b00000001)

        external_sync = bool(raw[7] & 0b10000000)
        source_reliable = bool(raw[7] & 0b01000000)

        knx_date_time = KNXDateTime(
            year=year if not _year_invalid else None,
            month=month if not _date_invalid else None,
            day=day if not _date_invalid else None,
            day_of_week=KNXDayOfWeek(weekday) if not _weekday_invalid else None,
            hour=hour if not _time_invalid else None,
            minutes=minutes if not _time_invalid else None,
            seconds=seconds if not _time_invalid else None,
            fault=fault,
            working_day=_working_day if not _working_day_invalid else None,
            dst=dst,
            external_sync=external_sync,
            source_reliable=source_reliable,
        )
        try:
            cls._test_range(knx_date_time)
        except ValueError as err:
            raise ConversionError(f"Could not parse {cls.dpt_name()}: {err}") from err
        return knx_date_time

    @classmethod
    def _to_knx(cls, value: KNXDateTime) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            cls._test_range(value)
        except ValueError as err:
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}: {err}"
            ) from err

        knx_year = (value.year - 1900) & 0xFF if value.year is not None else 0

        month_day_invalid = None in (value.month, value.day)
        month = value.month if value.month is not None else 0
        day = value.day if value.day is not None else 0

        day_of_week = value.day_of_week.value if value.day_of_week is not None else 0

        time_invalid = None in (value.hour, value.minutes, value.seconds)
        hour = value.hour if value.hour is not None else 0
        minutes = value.minutes if value.minutes is not None else 0
        seconds = value.seconds if value.seconds is not None else 0

        return DPTArray(
            (
                knx_year,
                month,
                day,
                day_of_week << 5 | hour,
                minutes,
                seconds,
                (
                    value.fault << 7
                    | bool(value.working_day) << 6
                    | (value.working_day is None) << 5
                    | (value.year is None) << 4
                    | month_day_invalid << 3
                    | (value.day_of_week is None) << 2
                    | time_invalid << 1
                    | value.dst
                ),
                (value.external_sync << 7 | value.source_reliable << 6),
            )
        )

    @staticmethod
    def _test_range(value: KNXDateTime) -> None:
        """Test if date is in valid range."""
        if value.year is not None and not 1900 <= value.year <= 2155:
            raise ValueError(f"Year out of range 1900..2155: {value.year}")
        if value.month is not None and not 1 <= value.month <= 12:
            raise ValueError(f"Month out of range 1..12: {value.month}")
        if value.day is not None and not 1 <= value.day <= 31:
            raise ValueError(f"Day out of range 1..31: {value.day}")
        if value.hour is not None and not 0 <= value.hour <= 24:
            raise ValueError(f"Hour out of range 0..24: {value.hour}")
        if value.minutes is not None and not 0 <= value.minutes <= 59:
            raise ValueError(f"Minutes out of range 0..59: {value.minutes}")
        if value.seconds is not None and not 0 <= value.seconds <= 59:
            raise ValueError(f"Seconds out of range 0..59: {value.seconds}")
        if value.hour == 24 and (value.minutes != 0 or value.seconds != 0):
            raise ValueError(
                "Invalid time. When hour is 24, minutes and seconds have to be set to zero."
            )
