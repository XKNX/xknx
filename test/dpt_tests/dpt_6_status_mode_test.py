"""Unit test for KNX DPT 6.020 DPT_Status_Mode3."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTStatusMode3, StatusMode3
from xknx.exceptions import ConversionError, CouldNotParseTelegram

_ALL_SET = {f"status_{name}": True for name in "abcde"}


class TestDPTStatusMode3:
    """Test class for KNX DPT 6.020 status with mode."""

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            # status bits are 0 when set
            (0b00000_001, StatusMode3(**_ALL_SET, mode=0)),
            (0b00000_010, StatusMode3(**_ALL_SET, mode=1)),
            (0b00000_100, StatusMode3(**_ALL_SET, mode=2)),
            (
                0b11111_001,
                StatusMode3(
                    status_a=False,
                    status_b=False,
                    status_c=False,
                    status_d=False,
                    status_e=False,
                    mode=0,
                ),
            ),
            (
                0b10101_010,
                StatusMode3(
                    status_a=False,
                    status_b=True,
                    status_c=False,
                    status_d=True,
                    status_e=False,
                    mode=1,
                ),
            ),
            (
                0b01000_100,
                StatusMode3(
                    status_a=True,
                    status_b=False,
                    status_c=True,
                    status_d=True,
                    status_e=True,
                    mode=2,
                ),
            ),
        ],
    )
    def test_transcoder(self, raw: int, value: StatusMode3) -> None:
        """Test parsing and serializing."""
        assert DPTStatusMode3.from_knx(DPTArray(raw)) == value
        assert DPTStatusMode3.to_knx(value) == DPTArray(raw)
        assert DPTStatusMode3.to_knx(value.as_dict()) == DPTArray(raw)
        assert StatusMode3.from_dict(value.as_dict()) == value

    @pytest.mark.parametrize("mode_bits", [0b000, 0b011, 0b101, 0b110, 0b111])
    def test_invalid_mode_bits(self, mode_bits: int) -> None:
        """Test that the mode field must hold exactly one bit."""
        with pytest.raises(ConversionError):
            DPTStatusMode3.from_knx(DPTArray(0b11111_000 | mode_bits))

    def test_wrong_payload(self) -> None:
        """Test parsing a wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTStatusMode3.from_knx(DPTArray((0x01, 0x01)))
        with pytest.raises(CouldNotParseTelegram):
            DPTStatusMode3.from_knx(DPTBinary(1))

    @pytest.mark.parametrize(
        "value",
        [
            StatusMode3(**_ALL_SET, mode=3),
            StatusMode3(**_ALL_SET, mode=True),
            StatusMode3(**{**_ALL_SET, "status_c": 1}, mode=0),  # type: ignore[arg-type]
        ],
    )
    def test_to_knx_invalid_value(self, value: StatusMode3) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTStatusMode3.to_knx(value)

    @pytest.mark.parametrize(
        "data",
        [
            {**_ALL_SET},
            {**_ALL_SET, "mode": 3},
            {**_ALL_SET, "mode": True},
            {**_ALL_SET, "mode": "1"},
            {**_ALL_SET, "status_b": 0, "mode": 1},
            {"status_a": True, "mode": 1},
            "status",
        ],
    )
    def test_from_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            StatusMode3.from_dict(data)
        with pytest.raises(ConversionError):
            DPTStatusMode3.to_knx(data)

    def test_lookup(self) -> None:
        """Test the lookup and the dict schema."""
        assert DPTBase.parse_transcoder("status_mode3") is DPTStatusMode3
        assert DPTBase.transcoder_by_dpt(6, 20) is DPTStatusMode3
        schema = DPTStatusMode3.get_dict_schema()
        assert [field["name"] for field in schema] == [
            "status_a",
            "status_b",
            "status_c",
            "status_d",
            "status_e",
            "mode",
        ]
        assert schema[-1]["value_min"] == 0
        assert schema[-1]["value_max"] == 2
