"""Implementation of the KNX DALI emergency converter test info data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, cast

from .dpt import DPTComplex, DPTComplexData, DPTComplexFieldSchema
from .dpt_7 import DPTTimePeriodHrs, DPTTimePeriodSec
from .dpt_19 import DPTDateTime, KNXDateTime
from .helpers.metadata import RANGE_UINT16
from .payload import DPTArray, DPTBinary


@dataclass
class _ConverterTestInfoDictSchemaFields:
    """Time period field definitions used for ConverterTestInfo.get_dict_schema()."""

    automated_test_interval: int = field(metadata=RANGE_UINT16)
    test_execution_time: int = field(metadata=RANGE_UINT16)


@dataclass(slots=True)
class ConverterTestInfo(DPTComplexData):
    """
    Representation of DALI emergency converter test info.

    `test_start`: start date and time of the preceding test execution
    `automated_test_interval`: interval of automated tests in hours 0..65535;
        0 if no automated testing is active
    `test_execution_time`: duration of the preceding test execution in seconds 0..65535

    The dict representation contains the fields of `test_start` (see KNXDateTime)
    next to the time periods.
    """

    test_start: KNXDateTime
    automated_test_interval: int
    test_execution_time: int

    _dict_schema_fields_class = _ConverterTestInfoDictSchemaFields

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConverterTestInfo:
        """Init from a dictionary."""
        try:
            date_time = {
                key: value
                for key, value in data.items()
                if key not in ("automated_test_interval", "test_execution_time")
                # as_dict() of KNXDateTime returns None for an invalid day of week
                and not (key == "day_of_week" and value is None)
            }
            automated_test_interval = int(data["automated_test_interval"])
            test_execution_time = int(data["test_execution_time"])
        except (AttributeError, KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for ConverterTestInfo: {err}") from err
        return cls(
            test_start=KNXDateTime.from_dict(date_time),
            automated_test_interval=automated_test_interval,
            test_execution_time=test_execution_time,
        )

    def as_dict(self) -> dict[str, Any]:
        """Create a JSON serializable dictionary."""
        return {
            **self.test_start.as_dict(),
            "automated_test_interval": self.automated_test_interval,
            "test_execution_time": self.test_execution_time,
        }

    @classmethod
    def get_dict_schema(cls) -> list[DPTComplexFieldSchema]:
        """Return schema for the dict used in as_dict() / from_dict()."""
        return [
            *KNXDateTime.get_dict_schema(),
            *super(ConverterTestInfo, cls).get_dict_schema(),
        ]


class DPTConverterTestInfo(DPTComplex[ConverterTestInfo]):
    """
    Abstraction for KNX 12 octet DALI converter test info (DPT 247.600).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.14
    """

    data_type = ConverterTestInfo
    payload_type = DPTArray
    payload_length = 12
    dpt_main_number = 247
    dpt_sub_number = 600
    value_type = "converter_test_info"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ConverterTestInfo:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return ConverterTestInfo(
            test_start=DPTDateTime.from_knx(DPTArray(raw[:8])),
            automated_test_interval=DPTTimePeriodHrs.from_knx(DPTArray(raw[8:10])),
            test_execution_time=DPTTimePeriodSec.from_knx(DPTArray(raw[10:])),
        )

    @classmethod
    def _to_knx(cls, value: ConverterTestInfo) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        test_start = cast(DPTArray, DPTDateTime.to_knx(value.test_start))
        return DPTArray(
            (
                *test_start.value,
                *DPTTimePeriodHrs.to_knx(value.automated_test_interval).value,
                *DPTTimePeriodSec.to_knx(value.test_execution_time).value,
            )
        )
