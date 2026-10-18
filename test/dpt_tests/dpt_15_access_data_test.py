"""Unit test for KNX DPT 15 objects."""

from typing import Any

import pytest

from xknx.dpt import AccessData, DPTAccessData, DPTArray, DPTBase, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestAccessData:
    """Test AccessData class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            ({"access_code": 0}, AccessData(access_code=0)),
            (
                {"access_code": 123456, "permission": True, "index": 13},
                AccessData(access_code=123456, permission=True, index=13),
            ),
            (
                {
                    "access_code": 999999,
                    "detection_error": True,
                    "permission": True,
                    "read_right_to_left": True,
                    "encrypted": True,
                    "index": 15,
                },
                AccessData(
                    access_code=999999,
                    detection_error=True,
                    permission=True,
                    read_right_to_left=True,
                    encrypted=True,
                    index=15,
                ),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: AccessData) -> None:
        """Test from_dict and as_dict methods."""
        assert AccessData.from_dict(data) == value
        default_dict = {
            "detection_error": False,
            "permission": False,
            "read_right_to_left": False,
            "encrypted": False,
            "index": 0,
        }
        assert value.as_dict() == default_dict | data

    def test_dict_string_numbers(self) -> None:
        """Test from_dict with numbers given as strings."""
        assert AccessData.from_dict({"access_code": "6789", "index": "14"}) == (
            AccessData(access_code=6789, index=14)
        )

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"index": 1},
            {"access_code": None},
            {"access_code": "a"},
            {"access_code": 1, "index": "a"},
            {"access_code": 1, "index": None},
            {"access_code": 1, "permission": "a"},
            {"access_code": 1, "detection_error": None},
            {"access_code": 1, "read_right_to_left": 2},
            {"access_code": 1, "encrypted": "yes"},
            {"access_code": 1, "permission": 1},
            {"access_code": 1, "detection_error": 0},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            AccessData.from_dict(data)

    @pytest.mark.parametrize("data", [1, None, "access_code", [("access_code", 1)]])
    def test_dict_not_a_mapping(self, data: Any) -> None:
        """Test from_dict with something that is not a mapping."""
        with pytest.raises(ValueError):
            AccessData.from_dict(data)


class TestDPTAccessData:
    """Test class for KNX DPTAccessData objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            # KNX v02.02.01 - Datapoint Types 03.07.02 - §3.16 EXAMPLE 6
            (
                AccessData(access_code=123456, permission=True, index=13),
                (0x12, 0x34, 0x56, 0x4D),
            ),
            # KNX v02.02.01 - Datapoint Types 03.07.02 - §3.16 EXAMPLE 7
            (AccessData(access_code=6789, index=14), (0x00, 0x67, 0x89, 0x0E)),
            (AccessData(access_code=0), (0x00, 0x00, 0x00, 0x00)),
            (AccessData(access_code=999999), (0x99, 0x99, 0x99, 0x00)),
            (AccessData(access_code=0, detection_error=True), (0, 0, 0, 0x80)),
            (AccessData(access_code=0, permission=True), (0, 0, 0, 0x40)),
            (AccessData(access_code=0, read_right_to_left=True), (0, 0, 0, 0x20)),
            (AccessData(access_code=0, encrypted=True), (0, 0, 0, 0x10)),
            (AccessData(access_code=0, index=15), (0, 0, 0, 0x0F)),
            (
                AccessData(
                    access_code=102030,
                    detection_error=True,
                    permission=True,
                    read_right_to_left=True,
                    encrypted=True,
                    index=15,
                ),
                (0x10, 0x20, 0x30, 0xFF),
            ),
        ],
    )
    def test_parse(self, value: AccessData, raw: tuple[int, ...]) -> None:
        """Test DPTAccessData parsing and streaming."""
        knx_value = DPTAccessData.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTAccessData.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test DPTAccessData serializing from a dict."""
        assert DPTAccessData.to_knx(
            {"access_code": 123456, "permission": True, "index": 13}
        ) == DPTArray((0x12, 0x34, 0x56, 0x4D))

    @pytest.mark.parametrize(
        "value",
        [
            AccessData(access_code=-1),
            AccessData(access_code=1_000_000),
            AccessData(access_code=0, index=-1),
            AccessData(access_code=0, index=16),
            {"access_code": 1_000_000},
            {"access_code": 0, "index": 16},
        ],
    )
    def test_to_knx_limits(self, value: AccessData | dict[str, Any]) -> None:
        """Test DPTAccessData serializing out of range values."""
        with pytest.raises(ConversionError):
            DPTAccessData.to_knx(value)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            "123456",
            {},
            {"access_code": "a"},
            {"access_code": 1, "permission": "a"},
            AccessData(access_code="a"),  # type: ignore[arg-type]
            AccessData(access_code=1.5),  # type: ignore[arg-type]
            AccessData(access_code=1, permission=1),  # type: ignore[arg-type]
            AccessData(access_code=1, encrypted="a"),  # type: ignore[arg-type]
        ],
    )
    def test_to_knx_wrong_value(self, value: Any) -> None:
        """Test DPTAccessData serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTAccessData.to_knx(value)

    @pytest.mark.parametrize(
        "raw",
        [
            (0xA0, 0x00, 0x00, 0x00),
            (0x0A, 0x00, 0x00, 0x00),
            (0x00, 0x00, 0x0F, 0x00),
            (0xFF, 0xFF, 0xFF, 0xFF),
        ],
    )
    def test_from_knx_invalid_digit(self, raw: tuple[int, ...]) -> None:
        """Test DPTAccessData parsing digits out of range 0..9."""
        with pytest.raises(ConversionError):
            DPTAccessData.from_knx(DPTArray(raw))

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x12, 0x34, 0x56)),
            DPTArray((0x12, 0x34, 0x56, 0x4D, 0x00)),
            DPTBinary(1),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test DPTAccessData parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTAccessData.from_knx(payload)

    @pytest.mark.parametrize("value_type", ["15.000", "access_data"])
    def test_parse_transcoder(self, value_type: str) -> None:
        """Test DPTAccessData lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder(value_type) is DPTAccessData

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTAccessData."""
        assert DPTAccessData.get_dict_schema() == [
            {
                "name": "access_code",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 999999,
            },
            {
                "name": "detection_error",
                "type": "boolean",
                "required": False,
                "default": False,
            },
            {
                "name": "permission",
                "type": "boolean",
                "required": False,
                "default": False,
            },
            {
                "name": "read_right_to_left",
                "type": "boolean",
                "required": False,
                "default": False,
            },
            {
                "name": "encrypted",
                "type": "boolean",
                "required": False,
                "default": False,
            },
            {
                "name": "index",
                "type": "integer",
                "required": False,
                "default": 0,
                "value_min": 0,
                "value_max": 15,
            },
        ]
