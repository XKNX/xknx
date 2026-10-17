"""Unit test for KNX DPT 248 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_248 import ConverterInfoFix, ConverterInfoValid, DPTConverterInfoFix
from xknx.exceptions import ConversionError, CouldNotParseTelegram

_FEATURES = (
    "integral_emergency_control_gear",
    "maintained_control_gear",
    "switched_maintained_control_gear",
    "auto_test_capability",
    "adjustable_emergency_level",
    "hardwired_inhibit_supported",
    "physical_selection_supported",
    "relight_in_rest_mode_supported",
)


def _info(
    info_valid: ConverterInfoValid = ConverterInfoValid.VALID,
    emergency_min_level: int | None = None,
    emergency_max_level: int | None = None,
    rated_duration: int = 0,
    **features: bool,
) -> ConverterInfoFix:
    return ConverterInfoFix(
        info_valid,
        emergency_min_level,
        emergency_max_level,
        rated_duration,
        *(features.get(name, False) for name in _FEATURES),
    )


def _features_dict(**features: bool) -> dict[str, bool]:
    return {name: features.get(name, False) for name in _FEATURES}


class TestConverterInfoFix:
    """Test ConverterInfoFix class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {
                    "info_valid": "valid",
                    "emergency_min_level": 10,
                    "emergency_max_level": 254,
                    "rated_duration": 180,
                    **_features_dict(auto_test_capability=True),
                },
                _info(
                    emergency_min_level=10,
                    emergency_max_level=254,
                    rated_duration=180,
                    auto_test_capability=True,
                ),
            ),
            (
                {
                    "info_valid": "not_available",
                    "rated_duration": 0,
                    **_features_dict(),
                },
                _info(info_valid=ConverterInfoValid.NOT_AVAILABLE),
            ),
            (
                {
                    "info_valid": "invalid",
                    "emergency_min_level": None,
                    "emergency_max_level": None,
                    "rated_duration": 255,
                    **_features_dict(
                        integral_emergency_control_gear=True,
                        relight_in_rest_mode_supported=True,
                    ),
                },
                _info(
                    info_valid=ConverterInfoValid.INVALID,
                    rated_duration=255,
                    integral_emergency_control_gear=True,
                    relight_in_rest_mode_supported=True,
                ),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: ConverterInfoFix) -> None:
        """Test from_dict and as_dict methods."""
        assert ConverterInfoFix.from_dict(data) == value
        default_dict = {"emergency_min_level": None, "emergency_max_level": None}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"info_valid": "valid", "rated_duration": 0},
            {"info_valid": "valid", **_features_dict()},
            {"info_valid": "maybe", "rated_duration": 0, **_features_dict()},
            {"info_valid": 3, "rated_duration": 0, **_features_dict()},
            {"info_valid": "valid", "rated_duration": "a", **_features_dict()},
            {
                "info_valid": "valid",
                "emergency_min_level": "a",
                "rated_duration": 0,
                **_features_dict(),
            },
            {
                "info_valid": "valid",
                "rated_duration": 0,
                **_features_dict(),
                "auto_test_capability": 1,
            },
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            ConverterInfoFix.from_dict(data)


class TestDPTConverterInfoFix:
    """Test class for KNX DPTConverterInfoFix objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                _info(info_valid=ConverterInfoValid.NOT_AVAILABLE),
                (0x00, 0xFF, 0xFF, 0x00, 0x00),
            ),
            (
                _info(emergency_min_level=0, emergency_max_level=0),
                (0x01, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                _info(
                    info_valid=ConverterInfoValid.INVALID,
                    emergency_min_level=1,
                    emergency_max_level=254,
                    rated_duration=255,
                ),
                (0x02, 0x01, 0xFE, 0xFF, 0x00),
            ),
            (
                _info(**dict.fromkeys(_FEATURES, True)),
                (0x01, 0xFF, 0xFF, 0x00, 0xFF),
            ),
        ],
    )
    def test_to_knx_from_knx(
        self, value: ConverterInfoFix, raw: tuple[int, ...]
    ) -> None:
        """Test DPTConverterInfoFix parsing and streaming."""
        knx_value = DPTConverterInfoFix.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTConverterInfoFix.from_knx(knx_value) == value
        assert DPTConverterInfoFix.to_knx(value.as_dict()) == DPTArray(raw)

    @pytest.mark.parametrize(("bit", "feature"), list(enumerate(_FEATURES)))
    def test_gear_features(self, bit: int, feature: str) -> None:
        """Test every gear feature bit."""
        value = _info(**{feature: True})
        raw = DPTArray((0x01, 0xFF, 0xFF, 0x00, 1 << bit))
        assert DPTConverterInfoFix.to_knx(value) == raw
        assert DPTConverterInfoFix.from_knx(raw) == value

    @pytest.mark.parametrize("raw_info_valid", [3, 255])
    def test_from_knx_reserved_info_valid(self, raw_info_valid: int) -> None:
        """Test parsing reserved InfoValid values."""
        with pytest.raises(ConversionError):
            DPTConverterInfoFix.from_knx(
                DPTArray((raw_info_valid, 0x00, 0x00, 0x00, 0x00))
            )

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00,) * 4),
            DPTArray((0x00,) * 6),
            DPTBinary(0),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTConverterInfoFix.from_knx(payload)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            {"info_valid": "valid"},
            _info(emergency_min_level=-1),
            _info(emergency_min_level=255),
            _info(emergency_max_level=-1),
            _info(emergency_max_level=255),
            _info(rated_duration=-1),
            _info(rated_duration=256),
            _info(info_valid="valid"),  # type: ignore[arg-type]
            _info(info_valid=3),  # type: ignore[arg-type]
        ],
    )
    def test_to_knx_wrong_value(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTConverterInfoFix.to_knx(value)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTConverterInfoFix."""
        assert DPTConverterInfoFix.get_dict_schema() == [
            {
                "name": "info_valid",
                "type": "enum",
                "required": True,
                "options": ["not_available", "valid", "invalid"],
            },
            {
                "name": "emergency_min_level",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 254,
            },
            {
                "name": "emergency_max_level",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 254,
            },
            {
                "name": "rated_duration",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 255,
            },
            *(
                {"name": name, "type": "boolean", "required": True}
                for name in _FEATURES
            ),
        ]

    def test_lookup(self) -> None:
        """Test transcoder lookup by DPT number and value type."""
        assert DPTBase.parse_transcoder("248.600") is DPTConverterInfoFix
        assert DPTBase.parse_transcoder("converter_info_fix") is DPTConverterInfoFix
