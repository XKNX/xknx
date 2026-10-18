"""Unit test for KNX DPT 241.800 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTStatusSAB, StatusSAB
from xknx.exceptions import ConversionError, CouldNotParseTelegram

STATUS_BITS = (
    "upper_end_position",
    "lower_end_position",
    "lower_predefined_position",
    "target_position_reached",
    "target_height_position_restricted",
    "target_slats_position_restricted",
    "weather_alarm",
    "forced",
    "locked",
    "local_override",
    "failure",
)

DEFAULT_DICT: dict[str, Any] = {
    "height_position": None,
    "slats_position": None,
} | dict.fromkeys(STATUS_BITS, False)


class TestStatusSAB:
    """Test StatusSAB class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            # an empty dict is a valid telegram: positions invalid, no status bit set
            ({}, StatusSAB()),
            (
                {"height_position": 0, "slats_position": 100},
                StatusSAB(height_position=0, slats_position=100),
            ),
            ({"height_position": 50}, StatusSAB(height_position=50)),
            ({"slats_position": 25}, StatusSAB(slats_position=25)),
            (
                {"height_position": None, "slats_position": None},
                StatusSAB(),
            ),
            (
                {"locked": True, "failure": True},
                StatusSAB(locked=True, failure=True),
            ),
            (
                {"height_position": 100, "target_position_reached": True},
                StatusSAB(height_position=100, target_position_reached=True),
            ),
            (
                {
                    "height_position": 100,
                    "slats_position": 100,
                    **dict.fromkeys(STATUS_BITS, True),
                },
                StatusSAB(100, 100, *(True for _ in STATUS_BITS)),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: StatusSAB) -> None:
        """Test from_dict and as_dict methods."""
        assert StatusSAB.from_dict(data) == value
        # positions default to `None`, status bits to `False`
        assert value.as_dict() == DEFAULT_DICT | data

    def test_dict_string_position(self) -> None:
        """Test from_dict converting positions to int."""
        assert StatusSAB.from_dict(
            {"height_position": "30", "slats_position": "70"}
        ) == StatusSAB(height_position=30, slats_position=70)

    @pytest.mark.parametrize(
        "data",
        [
            {"height_position": "a"},
            {"slats_position": "a"},
            {"slats_position": [1]},
            {"locked": 1},
            {"forced": 0},
            {"failure": "true"},
            {"weather_alarm": None},
            [1, 2],
            None,
            1,
            "locked",
        ],
    )
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            StatusSAB.from_dict(data)


