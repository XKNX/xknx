"""Unit test for KNX DPT 247 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_19 import KNXDateTime, KNXDayOfWeek
from xknx.dpt.dpt_247 import ConverterTestInfo, DPTConverterTestInfo
from xknx.exceptions import ConversionError, CouldNotParseTelegram

_TEST_START = KNXDateTime(
    year=2024,
    month=3,
    day=15,
    hour=10,
    minutes=30,
    seconds=0,
    day_of_week=KNXDayOfWeek.FRIDAY,
    working_day=True,
)
_TEST_START_RAW = (0x7C, 0x03, 0x0F, 0xAA, 0x1E, 0x00, 0x40, 0x00)
_INVALID_START_RAW = (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3E, 0x00)


class TestConverterTestInfo:
    """Test ConverterTestInfo class."""

    def test_dict(self) -> None:
        """Test from_dict and as_dict methods."""
        value = ConverterTestInfo(
            test_start=_TEST_START,
            automated_test_interval=168,
            test_execution_time=30,
        )
        data = {
            "year": 2024,
            "month": 3,
            "day": 15,
            "hour": 10,
            "minutes": 30,
            "seconds": 0,
            "day_of_week": "friday",
            "fault": False,
            "working_day": True,
            "dst": False,
            "external_sync": False,
            "source_reliable": False,
            "automated_test_interval": 168,
            "test_execution_time": 30,
        }
        assert value.as_dict() == data
        assert ConverterTestInfo.from_dict(data) == value

    def test_dict_invalid_start(self) -> None:
        """Test from_dict with all date and time fields omitted."""
        value = ConverterTestInfo.from_dict(
            {"automated_test_interval": 0, "test_execution_time": 0}
        )
        assert value == ConverterTestInfo(KNXDateTime(), 0, 0)

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"automated_test_interval": 0},
            {"test_execution_time": 0},
            {"automated_test_interval": "a", "test_execution_time": 0},
            {"automated_test_interval": 0, "test_execution_time": None},
            {"automated_test_interval": 0, "test_execution_time": 0, "unknown": 1},
            {
                "automated_test_interval": 0,
                "test_execution_time": 0,
                "day_of_week": "x",
            },
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            ConverterTestInfo.from_dict(data)


class TestDPTConverterTestInfo:
    """Test class for KNX DPTConverterTestInfo objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                ConverterTestInfo(_TEST_START, 168, 30),
                (*_TEST_START_RAW, 0x00, 0xA8, 0x00, 0x1E),
            ),
            (
                ConverterTestInfo(KNXDateTime(), 0, 0),
                (*_INVALID_START_RAW, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                ConverterTestInfo(KNXDateTime(), 65_535, 65_535),
                (*_INVALID_START_RAW, 0xFF, 0xFF, 0xFF, 0xFF),
            ),
        ],
    )
    def test_to_knx_from_knx(
        self, value: ConverterTestInfo, raw: tuple[int, ...]
    ) -> None:
        """Test DPTConverterTestInfo parsing and streaming."""
        knx_value = DPTConverterTestInfo.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTConverterTestInfo.from_knx(knx_value) == value
        assert DPTConverterTestInfo.to_knx(value.as_dict()) == DPTArray(raw)

    def test_from_knx_invalid_date_time(self) -> None:
        """Test parsing an out of range date and time."""
        with pytest.raises(ConversionError):
            DPTConverterTestInfo.from_knx(DPTArray((0x00,) * 12))

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00,) * 11),
            DPTArray((0x00,) * 13),
            DPTBinary(0),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTConverterTestInfo.from_knx(payload)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            {"automated_test_interval": 0},
            ConverterTestInfo(KNXDateTime(), -1, 0),
            ConverterTestInfo(KNXDateTime(), 65_536, 0),
            ConverterTestInfo(KNXDateTime(), 0, -1),
            ConverterTestInfo(KNXDateTime(), 0, 65_536),
            ConverterTestInfo(KNXDateTime(month=13, day=1), 0, 0),
            ConverterTestInfo(None, 0, 0),  # type: ignore[arg-type]
        ],
    )
    def test_to_knx_wrong_value(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTConverterTestInfo.to_knx(value)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTConverterTestInfo."""
        assert DPTConverterTestInfo.get_dict_schema() == [
            *KNXDateTime.get_dict_schema(),
            {
                "name": "automated_test_interval",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 65_535,
            },
            {
                "name": "test_execution_time",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 65_535,
            },
        ]

    def test_lookup(self) -> None:
        """Test transcoder lookup by DPT number and value type."""
        assert DPTBase.parse_transcoder("247.600") is DPTConverterTestInfo
        assert DPTBase.parse_transcoder("converter_test_info") is DPTConverterTestInfo
