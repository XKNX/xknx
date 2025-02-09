"""Unit test for KNX time objects."""

import datetime
from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBinary, DPTTime
from xknx.dpt.dpt_10 import KNXDay, KNXTime
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestKNXTime:
    """Test class for KNX time objects."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"hour": 5, "minutes": 10, "seconds": 9},
                KNXTime(5, 10, 9),
            ),
            (
                {"hour": 21, "minutes": 52, "seconds": 9, "day": "tuesday"},
                KNXTime(21, 52, 9, KNXDay.TUESDAY),
            ),
            (
                {"hour": 0, "minutes": 0, "seconds": 0},
                KNXTime(0, 0, 0, KNXDay.NO_DAY),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: KNXTime) -> None:
        """Test from_dict and as_dict methods."""
        assert KNXTime.from_dict(data) == value
        # day defaults to `no_day`
        default_dict = {"day": "no_day"}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            # invalid data
            {"hour": 1},
            {"hour": "a"},
            {"minutes": 2, "seconds": 3},
            {"hour": 2, "seconds": 3},
            {"hour": 1, "minutes": 2},
            {"hour": 1, "minutes": 2, "seconds": "a"},
            {"hour": 1, "minutes": 2, "seconds": 3, "day": "a"},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict and as_dict methods."""
        with pytest.raises(ValueError):
            KNXTime.from_dict(data)

    @pytest.mark.parametrize(
        ("time", "value"),
        [
            (datetime.time(5, 10, 9), KNXTime(5, 10, 9)),
            (datetime.time(21, 52, 9), KNXTime(21, 52, 9)),
            (datetime.time(0, 0, 0), KNXTime(0, 0, 0)),
            (datetime.time(23, 59, 59), KNXTime(23, 59, 59)),
        ],
    )
    def test_as_time(self, time: datetime.time, value: KNXTime) -> None:
        """Test from_time and as_time methods."""
        assert KNXTime.from_time(time) == value
        assert value.as_time() == time


class TestDPTTime:
    """Test class for KNX time objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (KNXTime(13, 23, 42, KNXDay.TUESDAY), (0x4D, 0x17, 0x2A)),
            (KNXTime(0, 0, 0, KNXDay.NO_DAY), (0x0, 0x0, 0x0)),
            (KNXTime(23, 59, 59, KNXDay.SUNDAY), (0xF7, 0x3B, 0x3B)),
        ],
    )
    def test_parse(self, value: KNXTime, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        knx_value = DPTTime.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTTime.from_knx(knx_value) == value

    def test_from_knx_wrong_value(self) -> None:
        """Test parsing from DPTTime object from wrong binary values."""
        with pytest.raises(ConversionError):
            # this parameter exceeds limit
            DPTTime.from_knx(DPTArray((0xF7, 0x3B, 0x3C)))
        with pytest.raises(CouldNotParseTelegram):
            DPTTime.from_knx(DPTArray((0xFF, 0x4E)))
        with pytest.raises(CouldNotParseTelegram):
            DPTTime.from_knx(DPTBinary(True))

    def test_to_knx_wrong_parameter(self) -> None:
        """Test parsing from DPTTime object from wrong value."""
        with pytest.raises(ConversionError):
            DPTTime.to_knx(KNXTime(24, 0, 0))  # out of range
        with pytest.raises(ConversionError):
            DPTTime.to_knx(KNXTime(0, 60, 0))  # out of range
        with pytest.raises(ConversionError):
            DPTTime.to_knx("fnord")
        with pytest.raises(ConversionError):
            DPTTime.to_knx((1, 2, 3))