class TestDPTStatusSAB:
    """Test class for KNX DPTStatusSAB objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (StatusSAB(), (0x00, 0x00, 0x00, 0x00)),
            (
                StatusSAB(height_position=0, slats_position=0),
                (0x00, 0x00, 0xC0, 0x00),
            ),
            (
                StatusSAB(height_position=100, slats_position=100),
                (0xFF, 0xFF, 0xC0, 0x00),
            ),
            (StatusSAB(height_position=50), (0x80, 0x00, 0x40, 0x00)),
            (StatusSAB(slats_position=50), (0x00, 0x80, 0x80, 0x00)),
            (
                StatusSAB(height_position=100, slats_position=20),
                (0xFF, 0x33, 0xC0, 0x00),
            ),
            (
                StatusSAB(100, 100, *(True for _ in STATUS_BITS)),
                (0xFF, 0xFF, 0xC7, 0xFF),
            ),
            (
                StatusSAB(
                    height_position=100,
                    slats_position=0,
                    lower_end_position=True,
                    lower_predefined_position=True,
                    target_position_reached=True,
                ),
                (0xFF, 0x00, 0xC0, 0x0E),
            ),
        ],
    )
    def test_dpt_status_sab_value(self, value: StatusSAB, raw: tuple[int, ...]) -> None:
        """Test DPTStatusSAB parsing and streaming."""
        knx_value = DPTStatusSAB.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTStatusSAB.from_knx(knx_value) == value

    @pytest.mark.parametrize(("bit", "name"), list(enumerate(STATUS_BITS)))
    def test_status_bits(self, bit: int, name: str) -> None:
        """Test every status bit on its own."""
        attributes = 1 << bit
        raw = (0x00, 0x00, attributes >> 8, attributes & 0xFF)
        value = StatusSAB(**{name: True})
        assert DPTStatusSAB.to_knx(value) == DPTArray(raw)
        assert DPTStatusSAB.from_knx(DPTArray(raw)) == value

    def test_validity_bits(self) -> None:
        """Test positions are None when their validity bit is cleared."""
        assert DPTStatusSAB.from_knx(DPTArray((0x80, 0x80, 0x00, 0x00))) == StatusSAB()
        assert DPTStatusSAB.from_knx(DPTArray((0x80, 0x80, 0x40, 0x00))) == StatusSAB(
            height_position=50
        )
        assert DPTStatusSAB.from_knx(DPTArray((0x80, 0x80, 0x80, 0x00))) == StatusSAB(
            slats_position=50
        )

    def test_reserved_bits_ignored(self) -> None:
        """Test reserved bits 11 to 13 are ignored when parsing."""
        assert DPTStatusSAB.from_knx(DPTArray((0x00, 0x00, 0x38, 0x00))) == StatusSAB()

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ({}, (0x00, 0x00, 0x00, 0x00)),
            (
                {"height_position": 100, "slats_position": 20, "forced": True},
                (0xFF, 0x33, 0xC0, 0x80),
            ),
            ({"weather_alarm": True}, (0x00, 0x00, 0x00, 0x40)),
            ({"local_override": True}, (0x00, 0x00, 0x02, 0x00)),
        ],
    )
    def test_dpt_status_sab_to_knx_from_dict(
        self, value: dict[str, Any], raw: tuple[int, ...]
    ) -> None:
        """Test DPTStatusSAB serializing from a dict."""
        assert DPTStatusSAB.to_knx(value) == DPTArray(raw)

    @pytest.mark.parametrize(
        "value",
        [
            StatusSAB(height_position=-1),
            StatusSAB(height_position=101),
            StatusSAB(slats_position=-1),
            StatusSAB(slats_position=101),
            {"height_position": 101},
            {"slats_position": -1},
        ],
    )
    def test_dpt_status_sab_to_knx_limits(self, value: Any) -> None:
        """Test DPTStatusSAB serializing out of range positions."""
        with pytest.raises(ConversionError):
            DPTStatusSAB.to_knx(value)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            (0xFF, 0x4E),
            {"height_position": "a"},
            {"locked": 1},
            StatusSAB(height_position="a"),  # type: ignore[arg-type]
            StatusSAB(locked=1),  # type: ignore[arg-type]
        ],
    )
    def test_dpt_status_sab_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTStatusSAB serializing wrong values."""
        with pytest.raises(ConversionError):
            DPTStatusSAB.to_knx(value)

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00, 0x00, 0x00)),
            DPTArray((0x00, 0x00, 0x00, 0x00, 0x00)),
            DPTBinary(0),
        ],
    )
    def test_dpt_status_sab_wrong_payload_from_knx(
        self, payload: DPTArray | DPTBinary
    ) -> None:
        """Test DPTStatusSAB parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTStatusSAB.from_knx(payload)

    def test_parse_transcoder(self) -> None:
        """Test DPTStatusSAB lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder("241.800") is DPTStatusSAB
        assert DPTBase.parse_transcoder({"main": 241, "sub": 800}) is DPTStatusSAB
        assert DPTBase.parse_transcoder("status_sab") is DPTStatusSAB

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTStatusSAB."""
        assert DPTStatusSAB.get_dict_schema() == [
            {
                "name": "height_position",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 100,
            },
            {
                "name": "slats_position",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 100,
            },
            *(
                {"name": name, "type": "boolean", "required": False, "default": False}
                for name in STATUS_BITS
            ),
        ]
