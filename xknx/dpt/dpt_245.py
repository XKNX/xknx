"""Implementation of the KNX DALI emergency converter test result data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData, DPTEnumData
from .dpt_7 import DPTTimePeriodMin
from .payload import DPTArray, DPTBinary


class ConverterTestResultCode(DPTEnumData):
    """Result of a converter test."""

    UNKNOWN = 0
    PASSED_IN_TIME = 1
    PASSED_MAX_DELAY_EXCEEDED = 2
    FAILED_IN_TIME = 3
    FAILED_MAX_DELAY_EXCEEDED = 4
    MANUALLY_STOPPED = 5


class ConverterTestStartMethod(DPTEnumData):
    """Start method of a converter test."""

    UNKNOWN = 0
    AUTOMATIC = 1
    GATEWAY = 2


@dataclass(slots=True)
class ConverterTestResult(DPTComplexData):
    """
    Representation of the DALI emergency converter test results.

    `function_test_result`: result of the last function test (FT)
    `duration_test_result`: result of the last duration test (DT)
    `partial_duration_test_result`: result of the last partial duration test (PDT)
    `function_test_start_method`: start method of the last FT
    `duration_test_start_method`: start method of the last DT
    `partial_duration_test_start_method`: start method of the last PDT
    `duration_test_discharge_time`: battery discharge time of the last successful
        DT in minutes 0..510; 510 means 510 min or longer
    `partial_duration_test_charge_level`: remaining battery charge level after
        the last PDT 0 (deep discharge point)..254 (fully charged); None if unknown
    """

    function_test_result: ConverterTestResultCode
    duration_test_result: ConverterTestResultCode
    partial_duration_test_result: ConverterTestResultCode
    function_test_start_method: ConverterTestStartMethod
    duration_test_start_method: ConverterTestStartMethod
    partial_duration_test_start_method: ConverterTestStartMethod
    duration_test_discharge_time: int = field(
        metadata={"value_min": 0, "value_max": 510}
    )
    partial_duration_test_charge_level: int | None = field(
        metadata={"value_min": 0, "value_max": 254}
    )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConverterTestResult:
        """Init from a dictionary."""
        try:
            function_test_result = ConverterTestResultCode.parse(
                data["function_test_result"]
            )
            duration_test_result = ConverterTestResultCode.parse(
                data["duration_test_result"]
            )
            partial_duration_test_result = ConverterTestResultCode.parse(
                data["partial_duration_test_result"]
            )
            function_test_start_method = ConverterTestStartMethod.parse(
                data["function_test_start_method"]
            )
            duration_test_start_method = ConverterTestStartMethod.parse(
                data["duration_test_start_method"]
            )
            partial_duration_test_start_method = ConverterTestStartMethod.parse(
                data["partial_duration_test_start_method"]
            )
            duration_test_discharge_time = int(data["duration_test_discharge_time"])
            charge_level = data.get("partial_duration_test_charge_level")
            if charge_level is not None:
                charge_level = int(charge_level)
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for ConverterTestResult: {err}") from err
        return cls(
            function_test_result=function_test_result,
            duration_test_result=duration_test_result,
            partial_duration_test_result=partial_duration_test_result,
            function_test_start_method=function_test_start_method,
            duration_test_start_method=duration_test_start_method,
            partial_duration_test_start_method=partial_duration_test_start_method,
            duration_test_discharge_time=duration_test_discharge_time,
            partial_duration_test_charge_level=charge_level,
        )

    def as_dict(self) -> dict[str, str | int | None]:
        """Create a JSON serializable dictionary."""
        return {
            "function_test_result": self.function_test_result.name.lower(),
            "duration_test_result": self.duration_test_result.name.lower(),
            "partial_duration_test_result": (
                self.partial_duration_test_result.name.lower()
            ),
            "function_test_start_method": self.function_test_start_method.name.lower(),
            "duration_test_start_method": self.duration_test_start_method.name.lower(),
            "partial_duration_test_start_method": (
                self.partial_duration_test_start_method.name.lower()
            ),
            "duration_test_discharge_time": self.duration_test_discharge_time,
            "partial_duration_test_charge_level": (
                self.partial_duration_test_charge_level
            ),
        }


class DPTConverterTestResult(DPTComplex[ConverterTestResult]):
    """
    Abstraction for KNX 6 octet DALI converter test result (DPT 245.600).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.12
    """

    data_type = ConverterTestResult
    payload_type = DPTArray
    payload_length = 6
    dpt_main_number = 245
    dpt_sub_number = 600
    value_type = "converter_test_result"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ConverterTestResult:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        discharge_time = DPTTimePeriodMin.from_knx(DPTArray(raw[3:5]))
        try:
            if discharge_time > 510:
                raise ValueError(
                    f"Discharge time out of range 0..510: {discharge_time}"
                )
            return ConverterTestResult(
                function_test_result=ConverterTestResultCode(raw[0] >> 4),
                duration_test_result=ConverterTestResultCode(raw[0] & 0x0F),
                partial_duration_test_result=ConverterTestResultCode(raw[1] >> 4),
                function_test_start_method=ConverterTestStartMethod(raw[2] >> 6),
                duration_test_start_method=ConverterTestStartMethod(raw[2] >> 4 & 0b11),
                partial_duration_test_start_method=ConverterTestStartMethod(
                    raw[2] >> 2 & 0b11
                ),
                duration_test_discharge_time=discharge_time,
                partial_duration_test_charge_level=raw[5] if raw[5] != 0xFF else None,
            )
        except ValueError as err:
            raise ConversionError(
                f"Could not parse {cls.dpt_name()}: {err}", raw=raw
            ) from err

    @classmethod
    def _to_knx(cls, value: ConverterTestResult) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= value.duration_test_discharge_time <= 510:
            raise ValueError(
                "Discharge time out of range 0..510: "
                f"{value.duration_test_discharge_time}"
            )
        charge_level = value.partial_duration_test_charge_level
        if charge_level is None:
            charge_level = 0xFF
        elif not 0 <= charge_level <= 254:
            raise ValueError(f"Charge level out of range 0..254: {charge_level}")
        return DPTArray(
            (
                ConverterTestResultCode(value.function_test_result).value << 4
                | ConverterTestResultCode(value.duration_test_result).value,
                ConverterTestResultCode(value.partial_duration_test_result).value << 4,
                ConverterTestStartMethod(value.function_test_start_method).value << 6
                | ConverterTestStartMethod(value.duration_test_start_method).value << 4
                | ConverterTestStartMethod(
                    value.partial_duration_test_start_method
                ).value
                << 2,
                *DPTTimePeriodMin.to_knx(value.duration_test_discharge_time).value,
                charge_level,
            )
        )
