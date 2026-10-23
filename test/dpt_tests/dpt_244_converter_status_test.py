"""Unit test for KNX DPT 244 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_244 import (
    ConverterFailure,
    ConverterMode,
    ConverterStatus,
    ConverterTestPending,
    DPTConverterStatus,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


def _status(
    mode: ConverterMode = ConverterMode.UNKNOWN,
    hardwired_inhibit_active: bool = False,
    hardwired_switch_on: bool = False,
    function_test_pending: ConverterTestPending = ConverterTestPending.UNKNOWN,
    duration_test_pending: ConverterTestPending = ConverterTestPending.UNKNOWN,
    partial_duration_test_pending: ConverterTestPending = ConverterTestPending.UNKNOWN,
    failure: ConverterFailure = ConverterFailure.UNKNOWN,
) -> ConverterStatus:
    return ConverterStatus(
        mode=mode,
        hardwired_inhibit_active=hardwired_inhibit_active,
        hardwired_switch_on=hardwired_switch_on,
        function_test_pending=function_test_pending,
        duration_test_pending=duration_test_pending,
        partial_duration_test_pending=partial_duration_test_pending,
        failure=failure,
    )


class TestConverterStatus:
    """Test ConverterStatus class."""

    def test_dict(self) -> None:
        """Test from_dict and as_dict methods."""
        value = _status(
            mode=ConverterMode.EMERGENCY,
            hardwired_switch_on=True,
            function_test_pending=ConverterTestPending.TEST_PENDING,
            duration_test_pending=ConverterTestPending.NO_TEST_PENDING,
            failure=ConverterFailure.FAILURE,
        )
        data = {
            "mode": "emergency",
            "hardwired_inhibit_active": False,
            "hardwired_switch_on": True,
            "function_test_pending": "test_pending",
            "duration_test_pending": "no_test_pending",
            "partial_duration_test_pending": "unknown",
            "failure": "failure",
        }
        assert value.as_dict() == data
        assert ConverterStatus.from_dict(data) == value
        # enum values may also be given as raw value or member
        assert (
            ConverterStatus.from_dict(
                data | {"mode": 5, "failure": ConverterFailure.FAILURE}
            )
            == value
        )

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"mode": "normal"},
            {
                "mode": "invalid",
                "hardwired_inhibit_active": False,
                "hardwired_switch_on": False,
                "function_test_pending": "unknown",
                "duration_test_pending": "unknown",
                "partial_duration_test_pending": "unknown",
                "failure": "unknown",
            },
            {
                "mode": 10,
                "hardwired_inhibit_active": False,
                "hardwired_switch_on": False,
                "function_test_pending": "unknown",
                "duration_test_pending": "unknown",
                "partial_duration_test_pending": "unknown",
                "failure": "unknown",
            },
            {
                "mode": "normal",
                "hardwired_inhibit_active": 2,
                "hardwired_switch_on": False,
                "function_test_pending": "unknown",
                "duration_test_pending": "unknown",
                "partial_duration_test_pending": "unknown",
                "failure": "unknown",
            },
            {
                "mode": "normal",
                "hardwired_inhibit_active": False,
                "hardwired_switch_on": "on",
                "function_test_pending": "unknown",
                "duration_test_pending": "unknown",
                "partial_duration_test_pending": "unknown",
                "failure": "unknown",
            },
            {
                "mode": "normal",
                "hardwired_inhibit_active": False,
                "hardwired_switch_on": False,
                "function_test_pending": "unknown",
                "duration_test_pending": "unknown",
                "partial_duration_test_pending": 3,
                "failure": "unknown",
            },
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            ConverterStatus.from_dict(data)


class TestDPTConverterStatus:
    """Test class for KNX DPTConverterStatus objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (_status(), (0x00, 0x00)),
            (
                _status(
                    mode=ConverterMode.NORMAL,
                    function_test_pending=ConverterTestPending.NO_TEST_PENDING,
                    duration_test_pending=ConverterTestPending.NO_TEST_PENDING,
                    partial_duration_test_pending=ConverterTestPending.NO_TEST_PENDING,
                    failure=ConverterFailure.NO_FAILURE,
                ),
                (0x10, 0b01010101),
            ),
            (_status(hardwired_inhibit_active=True), (0x01, 0x00)),
            (_status(hardwired_switch_on=True), (0x02, 0x00)),
            (
                _status(
                    mode=ConverterMode.HARDWIRED_INHIBIT,
                    hardwired_inhibit_active=True,
                    hardwired_switch_on=True,
                ),
                (0x33, 0x00),
            ),
            (
                _status(function_test_pending=ConverterTestPending.TEST_PENDING),
                (0x00, 0b10000000),
            ),
            (
                _status(duration_test_pending=ConverterTestPending.TEST_PENDING),
                (0x00, 0b00100000),
            ),
            (
                _status(
                    partial_duration_test_pending=ConverterTestPending.TEST_PENDING
                ),
                (0x00, 0b00001000),
            ),
            (_status(failure=ConverterFailure.FAILURE), (0x00, 0b00000010)),
            (
                _status(mode=ConverterMode.PARTIAL_DURATION_TEST_IN_PROGRESS),
                (0x90, 0x00),
            ),
        ],
    )
    def test_to_knx_from_knx(
        self, value: ConverterStatus, raw: tuple[int, ...]
    ) -> None:
        """Test DPTConverterStatus parsing and streaming."""
        knx_value = DPTConverterStatus.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTConverterStatus.from_knx(knx_value) == value
        assert DPTConverterStatus.to_knx(value.as_dict()) == DPTArray(raw)

    @pytest.mark.parametrize("mode", list(ConverterMode))
    def test_modes(self, mode: ConverterMode) -> None:
        """Test every converter mode."""
        raw = DPTArray((mode.value << 4, 0x00))
        assert DPTConverterStatus.from_knx(raw) == _status(mode=mode)
        assert DPTConverterStatus.to_knx(_status(mode=mode)) == raw

    def test_reserved_bits_ignored(self) -> None:
        """Test reserved hardware status bits are ignored on receive."""
        assert DPTConverterStatus.from_knx(DPTArray((0x1C, 0x00))) == _status(
            mode=ConverterMode.NORMAL
        )

    @pytest.mark.parametrize(
        "raw",
        [
            (0xA0, 0x00),  # reserved converter mode 10
            (0xF0, 0x00),  # reserved converter mode 15
            (0x00, 0b11000000),  # reserved FP 3
            (0x00, 0b00110000),  # reserved DP 3
            (0x00, 0b00001100),  # reserved PP 3
            (0x00, 0b00000011),  # reserved CF 3
        ],
    )
    def test_from_knx_reserved_values(self, raw: tuple[int, ...]) -> None:
        """Test parsing reserved enum values."""
        with pytest.raises(ConversionError):
            DPTConverterStatus.from_knx(DPTArray(raw))

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00,)),
            DPTArray((0x00, 0x00, 0x00)),
            DPTBinary(0),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTConverterStatus.from_knx(payload)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            {"mode": "normal"},
            _status(mode="normal"),  # type: ignore[arg-type]
            _status(mode=ConverterTestPending.UNKNOWN),  # type: ignore[arg-type]
            _status(failure=ConverterTestPending.UNKNOWN),  # type: ignore[arg-type]
        ],
    )
    def test_to_knx_wrong_value(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTConverterStatus.to_knx(value)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTConverterStatus."""
        test_pending_options = ["unknown", "no_test_pending", "test_pending"]
        assert DPTConverterStatus.get_dict_schema() == [
            {
                "name": "mode",
                "type": "enum",
                "required": True,
                "options": [
                    "unknown",
                    "normal",
                    "inhibit",
                    "hardwired_inhibit",
                    "rest",
                    "emergency",
                    "extended_emergency",
                    "function_test_in_progress",
                    "duration_test_in_progress",
                    "partial_duration_test_in_progress",
                ],
            },
            {"name": "hardwired_inhibit_active", "type": "boolean", "required": True},
            {"name": "hardwired_switch_on", "type": "boolean", "required": True},
            {
                "name": "function_test_pending",
                "type": "enum",
                "required": True,
                "options": test_pending_options,
            },
            {
                "name": "duration_test_pending",
                "type": "enum",
                "required": True,
                "options": test_pending_options,
            },
            {
                "name": "partial_duration_test_pending",
                "type": "enum",
                "required": True,
                "options": test_pending_options,
            },
            {
                "name": "failure",
                "type": "enum",
                "required": True,
                "options": ["unknown", "no_failure", "failure"],
            },
        ]

    def test_lookup(self) -> None:
        """Test transcoder lookup by DPT number and value type."""
        assert DPTBase.parse_transcoder("244.600") is DPTConverterStatus
        assert DPTBase.parse_transcoder("converter_status") is DPTConverterStatus
