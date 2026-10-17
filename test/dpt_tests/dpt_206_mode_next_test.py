"""Unit test for KNX DPT 206 mode and time delay objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_20 import HVACOperationMode
from xknx.dpt.dpt_206 import (
    BuildingMode,
    BuildingModeNext,
    DHWMode,
    DHWModeNext,
    DPTBuildingModeNext,
    DPTDHWModeNext,
    DPTHVACModeNext,
    DPTOccModeNext,
    HVACModeNext,
    OccupancyMode,
    OccupancyModeNext,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestHVACModeNext:
    """Test HVACModeNext and DHWModeNext classes."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            ({}, HVACModeNext()),
            ({"mode": "comfort"}, HVACModeNext(mode=HVACOperationMode.COMFORT)),
            ({"delay_time": 60}, HVACModeNext(delay_time=60)),
            (
                {"mode": "building_protection", "delay_time": 65_535},
                HVACModeNext(HVACOperationMode.BUILDING_PROTECTION, 65_535),
            ),
            (
                {"mode": None, "delay_time": None},
                HVACModeNext(),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: HVACModeNext) -> None:
        """Test from_dict and as_dict methods."""
        assert HVACModeNext.from_dict(data) == value
        assert value.as_dict() == {"mode": None, "delay_time": None} | data

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            ({}, DHWModeNext()),
            ({"mode": "legio_protect"}, DHWModeNext(mode=DHWMode.LEGIO_PROTECT)),
            (
                {"mode": "off_frost_protect", "delay_time": 1},
                DHWModeNext(DHWMode.OFF_FROST_PROTECT, 1),
            ),
        ],
    )
    def test_dict_dhw(self, data: dict[str, Any], value: DHWModeNext) -> None:
        """Test from_dict and as_dict methods of DHWModeNext."""
        assert DHWModeNext.from_dict(data) == value
        assert value.as_dict() == {"mode": None, "delay_time": None} | data

    @pytest.mark.parametrize(
        "data",
        [
            {"mode": "invalid"},
            {"mode": 1.5},
            {"delay_time": "a"},
            {"delay_time": [1]},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            HVACModeNext.from_dict(data)
        with pytest.raises(ValueError):
            DHWModeNext.from_dict(data)


class TestOccupancyModeNext:
    """Test OccupancyModeNext and BuildingModeNext classes."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"mode": "occupied"},
                OccupancyModeNext(mode=OccupancyMode.OCCUPIED),
            ),
            (
                {"mode": "not_occupied", "delay_time": 30},
                OccupancyModeNext(OccupancyMode.NOT_OCCUPIED, 30),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: OccupancyModeNext) -> None:
        """Test from_dict and as_dict methods."""
        assert OccupancyModeNext.from_dict(data) == value
        assert value.as_dict() == {"delay_time": None} | data

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"mode": "building_in_use"},
                BuildingModeNext(mode=BuildingMode.BUILDING_IN_USE),
            ),
            (
                {"mode": "building_protection", "delay_time": 120},
                BuildingModeNext(BuildingMode.BUILDING_PROTECTION, 120),
            ),
        ],
    )
    def test_dict_building(self, data: dict[str, Any], value: BuildingModeNext) -> None:
        """Test from_dict and as_dict methods of BuildingModeNext."""
        assert BuildingModeNext.from_dict(data) == value
        assert value.as_dict() == {"delay_time": None} | data

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"delay_time": 10},
            {"mode": "invalid"},
            {"mode": 0, "delay_time": "a"},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            OccupancyModeNext.from_dict(data)
        with pytest.raises(ValueError):
            BuildingModeNext.from_dict(data)


class TestDPTHVACModeNext:
    """Test class for KNX DPTHVACModeNext objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (HVACModeNext(), (0x00, 0x00, 0x00)),
            (HVACModeNext(HVACOperationMode.COMFORT), (0x00, 0x00, 0x01)),
            (HVACModeNext(HVACOperationMode.STANDBY, 1), (0x00, 0x01, 0x02)),
            (HVACModeNext(HVACOperationMode.ECONOMY, 300), (0x01, 0x2C, 0x03)),
            (
                HVACModeNext(HVACOperationMode.BUILDING_PROTECTION, 65_535),
                (0xFF, 0xFF, 0x04),
            ),
            (HVACModeNext(delay_time=90), (0x00, 0x5A, 0x00)),
        ],
    )
    def test_values(self, value: HVACModeNext, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        knx_value = DPTHVACModeNext.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTHVACModeNext.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test serializing from a dict."""
        assert DPTHVACModeNext.to_knx(
            {"mode": "economy", "delay_time": 300}
        ) == DPTArray((0x01, 0x2C, 0x03))

    @pytest.mark.parametrize(
        "value",
        [
            HVACModeNext(HVACOperationMode.AUTO, 10),
            HVACModeNext(HVACOperationMode.COMFORT, 0),
            HVACModeNext(HVACOperationMode.COMFORT, 65_536),
            HVACModeNext(HVACOperationMode.COMFORT, -1),
            {"mode": "auto"},
            {"mode": "invalid"},
            {"delay_time": "a"},
            None,
            1,
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTHVACModeNext.to_knx(value)

    @pytest.mark.parametrize("mode", [0x05, 0xFF])
    def test_from_knx_reserved_mode(self, mode: int) -> None:
        """Test parsing reserved HVAC modes."""
        with pytest.raises(ConversionError):
            DPTHVACModeNext.from_knx(DPTArray((0x00, 0x01, mode)))

    @pytest.mark.parametrize(
        "payload",
        [DPTArray((0x00, 0x01)), DPTArray((0x00, 0x01, 0x01, 0x00)), DPTBinary(1)],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing wrong payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTHVACModeNext.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema - AUTO is not part of the options."""
        assert DPTHVACModeNext.get_dict_schema() == [
            {
                "name": "mode",
                "type": "enum",
                "required": False,
                "options": ["comfort", "standby", "economy", "building_protection"],
            },
            {
                "name": "delay_time",
                "type": "integer",
                "required": False,
                "value_min": 1,
                "value_max": 65_535,
            },
        ]


class TestDPTDHWModeNext:
    """Test class for KNX DPTDHWModeNext objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (DHWModeNext(), (0x00, 0x00, 0x00)),
            (DHWModeNext(DHWMode.LEGIO_PROTECT), (0x00, 0x00, 0x01)),
            (DHWModeNext(DHWMode.NORMAL, 1), (0x00, 0x01, 0x02)),
            (DHWModeNext(DHWMode.REDUCED, 480), (0x01, 0xE0, 0x03)),
            (DHWModeNext(DHWMode.OFF_FROST_PROTECT, 65_535), (0xFF, 0xFF, 0x04)),
            (DHWModeNext(delay_time=15), (0x00, 0x0F, 0x00)),
        ],
    )
    def test_values(self, value: DHWModeNext, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        knx_value = DPTDHWModeNext.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTDHWModeNext.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        "value",
        [
            DHWModeNext(DHWMode.AUTO),
            DHWModeNext(DHWMode.NORMAL, 65_536),
            DHWModeNext(HVACOperationMode.COMFORT),  # type: ignore[arg-type]
            {"mode": "auto"},
            {"mode": "comfort"},
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTDHWModeNext.to_knx(value)

    @pytest.mark.parametrize("mode", [0x05, 0xFF])
    def test_from_knx_reserved_mode(self, mode: int) -> None:
        """Test parsing reserved DHW modes."""
        with pytest.raises(ConversionError):
            DPTDHWModeNext.from_knx(DPTArray((0x00, 0x01, mode)))

    def test_from_knx_wrong_payload(self) -> None:
        """Test parsing a wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTDHWModeNext.from_knx(DPTArray((0x00, 0x01)))

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema - AUTO is not part of the options."""
        assert DPTDHWModeNext.get_dict_schema() == [
            {
                "name": "mode",
                "type": "enum",
                "required": False,
                "options": ["legio_protect", "normal", "reduced", "off_frost_protect"],
            },
            {
                "name": "delay_time",
                "type": "integer",
                "required": False,
                "value_min": 1,
                "value_max": 65_535,
            },
        ]


class TestDPTOccModeNext:
    """Test class for KNX DPTOccModeNext objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (OccupancyModeNext(OccupancyMode.OCCUPIED), (0x00, 0x00, 0x00)),
            (OccupancyModeNext(OccupancyMode.STANDBY, 1), (0x00, 0x01, 0x01)),
            (
                OccupancyModeNext(OccupancyMode.NOT_OCCUPIED, 65_535),
                (0xFF, 0xFF, 0x02),
            ),
        ],
    )
    def test_values(self, value: OccupancyModeNext, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        knx_value = DPTOccModeNext.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTOccModeNext.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        "value",
        [
            OccupancyModeNext(OccupancyMode.OCCUPIED, 0),
            OccupancyModeNext(OccupancyMode.OCCUPIED, 65_536),
            OccupancyModeNext(BuildingMode.BUILDING_IN_USE),  # type: ignore[arg-type]
            {},
            {"mode": "building_in_use"},
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTOccModeNext.to_knx(value)

    @pytest.mark.parametrize("mode", [0x03, 0xFF])
    def test_from_knx_reserved_mode(self, mode: int) -> None:
        """Test parsing reserved occupancy modes."""
        with pytest.raises(ConversionError):
            DPTOccModeNext.from_knx(DPTArray((0x00, 0x01, mode)))

    def test_from_knx_wrong_payload(self) -> None:
        """Test parsing a wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTOccModeNext.from_knx(DPTArray((0x00, 0x01, 0x00, 0x00)))

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema."""
        assert DPTOccModeNext.get_dict_schema() == [
            {
                "name": "mode",
                "type": "enum",
                "required": True,
                "options": ["occupied", "standby", "not_occupied"],
            },
            {
                "name": "delay_time",
                "type": "integer",
                "required": False,
                "value_min": 1,
                "value_max": 65_535,
            },
        ]


class TestDPTBuildingModeNext:
    """Test class for KNX DPTBuildingModeNext objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (BuildingModeNext(BuildingMode.BUILDING_IN_USE), (0x00, 0x00, 0x00)),
            (BuildingModeNext(BuildingMode.BUILDING_NOT_USED, 2), (0x00, 0x02, 0x01)),
            (
                BuildingModeNext(BuildingMode.BUILDING_PROTECTION, 65_535),
                (0xFF, 0xFF, 0x02),
            ),
        ],
    )
    def test_values(self, value: BuildingModeNext, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        knx_value = DPTBuildingModeNext.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTBuildingModeNext.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        "value",
        [
            BuildingModeNext(BuildingMode.BUILDING_IN_USE, 0),
            BuildingModeNext(BuildingMode.BUILDING_IN_USE, 65_536),
            {},
            {"mode": "occupied"},
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTBuildingModeNext.to_knx(value)

    @pytest.mark.parametrize("mode", [0x03, 0xFF])
    def test_from_knx_reserved_mode(self, mode: int) -> None:
        """Test parsing reserved building modes."""
        with pytest.raises(ConversionError):
            DPTBuildingModeNext.from_knx(DPTArray((0x00, 0x01, mode)))

    def test_from_knx_wrong_payload(self) -> None:
        """Test parsing a wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTBuildingModeNext.from_knx(DPTArray((0x00,)))

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema."""
        assert DPTBuildingModeNext.get_dict_schema() == [
            {
                "name": "mode",
                "type": "enum",
                "required": True,
                "options": [
                    "building_in_use",
                    "building_not_used",
                    "building_protection",
                ],
            },
            {
                "name": "delay_time",
                "type": "integer",
                "required": False,
                "value_min": 1,
                "value_max": 65_535,
            },
        ]


@pytest.mark.parametrize(
    ("dpt_class", "dpt_number", "value_type"),
    [
        (DPTHVACModeNext, "206.100", "hvac_mode_next"),
        (DPTDHWModeNext, "206.102", "dhw_mode_next"),
        (DPTOccModeNext, "206.104", "occupancy_mode_next"),
        (DPTBuildingModeNext, "206.105", "building_mode_next"),
    ],
)
def test_lookup(dpt_class: type[DPTBase], dpt_number: str, value_type: str) -> None:
    """Test lookup by DPT number and value_type."""
    assert DPTBase.parse_transcoder(dpt_number) is dpt_class
    assert DPTBase.parse_transcoder(value_type) is dpt_class
