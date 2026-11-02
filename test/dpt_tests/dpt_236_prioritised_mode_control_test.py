"""Unit test for KNX DPT 236 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_236 import DPTPrioritisedModeControl, PrioritisedModeControl
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestPrioritisedModeControl:
    """Test PrioritisedModeControl class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"priority_level": 0, "mode_level": 0},
                PrioritisedModeControl(0, 0),
            ),
            (
                {"priority_level": 7, "mode_level": 15, "deactivate_priority": True},
                PrioritisedModeControl(7, 15, True),
            ),
            (
                {"priority_level": 2, "mode_level": 3, "deactivate_priority": False},
                PrioritisedModeControl(2, 3, False),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: PrioritisedModeControl) -> None:
        """Test from_dict and as_dict methods."""
        assert PrioritisedModeControl.from_dict(data) == value
        default_dict = {"deactivate_priority": False}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"priority_level": 1},
            {"mode_level": 1},
            {"priority_level": "a", "mode_level": 1},
            {"priority_level": 1, "mode_level": None},
            {"priority_level": 1, "mode_level": 1, "deactivate_priority": "a"},
            {"priority_level": 1, "mode_level": 1, "deactivate_priority": None},
            [1, 2],
        ],
    )
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            PrioritisedModeControl.from_dict(data)


class TestDPTPrioritisedModeControl:
    """Test class for KNX DPTPrioritisedModeControl objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (PrioritisedModeControl(0, 0), (0x00,)),
            (PrioritisedModeControl(1, 0), (0x10,)),  # spec example 0001xxxxb
            (PrioritisedModeControl(2, 0), (0x20,)),  # spec example 0010xxxxb
            (PrioritisedModeControl(2, 0, True), (0xA0,)),  # spec example 1010xxxxb
            (PrioritisedModeControl(0, 15), (0x0F,)),
            (PrioritisedModeControl(7, 0), (0x70,)),
            (PrioritisedModeControl(0, 0, True), (0x80,)),
            (PrioritisedModeControl(7, 15, True), (0xFF,)),
            (PrioritisedModeControl(5, 10, False), (0x5A,)),
        ],
    )
    def test_values(self, value: PrioritisedModeControl, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        knx_value = DPTPrioritisedModeControl.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTPrioritisedModeControl.from_knx(knx_value) == value

    @pytest.mark.parametrize("level", range(8))
    def test_priority_levels(self, level: int) -> None:
        """Test every priority level."""
        value = PrioritisedModeControl(level, 0)
        assert DPTPrioritisedModeControl.to_knx(value) == DPTArray(level << 4)
        assert DPTPrioritisedModeControl.from_knx(DPTArray(level << 4)) == value

    @pytest.mark.parametrize("level", range(16))
    def test_mode_levels(self, level: int) -> None:
        """Test every mode level."""
        value = PrioritisedModeControl(0, level)
        assert DPTPrioritisedModeControl.to_knx(value) == DPTArray(level)
        assert DPTPrioritisedModeControl.from_knx(DPTArray(level)) == value

    def test_to_knx_from_dict(self) -> None:
        """Test serializing from a dict."""
        assert DPTPrioritisedModeControl.to_knx(
            {"priority_level": 3, "mode_level": 4, "deactivate_priority": True}
        ) == DPTArray(0xB4)

    @pytest.mark.parametrize(
        "value",
        [
            PrioritisedModeControl(-1, 0),
            PrioritisedModeControl(8, 0),
            PrioritisedModeControl(0, -1),
            PrioritisedModeControl(0, 16),
            PrioritisedModeControl("a", 0),  # type: ignore[arg-type]
            {"priority_level": 8, "mode_level": 0},
            {"priority_level": 0},
            None,
            1,
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTPrioritisedModeControl.to_knx(value)

    @pytest.mark.parametrize(
        "payload", [DPTArray(()), DPTArray((0x00, 0x00)), DPTBinary(1)]
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing wrong payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTPrioritisedModeControl.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema."""
        assert DPTPrioritisedModeControl.get_dict_schema() == [
            {
                "name": "priority_level",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 7,
            },
            {
                "name": "mode_level",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 15,
            },
            {
                "name": "deactivate_priority",
                "type": "boolean",
                "required": False,
                "default": False,
            },
        ]

    def test_transcoder_lookup(self) -> None:
        """Test lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder("236.001") is DPTPrioritisedModeControl
        assert (
            DPTBase.parse_transcoder("prioritised_mode_control")
            is DPTPrioritisedModeControl
        )


def test_to_knx_coerces_deactivate_priority() -> None:
    """Test a non-bool flag of a constructed dataclass is sent as one bit."""
    assert DPTPrioritisedModeControl.to_knx(
        PrioritisedModeControl(0, 0, 2)  # type: ignore[arg-type]
    ) == DPTArray(0x80)
