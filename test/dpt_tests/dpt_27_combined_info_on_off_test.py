"""Unit test for KNX DPT 27 objects."""

from typing import Any

import pytest

from xknx.dpt import (
    CombinedInfoOnOff,
    DPTArray,
    DPTBase,
    DPTBinary,
    DPTCombinedInfoOnOff,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram

ALL_NONE = {f"output_{n}": None for n in range(1, 17)}


class TestCombinedInfoOnOff:
    """Test CombinedInfoOnOff class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            # an empty dict is a valid telegram with every output not valid
            ({}, CombinedInfoOnOff()),
            ({"output_1": True}, CombinedInfoOnOff(output_1=True)),
            ({"output_16": False}, CombinedInfoOnOff(output_16=False)),
            (
                {"output_2": True, "output_9": False, "output_15": None},
                CombinedInfoOnOff(output_2=True, output_9=False),
            ),
            (
                {f"output_{n}": True for n in range(1, 17)},
                CombinedInfoOnOff(*(True,) * 16),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: CombinedInfoOnOff) -> None:
        """Test from_dict and as_dict methods."""
        assert CombinedInfoOnOff.from_dict(data) == value
        # fields default to `None`
        assert value.as_dict() == ALL_NONE | data

    @pytest.mark.parametrize(
        "data",
        [
            {"output_1": "a"},
            {"output_1": 1},
            {"output_2": 0},
            {"output_3": 2},
            {"output_16": "on"},
            {"output_4": 0.5},
            1,
            None,
            "output_1",
            [("output_1", True)],
        ],
    )
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid values."""
        with pytest.raises(ValueError):
            CombinedInfoOnOff.from_dict(data)


class TestDPTCombinedInfoOnOff:
    """Test class for KNX DPTCombinedInfoOnOff objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            # octets: m15..m8, m7..m0, s15..s8, s7..s0
            (CombinedInfoOnOff(), (0x00, 0x00, 0x00, 0x00)),
            (CombinedInfoOnOff(output_1=True), (0x00, 0x01, 0x00, 0x01)),
            (CombinedInfoOnOff(output_1=False), (0x00, 0x01, 0x00, 0x00)),
            (CombinedInfoOnOff(output_8=True), (0x00, 0x80, 0x00, 0x80)),
            (CombinedInfoOnOff(output_9=False), (0x01, 0x00, 0x00, 0x00)),
            (CombinedInfoOnOff(output_9=True), (0x01, 0x00, 0x01, 0x00)),
            (CombinedInfoOnOff(output_16=True), (0x80, 0x00, 0x80, 0x00)),
            (CombinedInfoOnOff(*(True,) * 16), (0xFF, 0xFF, 0xFF, 0xFF)),
            (CombinedInfoOnOff(*(False,) * 16), (0xFF, 0xFF, 0x00, 0x00)),
            # outputs 1..8 valid, odd outputs On
            (
                CombinedInfoOnOff(*(True, False) * 4),
                (0x00, 0xFF, 0x00, 0x55),
            ),
            # outputs 1..4 On, 5..6 Off, 7..16 not valid
            (
                CombinedInfoOnOff(True, True, True, True, False, False),
                (0x00, 0x3F, 0x00, 0x0F),
            ),
        ],
    )
    def test_values(self, value: CombinedInfoOnOff, raw: tuple[int, ...]) -> None:
        """Test DPTCombinedInfoOnOff parsing and streaming."""
        knx_value = DPTCombinedInfoOnOff.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTCombinedInfoOnOff.from_knx(knx_value) == value

    def test_from_knx_state_without_mask(self) -> None:
        """Test state bits of not valid outputs are ignored."""
        value = DPTCombinedInfoOnOff.from_knx(DPTArray((0x00, 0x01, 0xFF, 0xFF)))
        assert value == CombinedInfoOnOff(output_1=True)
        assert DPTCombinedInfoOnOff.to_knx(value) == DPTArray((0x00, 0x01, 0x00, 0x01))

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ({}, (0x00, 0x00, 0x00, 0x00)),
            ({"output_1": True, "output_16": False}, (0x80, 0x01, 0x00, 0x01)),
            ({"output_12": True}, (0x08, 0x00, 0x08, 0x00)),
        ],
    )
    def test_to_knx_from_dict(
        self, value: dict[str, Any], raw: tuple[int, ...]
    ) -> None:
        """Test DPTCombinedInfoOnOff serializing from a dict."""
        assert DPTCombinedInfoOnOff.to_knx(value) == DPTArray(raw)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            "a",
            (0x00, 0x01, 0x00, 0x01),
            {"output_1": "a"},
            {"output_2": 2},
            {"output_3": 1},
            CombinedInfoOnOff(output_1="a"),  # type: ignore[arg-type]
            CombinedInfoOnOff(output_16=1),  # type: ignore[arg-type]
        ],
    )
    def test_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTCombinedInfoOnOff serializing with wrong value."""
        with pytest.raises(ConversionError):
            DPTCombinedInfoOnOff.to_knx(value)

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray(()),
            DPTArray((0x00, 0x01, 0x00)),
            DPTArray((0x00, 0x01, 0x00, 0x01, 0x00)),
            DPTBinary(1),
        ],
    )
    def test_wrong_value_from_knx(self, payload: DPTArray | DPTBinary) -> None:
        """Test DPTCombinedInfoOnOff parsing with wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTCombinedInfoOnOff.from_knx(payload)

    @pytest.mark.parametrize("transcoder", ["27.001", "combined_info_on_off"])
    def test_parse_transcoder(self, transcoder: str) -> None:
        """Test lookup by DPT number and value type."""
        assert DPTBase.parse_transcoder(transcoder) is DPTCombinedInfoOnOff

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTCombinedInfoOnOff."""
        assert DPTCombinedInfoOnOff.get_dict_schema() == [
            {"name": f"output_{n}", "type": "boolean", "required": False}
            for n in range(1, 17)
        ]
