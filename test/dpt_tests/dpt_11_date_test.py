"""Unit test for KNX date objects."""

import datetime
from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTDate
from xknx.dpt.dpt_11 import KNXDate
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestKNXDate:
    """Test class for KNX date objects."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            ({"year": 1990, "month": 1, "day": 1}, KNXDate(1990, 1, 1)),
            ({"year": 2024, "month": 7, "day": 26}, KNXDate(2024, 7, 26)),
            ({"year": 2089, "month": 12, "day": 31}, KNXDate(2089, 12, 31)),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: KNXDate) -> None:
        """Test from_dict and as_dict methods."""
        assert KNXDate.from_dict(data) == value
        assert value.as_dict() == data

    @pytest.mark.parametrize(
        "data",
        [
            # invalid data
            {"year": 1},
            {"year": "a"},
            {"month": 2, "day": 3},
            {"year": 2, "day": 3},
            {"year": 1, "month": 2},
            {"year": 1, "month": 2, "day": "a"},
            {"year": 1, "month": None, "day": 3},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict and as_dict methods."""
        with pytest.raises(ValueError):
            KNXDate.from_dict(data)

    @pytest.mark.parametrize(
        ("date", "value"),
        [
            (datetime.date(1990, 1, 1), KNXDate(1990, 1, 1)),
            (datetime.date(2024, 7, 26), KNXDate(2024, 7, 26)),
            (datetime.date(2089, 12, 31), KNXDate(2089, 12, 31)),
        ],
    )
    def test_as_date(self, date: datetime.date, value: KNXDate) -> None:
        """Test from_time and as_time methods."""
        assert KNXDate.from_date(date) == value
        assert value.as_date() == date


class TestDPTDate:
    """Test class for KNX date objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (KNXDate(2002, 1, 4), (0x04, 0x01, 0x02)),
            (KNXDate(1990, 1, 31), (0x1F, 0x01, 0x5A)),
            (KNXDate(2089, 12, 4), (0x04, 0x0C, 0x59)),
        ],
    )
    def test_from_knx(self, value: KNXDate, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        knx_value = DPTDate.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTDate.from_knx(knx_value) == value

    def test_from_knx_wrong_parameter(self) -> None:
        """Test parsing from DPTDate object from wrong binary values."""
        with pytest.raises(CouldNotParseTelegram):
            DPTDate.from_knx(DPTArray((0xF8, 0x23)))

    def test_to_knx_wrong_value(self) -> None:
        """Test parsing from DPTDate object from wrong string value."""
        with pytest.raises(ConversionError):
            DPTDate.to_knx(KNXDate(2090, 1, 1))  # year out of range
        with pytest.raises(ConversionError):
            DPTDate.to_knx(KNXDate(1990, 0, 1))  # month out of range
        with pytest.raises(ConversionError):
            DPTDate.to_knx(KNXDate(1990, 1, 32))  # day out of range
        with pytest.raises(ConversionError):
            DPTDate.to_knx("hello")

    def test_from_knx_wrong_range_month(self) -> None:
        """Test Exception when parsing DPTDAte from KNX with wrong month."""
        with pytest.raises(ConversionError):
            DPTDate.from_knx(DPTArray((0x04, 0x00, 0x59)))

    def test_from_knx_wrong_range_year(self) -> None:
        """Test Exception when parsing DPTDate from KNX with wrong year."""
        with pytest.raises(ConversionError):
            DPTDate.from_knx(DPTArray((0x04, 0x01, 0x64)))
