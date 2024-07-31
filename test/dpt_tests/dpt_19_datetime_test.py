"""Unit test for KNX datetime objects."""

import datetime

import pytest

from xknx.dpt import DPTArray, DPTBinary, DPTDateTime
from xknx.dpt.dpt_19 import KNXDateTime, KNXDayOfWeek
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestKNXDateTime:
    """Test class for KNX datetime objects."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {
                    "year": 1900,
                    "month": 1,
                    "day": 1,
                    "hour": 0,
                    "minutes": 0,
                    "seconds": 0,
                },
                KNXDateTime(1900, 1, 1, 0, 0, 0),
            ),
            (
                {
                    "year": 2155,
                    "month": 12,
                    "day": 31,
                    "hour": 23,
                    "minutes": 59,
                    "seconds": 59,
                    "day_of_week": "monday",
                },
                KNXDateTime(
                    2155,
                    12,
                    31,
                    23,
                    59,
                    59,
                    day_of_week=KNXDayOfWeek.MONDAY,
                ),
            ),
            (
                {
                    "year": 2017,
                    "month": 11,
                    "day": 28,
                    "hour": 23,
                    "minutes": 7,
                    "seconds": 24,
                    "day_of_week": "any_day",
                    "fault": True,
                    "working_day": True,
                    "dst": True,
                    "external_sync": True,
                    "source_reliable": True,
                },
                KNXDateTime(
                    2017,
                    11,
                    28,
                    23,
                    7,
                    24,
                    day_of_week=KNXDayOfWeek.ANY_DAY,
                    fault=True,
                    working_day=True,
                    dst=True,
                    external_sync=True,
                    source_reliable=True,
                ),
            ),
        ],
    )
    def test_dict(self, data, value):
        """Test from_dict and as_dict methods."""
        assert KNXDateTime.from_dict(data) == value
        default_dict = {
            "day_of_week": None,
            "fault": False,
            "working_day": None,
            "dst": False,
            "external_sync": False,
            "source_reliable": False,
        }
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            # invalid data
            {"hours": 1},  # additional "s" in "hours"
            {
                "year": 1900,
                "month": 1,
                "day": 1,
                "hour": 0,
                "minutes": 0,
                "seconds": 0,
                "invalid": True,
            },
        ],
    )
    def test_dict_invalid(self, data):
        """Test from_dict and as_dict methods."""
        with pytest.raises(ValueError):
            KNXDateTime.from_dict(data)

    @pytest.mark.parametrize(
        ("dt", "value"),
        [
            (
                datetime.datetime(2024, 7, 28, 22, 59, 17),
                KNXDateTime(2024, 7, 28, 22, 59, 17),
            ),
            (
                datetime.datetime(1999, 3, 31),
                KNXDateTime(1999, 3, 31, 0, 0, 0),  # datetime time defaults to 0:00:00
            ),
        ],
    )
    def test_as_datetime(self, dt, value):
        """Test from_time and as_time methods."""
        assert KNXDateTime.from_datetime(dt) == value
        assert value.as_datetime() == dt


class TestDPTDateTime:
    """Test class for KNX datetime objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                KNXDateTime(2017, 11, 28, 23, 7, 24),
                (0x75, 0x0B, 0x1C, 0x17, 0x07, 0x18, 0x24, 0x00),
            ),
            (
                KNXDateTime(1900, 1, 1, 0, 0, 0),
                (0x00, 0x1, 0x1, 0x00, 0x00, 0x00, 0x24, 0x00),
            ),
            (
                KNXDateTime(2155, 12, 31, 23, 59, 59, day_of_week=KNXDayOfWeek.SUNDAY),
                (0xFF, 0x0C, 0x1F, 0xF7, 0x3B, 0x3B, 0x20, 0x00),
            ),
        ],
    )
    def test_parse(self, value, raw):
        """Test parsing and streaming."""
        knx_value = DPTDateTime.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTDateTime.from_knx(knx_value) == value

    def test_from_knx_wrong_value(self):
        """Test parsing DPTDateTime from KNX with wrong binary values."""
        with pytest.raises(CouldNotParseTelegram):
            DPTDateTime.from_knx(DPTArray((0xF8, 0x23)))
        with pytest.raises(ConversionError):
            # (second byte exceeds value...)
            DPTDateTime.from_knx(
                DPTArray((0xFF, 0x0D, 0x1F, 0xF7, 0x3B, 0x3B, 0x00, 0x00))
            )
        with pytest.raises(CouldNotParseTelegram):
            DPTDateTime.from_knx(DPTBinary(True))

    def test_to_knx_wrong_value(self):
        """Test parsing from DPTDateTime object from wrong value."""
        with pytest.raises(ConversionError):
            # year out of range
            DPTDateTime.to_knx(KNXDateTime(1889, 1, 1, 0, 0, 0))
        with pytest.raises(ConversionError):
            # day out of range (0)
            DPTDateTime.to_knx(KNXDateTime(2000, 1, 0, 0, 0, 0))
        with pytest.raises(ConversionError):
            # hour out of range
            DPTDateTime.to_knx(KNXDateTime(2000, 1, 1, 25, 0, 0))
        with pytest.raises(ConversionError):
            # minutes out of range
            DPTDateTime.to_knx(KNXDateTime(2000, 1, 1, 1, 60, 0))
        with pytest.raises(ConversionError):
            # seconds out of range
            DPTDateTime.to_knx(KNXDateTime(2000, 1, 1, 1, 0, 60))
        with pytest.raises(ConversionError):
            # seconds out of range at hour 24
            DPTDateTime.to_knx(KNXDateTime(2000, 1, 1, 24, 0, 1))
        with pytest.raises(ConversionError):
            DPTDateTime.to_knx("hello")
        with pytest.raises(ConversionError):
            DPTDateTime.to_knx((1, 2, 3))
