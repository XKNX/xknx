"""Implementation of Basic KNX Time."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import datetime
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData, DPTEnumData
from .payload import DPTArray, DPTBinary


class KNXDay(DPTEnumData):
    """Enum for the different KNX days."""

    NO_DAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


@dataclass(slots=True)
class KNXTime(DPTComplexData):
    """Class for KNX Time."""

    hour: int
    minutes: int
    seconds: int
    day: KNXDay = KNXDay.NO_DAY

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> KNXTime:
        """Init from a dictionary."""
        try:
            hour = int(data["hour"])
            minutes = int(data["minutes"])
            seconds = int(data["seconds"])
            day = KNXDay.parse(data.get("day", KNXDay.NO_DAY))
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for KNXTime: {err}") from err
        return cls(hour=hour, minutes=minutes, seconds=seconds, day=day)

    def as_dict(self) -> dict[str, int | str]:
        """Create a JSON serializable dictionary."""
        return {
            "hour": self.hour,
            "minutes": self.minutes,
            "seconds": self.seconds,
            "day": self.day.name.lower(),
        }

    def as_time(self) -> datetime.time:
        """Return time object. Ignoring day field."""
        return datetime.time(self.hour, self.minutes, self.seconds)

    @classmethod
    def from_time(cls, time: datetime.time) -> KNXTime:
        """Return KNXTime object from time object. Day field is set to NO_DAY."""
        return cls(time.hour, time.minute, time.second)


class DPTTime(DPTComplex[KNXTime]):
    """
    Abstraction for KNX 3 Octet Time.

    DPT 10.001
    """

    data_type = KNXTime
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 10
    dpt_sub_number = 1
    value_type = "time"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> KNXTime:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)

        weekday = (raw[0] & 0xE0) >> 5  # can not be out of range - 3 bits 0..7
        hours = raw[0] & 0x1F
        minutes = raw[1] & 0x3F
        seconds = raw[2] & 0x3F
        try:
            DPTTime._test_range(hours, minutes, seconds)
        except ValueError as err:
            raise ConversionError(f"Could not parse {cls.dpt_name()}: {err}") from err
        return KNXTime(
            hour=hours, minutes=minutes, seconds=seconds, day=KNXDay(weekday)
        )

    @classmethod
    def _to_knx(cls, value: KNXTime) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            DPTTime._test_range(value.hour, value.minutes, value.seconds)
        except ValueError as err:
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}: {err}"
            ) from err
        return DPTArray(
            (
                value.day.value << 5 | value.hour,
                value.minutes,
                value.seconds,
            )
        )

    @staticmethod
    def _test_range(hour: int, minutes: int, seconds: int) -> None:
        """Test if values are in the correct value range."""
        if not 0 <= hour <= 23:
            raise ValueError(f"Hour out of range 0..23: {hour}")
        if not 0 <= minutes <= 59:
            raise ValueError(f"Minutes out of range 0..59: {minutes}")
        if not 0 <= seconds <= 59:
            raise ValueError(f"Seconds out of range 0..59: {seconds}")
