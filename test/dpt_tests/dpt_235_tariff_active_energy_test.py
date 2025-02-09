"""Unit test for KNX DPT 235 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTTariffActiveEnergy, TariffActiveEnergy
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestTariffActiveEnergy:
    """Test TariffActiveEnergy class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"energy": -2_147_483_648, "tariff": 0},
                TariffActiveEnergy(-2_147_483_648, 0),
            ),
            (
                {"energy": 2_147_483_647, "tariff": 255},
                TariffActiveEnergy(2_147_483_647, 255),
            ),
            ({"tariff": 128}, TariffActiveEnergy(None, 128)),
            ({"energy": 50}, TariffActiveEnergy(50, None)),
            ({}, TariffActiveEnergy()),
            (
                {"energy": 255, "tariff": None},
                TariffActiveEnergy(255, None),
            ),
            (
                {"energy": None, "tariff": 128},
                TariffActiveEnergy(None, 128),
            ),
            ({"energy": 255, "tariff": None}, TariffActiveEnergy(255, None)),
            ({"tariff": 128}, TariffActiveEnergy(None, 128)),
            ({"energy": 128}, TariffActiveEnergy(128, None)),
            ({"energy": 128, "tariff": 128}, TariffActiveEnergy(128, 128)),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: TariffActiveEnergy) -> None:
        """Test from_dict and as_dict methods."""
        test_value = TariffActiveEnergy.from_dict(data)
        assert test_value == value
        # fields default to `None`
        default_dict = {"energy": None, "tariff": None}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            # invalid data
            {"energy": 128, "tariff": "a"},
            {"energy": "a", "tariff": 128},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict and as_dict methods."""
        with pytest.raises(ValueError):
            TariffActiveEnergy.from_dict(data)


class TestDPTTariffActiveEnergy:
    """Test class for KNX DPTTariffActiveEnergy objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                TariffActiveEnergy(0, 0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x03),
            ),  # zero values
            (
                TariffActiveEnergy(-2_147_483_648, 0),
                (0x80, 0x00, 0x00, 0x00, 0x00, 0x03),
            ),  # min values
            (
                TariffActiveEnergy(2_147_483_647, 254),
                (0x7F, 0xFF, 0xFF, 0xFF, 0xFE, 0x03),
            ),  # max values
            (
                TariffActiveEnergy(None, 0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x01),
            ),  # energy None
            (
                TariffActiveEnergy(0, None),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x02),
            ),  # tariff None
            (TariffActiveEnergy(None, None), (0x00, 0x00, 0x00, 0x00, 0x00, 0x00)),
            (TariffActiveEnergy(128, 128), (0x00, 0x00, 0x00, 0x80, 0x80, 0x03)),
            (TariffActiveEnergy(204, 204), (0x00, 0x00, 0x00, 0xCC, 0xCC, 0x03)),
        ],
    )
    def test_dpt_tariff_active_energy_value(
        self, value: TariffActiveEnergy, raw: tuple[int, ...]
    ) -> None:
        """Test DPTTariffActiveEnergy parsing and streaming."""
        knx_value = DPTTariffActiveEnergy.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTTariffActiveEnergy.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ({"tariff": 128, "energy": 128}, (0x00, 0x00, 0x00, 0x80, 0x80, 0x03)),
            ({"tariff": 204, "energy": 204}, (0x00, 0x00, 0x00, 0xCC, 0xCC, 0x03)),
        ],
    )
    def test_dpt_tariff_active_energy_to_knx_from_dict(
        self, value: dict[str, Any], raw: tuple[int, ...]
    ) -> None:
        """Test DPTTariffActiveEnergy parsing from a dict."""
        knx_value = DPTTariffActiveEnergy.to_knx(value)
        assert knx_value == DPTArray(raw)

    @pytest.mark.parametrize(
        ("value"),
        [
            TariffActiveEnergy(-2_147_483_649, 0),
            TariffActiveEnergy(2_147_483_648, 0),
            TariffActiveEnergy(0, -1),
            TariffActiveEnergy(0, 255),
        ],
    )
    def test_dpt_tariff_active_energy_to_knx_limits(
        self, value: TariffActiveEnergy
    ) -> None:
        """Test initialization of DPTTariffActiveEnergy with wrong value."""
        with pytest.raises(ConversionError):
            DPTTariffActiveEnergy.to_knx(value)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            (0xFF, 0x4E),
            1,
            ((0x00, 0xFF), 0x4E),
            ((0xFF, 0x4E), (0x12, 0x00)),
            ((0, 0), "a"),
            ((0, 0), 0.4),
            TariffActiveEnergy(tariff=0, energy="a"),
            TariffActiveEnergy(tariff="a", energy=0),
        ],
    )
    def test_dpt_tariff_active_energy_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTTariffActiveEnergy parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTTariffActiveEnergy.to_knx(value)

    def test_dpt_tariff_active_energy_wrong_value_from_knx(self) -> None:
        """Test DPTTariffActiveEnergy parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPTTariffActiveEnergy.from_knx(DPTArray((0xFF, 0x4E)))
