"""Unit test for KNX DPT 245 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_245 import (
    ConverterTestResult,
    ConverterTestResultCode,
    ConverterTestStartMethod,
    DPTConverterTestResult,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


def _result(
    function_test_result: ConverterTestResultCode = ConverterTestResultCode.UNKNOWN,
    duration_test_result: ConverterTestResultCode = ConverterTestResultCode.UNKNOWN,
    partial_duration_test_result: ConverterTestResultCode = (
        ConverterTestResultCode.UNKNOWN
    ),
    function_test_start_method: ConverterTestStartMethod = (
        ConverterTestStartMethod.UNKNOWN
    ),
    duration_test_start_method: ConverterTestStartMethod = (
        ConverterTestStartMethod.UNKNOWN
    ),
    partial_duration_test_start_method: ConverterTestStartMethod = (
        ConverterTestStartMethod.UNKNOWN
    ),
    duration_test_discharge_time: int = 0,
    partial_duration_test_charge_level: int | None = None,
) -> ConverterTestResult:
    return ConverterTestResult(
        function_test_result=function_test_result,
        duration_test_result=duration_test_result,
        partial_duration_test_result=partial_duration_test_result,
        function_test_start_method=function_test_start_method,
        duration_test_start_method=duration_test_start_method,
        partial_duration_test_start_method=partial_duration_test_start_method,
        duration_test_discharge_time=duration_test_discharge_time,
        partial_duration_test_charge_level=partial_duration_test_charge_level,
    )


_UNKNOWN_DICT = {
    "function_test_result": "unknown",
    "duration_test_result": "unknown",
    "partial_duration_test_result": "unknown",
    "function_test_start_method": "unknown",
    "duration_test_start_method": "unknown",
    "partial_duration_test_start_method": "unknown",
    "duration_test_discharge_time": 0,
}


class TestConverterTestResult:
    """Test ConverterTestResult class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (_UNKNOWN_DICT, _result()),
            (
                _UNKNOWN_DICT | {"partial_duration_test_charge_level": None},
                _result(),
            ),
            (
                {
                    "function_test_result": "passed_in_time",
                    "duration_test_result": "failed_max_delay_exceeded",
                    "partial_duration_test_result": "manually_stopped",
                    "function_test_start_method": "automatic",
                    "duration_test_start_method": "gateway",
                    "partial_duration_test_start_method": "unknown",
                    "duration_test_discharge_time": 510,
                    "partial_duration_test_charge_level": 254,
                },
                _result(
                    function_test_result=ConverterTestResultCode.PASSED_IN_TIME,
                    duration_test_result=(
                        ConverterTestResultCode.FAILED_MAX_DELAY_EXCEEDED
                    ),
                    partial_duration_test_result=(
                        ConverterTestResultCode.MANUALLY_STOPPED
                    ),
                    function_test_start_method=ConverterTestStartMethod.AUTOMATIC,
                    duration_test_start_method=ConverterTestStartMethod.GATEWAY,
                    duration_test_discharge_time=510,
                    partial_duration_test_charge_level=254,
                ),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: ConverterTestResult) -> None:
        """Test from_dict and as_dict methods."""
        assert ConverterTestResult.from_dict(data) == value
        default_dict = {"partial_duration_test_charge_level": None}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"function_test_result": "unknown"},
            _UNKNOWN_DICT | {"function_test_result": "invalid"},
            _UNKNOWN_DICT | {"duration_test_result": 6},
            _UNKNOWN_DICT | {"partial_duration_test_start_method": 3},
            _UNKNOWN_DICT | {"duration_test_discharge_time": "a"},
            _UNKNOWN_DICT | {"duration_test_discharge_time": None},
            _UNKNOWN_DICT | {"partial_duration_test_charge_level": "a"},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            ConverterTestResult.from_dict(data)


