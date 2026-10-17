"""Unit test for KNX DPT 217 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTVersion, KNXVersion
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestKNXVersion:
    """Test KNXVersion class."""

    def test_dict(self) -> None:
        """Test from_dict and as_dict methods."""
        data = {"magic_number": 1, "version_number": 2, "revision_number": 3}
        value = KNXVersion.from_dict(data)
        assert value == KNXVersion(1, 2, 3)
        assert value.as_dict() == data

    @pytest.mark.parametrize(
        "data",
        [
            {"magic_number": 1, "version_number": 2},
            {"magic_number": "a", "version_number": 2, "revision_number": 3},
            {"magic_number": None, "version_number": 2, "revision_number": 3},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            KNXVersion.from_dict(data)

    def test_str(self) -> None:
        """Test the string representation."""
        assert str(KNXVersion(0, 1, 13)) == "0.1.13"

    def test_invalid(self) -> None:
        """Test the encoding of invalid version information."""
        assert KNXVersion(31, 31, 63) == KNXVersion.INVALID
        assert KNXVersion.INVALID.is_invalid
        assert KNXVersion(31, 31, 63).is_invalid
        assert not KNXVersion(31, 31, 62).is_invalid
        assert not KNXVersion(0, 0, 0).is_invalid


class TestDPTVersion:
    """Test class for KNX DPTVersion objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (KNXVersion(0, 0, 0), (0x00, 0x00)),
            (KNXVersion(0, 0, 13), (0x00, 0x0D)),
            (KNXVersion(0, 1, 0), (0x00, 0x40)),
            (KNXVersion(1, 0, 0), (0x08, 0x00)),
            (KNXVersion(1, 2, 3), (0x08, 0x83)),
            (KNXVersion(31, 31, 63), (0xFF, 0xFF)),
        ],
    )
    def test_dpt_version_value(self, value: KNXVersion, raw: tuple[int, ...]) -> None:
        """Test DPTVersion parsing and streaming."""
        knx_value = DPTVersion.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTVersion.from_knx(knx_value) == value

    def test_dpt_version_invalid(self) -> None:
        """Test DPTVersion with invalid version information."""
        assert DPTVersion.to_knx(KNXVersion.INVALID) == DPTArray((0xFF, 0xFF))
        assert DPTVersion.from_knx(DPTArray((0xFF, 0xFF))).is_invalid

    def test_dpt_version_to_knx_from_dict(self) -> None:
        """Test DPTVersion parsing from a dict."""
        knx_value = DPTVersion.to_knx(
            {"magic_number": 1, "version_number": 2, "revision_number": 3}
        )
        assert knx_value == DPTArray((0x08, 0x83))

    @pytest.mark.parametrize(
        "value",
        [
            KNXVersion(32, 0, 0),
            KNXVersion(0, 32, 0),
            KNXVersion(0, 0, 64),
            KNXVersion(-1, 0, 0),
        ],
    )
    def test_dpt_version_to_knx_limits(self, value: KNXVersion) -> None:
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
