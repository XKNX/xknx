"""Unit test for KNX DPT 217 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTVersion, Version
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestVersion:
    """Test Version class."""

    def test_dict(self) -> None:
        """Test from_dict and as_dict methods."""
        data = {"magic_number": 1, "version": 2, "revision": 3}
        value = Version.from_dict(data)
        assert value == Version(1, 2, 3)
        assert value.as_dict() == data

    @pytest.mark.parametrize(
        "data",
        [
            {"magic_number": 1, "version": 2},
            {"magic_number": "a", "version": 2, "revision": 3},
            {"magic_number": None, "version": 2, "revision": 3},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            Version.from_dict(data)

    def test_str(self) -> None:
        """Test the string representation."""
        assert str(Version(0, 1, 13)) == "0.1.13"


class TestDPTVersion:
    """Test class for KNX DPTVersion objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (Version(0, 0, 0), (0x00, 0x00)),
            (Version(0, 0, 13), (0x00, 0x0D)),
            (Version(0, 1, 0), (0x00, 0x40)),
            (Version(1, 0, 0), (0x08, 0x00)),
            (Version(1, 2, 3), (0x08, 0x83)),
            (Version(31, 31, 63), (0xFF, 0xFF)),
        ],
    )
    def test_dpt_version_value(self, value: Version, raw: tuple[int, ...]) -> None:
        """Test DPTVersion parsing and streaming."""
        knx_value = DPTVersion.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTVersion.from_knx(knx_value) == value

    def test_dpt_version_to_knx_from_dict(self) -> None:
        """Test DPTVersion parsing from a dict."""
        knx_value = DPTVersion.to_knx({"magic_number": 1, "version": 2, "revision": 3})
        assert knx_value == DPTArray((0x08, 0x83))

    @pytest.mark.parametrize(
        "value",
        [
            Version(32, 0, 0),
            Version(0, 32, 0),
            Version(0, 0, 64),
            Version(-1, 0, 0),
        ],
    )
    def test_dpt_version_to_knx_limits(self, value: Version) -> None:
        """Test DPTVersion with values out of range."""
        with pytest.raises(ConversionError):
            DPTVersion.to_knx(value)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            (0x00,),
            (0x00, 0x00, 0x00),
        ],
    )
    def test_dpt_version_to_knx_wrong_value(self, value: Any) -> None:
        """Test DPTVersion with wrong value type."""
        with pytest.raises(ConversionError):
            DPTVersion.to_knx(value)

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00,)),
            DPTArray((0x00, 0x00, 0x00)),
        ],
    )
    def test_dpt_version_from_knx_wrong_payload(self, payload: DPTArray) -> None:
        """Test DPTVersion parsing a payload of the wrong length."""
        with pytest.raises(CouldNotParseTelegram):
            DPTVersion.from_knx(payload)

    def test_lookup(self) -> None:
        """Test looking up DPTVersion by number and value type."""
        assert DPTVersion.parse_transcoder("version") is DPTVersion
        assert DPTVersion.parse_transcoder("217.001") is DPTVersion