class TestDPTConverterTestResult:
    """Test class for KNX DPTConverterTestResult objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (_result(), (0x00, 0x00, 0x00, 0x00, 0x00, 0xFF)),
            (
                _result(partial_duration_test_charge_level=0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                _result(partial_duration_test_charge_level=254),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0xFE),
            ),
            (
                _result(function_test_result=ConverterTestResultCode.MANUALLY_STOPPED),
                (0x50, 0x00, 0x00, 0x00, 0x00, 0xFF),
            ),
            (
                _result(duration_test_result=ConverterTestResultCode.FAILED_IN_TIME),
                (0x03, 0x00, 0x00, 0x00, 0x00, 0xFF),
            ),
            (
                _result(
                    partial_duration_test_result=(
                        ConverterTestResultCode.PASSED_MAX_DELAY_EXCEEDED
                    )
                ),
                (0x00, 0x20, 0x00, 0x00, 0x00, 0xFF),
            ),
            (
                _result(function_test_start_method=ConverterTestStartMethod.GATEWAY),
                (0x00, 0x00, 0b10000000, 0x00, 0x00, 0xFF),
            ),
            (
                _result(duration_test_start_method=ConverterTestStartMethod.GATEWAY),
                (0x00, 0x00, 0b00100000, 0x00, 0x00, 0xFF),
            ),
            (
                _result(
                    partial_duration_test_start_method=ConverterTestStartMethod.GATEWAY
                ),
                (0x00, 0x00, 0b00001000, 0x00, 0x00, 0xFF),
            ),
            (
                _result(duration_test_discharge_time=510),
                (0x00, 0x00, 0x00, 0x01, 0xFE, 0xFF),
            ),
            (
                _result(
                    function_test_result=ConverterTestResultCode.PASSED_IN_TIME,
                    duration_test_result=ConverterTestResultCode.PASSED_IN_TIME,
                    partial_duration_test_result=ConverterTestResultCode.PASSED_IN_TIME,
                    function_test_start_method=ConverterTestStartMethod.AUTOMATIC,
                    duration_test_start_method=ConverterTestStartMethod.AUTOMATIC,
                    partial_duration_test_start_method=(
                        ConverterTestStartMethod.AUTOMATIC
                    ),
                    duration_test_discharge_time=180,
                    partial_duration_test_charge_level=200,
                ),
                (0x11, 0x10, 0b01010100, 0x00, 0xB4, 0xC8),
            ),
        ],
    )
    def test_to_knx_from_knx(
        self, value: ConverterTestResult, raw: tuple[int, ...]
    ) -> None:
        """Test DPTConverterTestResult parsing and streaming."""
        knx_value = DPTConverterTestResult.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTConverterTestResult.from_knx(knx_value) == value
        assert DPTConverterTestResult.to_knx(value.as_dict()) == DPTArray(raw)

    @pytest.mark.parametrize("result", list(ConverterTestResultCode))
    def test_results(self, result: ConverterTestResultCode) -> None:
        """Test every test result value in each result field."""
        value = _result(
            function_test_result=result,
            duration_test_result=result,
            partial_duration_test_result=result,
        )
        raw = DPTArray(
            (result.value << 4 | result.value, result.value << 4, 0, 0, 0, 0xFF)
        )
        assert DPTConverterTestResult.to_knx(value) == raw
        assert DPTConverterTestResult.from_knx(raw) == value

    @pytest.mark.parametrize("method", list(ConverterTestStartMethod))
    def test_start_methods(self, method: ConverterTestStartMethod) -> None:
        """Test every start method value in each start method field."""
        value = _result(
            function_test_start_method=method,
            duration_test_start_method=method,
            partial_duration_test_start_method=method,
        )
        bits = method.value
        raw = DPTArray((0, 0, bits << 6 | bits << 4 | bits << 2, 0, 0, 0xFF))
        assert DPTConverterTestResult.to_knx(value) == raw
        assert DPTConverterTestResult.from_knx(raw) == value

    def test_reserved_bits_ignored(self) -> None:
        """Test reserved bits are ignored on receive."""
        assert (
            DPTConverterTestResult.from_knx(
                DPTArray((0x00, 0x0F, 0b00000011, 0x00, 0x00, 0xFF))
            )
            == _result()
        )

    @pytest.mark.parametrize(
        "raw",
        [
            (0x60, 0x00, 0x00, 0x00, 0x00, 0xFF),  # reserved LTRF 6
            (0x0F, 0x00, 0x00, 0x00, 0x00, 0xFF),  # reserved LTRD 15
            (0x00, 0x60, 0x00, 0x00, 0x00, 0xFF),  # reserved LTRP 6
            (0x00, 0x00, 0b11000000, 0x00, 0x00, 0xFF),  # reserved SF 3
            (0x00, 0x00, 0b00110000, 0x00, 0x00, 0xFF),  # reserved SD 3
            (0x00, 0x00, 0b00001100, 0x00, 0x00, 0xFF),  # reserved SP 3
            (0x00, 0x00, 0x00, 0x01, 0xFF, 0xFF),  # discharge time 511
        ],
    )
    def test_from_knx_invalid_values(self, raw: tuple[int, ...]) -> None:
        """Test parsing reserved or out of range values."""
        with pytest.raises(ConversionError):
            DPTConverterTestResult.from_knx(DPTArray(raw))

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00,) * 5),
            DPTArray((0x00,) * 7),
            DPTBinary(0),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTConverterTestResult.from_knx(payload)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            {"function_test_result": "unknown"},
            _result(duration_test_discharge_time=-1),
            _result(duration_test_discharge_time=511),
            _result(partial_duration_test_charge_level=-1),
            _result(partial_duration_test_charge_level=255),
            _result(function_test_result="unknown"),  # type: ignore[arg-type]
            _result(
                function_test_start_method=ConverterTestResultCode.UNKNOWN  # type: ignore[arg-type]
            ),
        ],
    )
    def test_to_knx_wrong_value(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTConverterTestResult.to_knx(value)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTConverterTestResult."""
        result_options = [
            "unknown",
            "passed_in_time",
            "passed_max_delay_exceeded",
            "failed_in_time",
            "failed_max_delay_exceeded",
            "manually_stopped",
        ]
        start_options = ["unknown", "automatic", "gateway"]
        assert DPTConverterTestResult.get_dict_schema() == [
            {
                "name": "function_test_result",
                "type": "enum",
                "required": True,
                "options": result_options,
            },
            {
                "name": "duration_test_result",
                "type": "enum",
                "required": True,
                "options": result_options,
            },
            {
                "name": "partial_duration_test_result",
                "type": "enum",
                "required": True,
                "options": result_options,
            },
            {
                "name": "function_test_start_method",
                "type": "enum",
                "required": True,
                "options": start_options,
            },
            {
                "name": "duration_test_start_method",
                "type": "enum",
                "required": True,
                "options": start_options,
            },
            {
                "name": "partial_duration_test_start_method",
                "type": "enum",
                "required": True,
                "options": start_options,
            },
            {
                "name": "duration_test_discharge_time",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 510,
            },
            {
                "name": "partial_duration_test_charge_level",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 254,
            },
        ]

    def test_lookup(self) -> None:
        """Test transcoder lookup by DPT number and value type."""
        assert DPTBase.parse_transcoder("245.600") is DPTConverterTestResult
        assert (
            DPTBase.parse_transcoder("converter_test_result") is DPTConverterTestResult
        )
