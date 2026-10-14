"""Implementation of the KNX DALI emergency converter status data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData, DPTEnumData
from .payload import DPTArray, DPTBinary


class ConverterMode(DPTEnumData):
    """Converter mode according to the DALI converter state machine."""

    UNKNOWN = 0
    NORMAL = 1
    INHIBIT = 2
    HARDWIRED_INHIBIT = 3
    REST = 4
    EMERGENCY = 5
    EXTENDED_EMERGENCY = 6
    FUNCTION_TEST_IN_PROGRESS = 7
    DURATION_TEST_IN_PROGRESS = 8
    PARTIAL_DURATION_TEST_IN_PROGRESS = 9


class ConverterTestPending(DPTEnumData):
    """Pending state of a converter test."""

    UNKNOWN = 0
    NO_TEST_PENDING = 1
    TEST_PENDING = 2


class ConverterFailure(DPTEnumData):
    """Converter failure state."""

    UNKNOWN = 0
    NO_FAILURE = 1
    FAILURE = 2


@dataclass(slots=True)
class ConverterStatus(DPTComplexData):
    """
    Representation of a DALI emergency converter status.

    `mode`: converter mode
    `hardwired_inhibit_active`: hardwired inhibit is active
    `hardwired_switch_on`: hardwired switch is on
    `function_test_pending`: pending state of the function test (FT)
    `duration_test_pending`: pending state of the duration test (DT)
    `partial_duration_test_pending`: pending state of the partial duration test (PDT)
    `failure`: one or more failures were detected
    """

    mode: ConverterMode
    hardwired_inhibit_active: bool
    hardwired_switch_on: bool
    function_test_pending: ConverterTestPending
    duration_test_pending: ConverterTestPending
    partial_duration_test_pending: ConverterTestPending
    failure: ConverterFailure

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConverterStatus:
        """Init from a dictionary."""
        try:
            mode = ConverterMode.parse(data["mode"])
            hardwired_inhibit_active = data["hardwired_inhibit_active"]
            hardwired_switch_on = data["hardwired_switch_on"]
            function_test_pending = ConverterTestPending.parse(
                data["function_test_pending"]
            )
            duration_test_pending = ConverterTestPending.parse(
                data["duration_test_pending"]
            )
            partial_duration_test_pending = ConverterTestPending.parse(
                data["partial_duration_test_pending"]
            )
            failure = ConverterFailure.parse(data["failure"])
        except (KeyError, TypeError) as err:
            raise ValueError(f"Invalid value for ConverterStatus: {err}") from err
        if not isinstance(hardwired_inhibit_active, bool) or not isinstance(
            hardwired_switch_on, bool
        ):
            raise ValueError(
                "Invalid value for ConverterStatus boolean fields: "
                f"{hardwired_inhibit_active=}, {hardwired_switch_on=}"
            )
        return cls(
            mode=mode,
            hardwired_inhibit_active=hardwired_inhibit_active,
            hardwired_switch_on=hardwired_switch_on,
            function_test_pending=function_test_pending,
            duration_test_pending=duration_test_pending,
            partial_duration_test_pending=partial_duration_test_pending,
            failure=failure,
        )

    def as_dict(self) -> dict[str, str | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "mode": self.mode.name.lower(),
            "hardwired_inhibit_active": self.hardwired_inhibit_active,
            "hardwired_switch_on": self.hardwired_switch_on,
            "function_test_pending": self.function_test_pending.name.lower(),
            "duration_test_pending": self.duration_test_pending.name.lower(),
            "partial_duration_test_pending": (
                self.partial_duration_test_pending.name.lower()
            ),
            "failure": self.failure.name.lower(),
        }


class DPTConverterStatus(DPTComplex[ConverterStatus]):
    """
    Abstraction for KNX 2 octet DALI converter status (DPT 244.600).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.11
    """

    data_type = ConverterStatus
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 244
    dpt_sub_number = 600
    value_type = "converter_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ConverterStatus:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        try:
            return ConverterStatus(
                mode=ConverterMode(raw[0] >> 4),
                hardwired_inhibit_active=bool(raw[0] & 0b1),
                hardwired_switch_on=bool(raw[0] >> 1 & 0b1),
                function_test_pending=ConverterTestPending(raw[1] >> 6),
                duration_test_pending=ConverterTestPending(raw[1] >> 4 & 0b11),
                partial_duration_test_pending=ConverterTestPending(raw[1] >> 2 & 0b11),
                failure=ConverterFailure(raw[1] & 0b11),
            )
        except ValueError as err:
            raise ConversionError(
                f"Could not parse {cls.dpt_name()}: {err}", raw=raw
            ) from err

    @classmethod
    def _to_knx(cls, value: ConverterStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                ConverterMode(value.mode).value << 4
                | bool(value.hardwired_switch_on) << 1
                | bool(value.hardwired_inhibit_active),
                ConverterTestPending(value.function_test_pending).value << 6
                | ConverterTestPending(value.duration_test_pending).value << 4
                | ConverterTestPending(value.partial_duration_test_pending).value << 2
                | ConverterFailure(value.failure).value,
            )
        )
