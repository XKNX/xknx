"""Unit test for KNX DPT 22 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_1 import HeatCool
from xknx.dpt.dpt_22 import (
    ChannelActivation16,
    DPTChannelActivation16,
    DPTMedia,
    DPTStatusDHWC,
    DPTStatusRHCC,
    Media,
    StatusDHWC,
    StatusRHCC,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram

DHWC_FIELDS = (
    "fault",
    "dhw_load_active",
    "legio_prot_active",
    "dhw_push_active",
    "other_energy_source_active",
    "solar_energy_only",
    "solar_energy_support",
    "temp_optim_shift_active",
)
RHCC_FLAGS = (
    "fault",
    "status_eco_h",
    "temp_flow_limit",
    "temp_return_limit",
    "status_morning_boost_h",
    "status_start_optim",
    "status_stop_optim",
    "heating_disabled",
    "status_eco_c",
    "status_pre_cool",
    "cooling_disabled",
    "dew_point_status",
    "frost_alarm",
    "overheat_alarm",
)
MEDIA_FIELDS = ("tp1", "pl110", "rf", "knx_ip")
CHANNEL_FIELDS = tuple(f"channel_{n}" for n in range(1, 17))


class TestDPTStatusDHWC:
    """Test class for KNX DPTStatusDHWC objects."""

    @pytest.mark.parametrize(
        ("field", "raw"),
        [
            ("fault", (0x00, 0x01)),
            ("dhw_load_active", (0x00, 0x02)),
            ("legio_prot_active", (0x00, 0x04)),
            ("dhw_push_active", (0x00, 0x08)),
            ("other_energy_source_active", (0x00, 0x10)),
            ("solar_energy_only", (0x00, 0x20)),
            ("solar_energy_support", (0x00, 0x40)),
            ("temp_optim_shift_active", (0x00, 0x80)),
        ],
    )
    def test_single_bit(self, field: str, raw: tuple[int, ...]) -> None:
        """Test each bit of DPTStatusDHWC."""
        value = StatusDHWC(**{field: True})
        assert DPTStatusDHWC.to_knx(value) == DPTArray(raw)
        assert DPTStatusDHWC.from_knx(DPTArray(raw)) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (StatusDHWC(), (0x00, 0x00)),
            (StatusDHWC(**dict.fromkeys(DHWC_FIELDS, True)), (0x00, 0xFF)),
            (
                StatusDHWC(dhw_load_active=True, solar_energy_support=True),
                (0x00, 0x42),
            ),
        ],
    )
    def test_values(self, value: StatusDHWC, raw: tuple[int, ...]) -> None:
        """Test DPTStatusDHWC parsing and streaming."""
        assert DPTStatusDHWC.to_knx(value) == DPTArray(raw)
        assert DPTStatusDHWC.from_knx(DPTArray(raw)) == value

    def test_reserved_bits_ignored(self) -> None:
        """Test reserved bits 8..15 are ignored on receive."""
        assert DPTStatusDHWC.from_knx(DPTArray((0xFF, 0x01))) == StatusDHWC(fault=True)

    def test_dict(self) -> None:
        """Test from_dict and as_dict methods."""
        assert StatusDHWC.from_dict({"legio_prot_active": True}) == StatusDHWC(
            legio_prot_active=True
        )
        assert StatusDHWC(fault=True).as_dict() == dict.fromkeys(DHWC_FIELDS, False) | {
            "fault": True
        }
        assert DPTStatusDHWC.to_knx({"dhw_push_active": True}) == DPTArray((0x00, 0x08))

    @pytest.mark.parametrize(
        "data",
        [
            {"fault": "a"},
            {"fault": None},
            {"solar_energy_only": 2},
            "fault",
        ],
    )
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            StatusDHWC.from_dict(data)
        with pytest.raises(ConversionError):
            DPTStatusDHWC.to_knx(data)

    def test_to_knx_wrong_value(self) -> None:
        """Test serializing a field with a wrong value."""
        with pytest.raises(ConversionError):
            DPTStatusDHWC.to_knx(StatusDHWC(fault="a"))  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "payload",
        [DPTArray((0x00,)), DPTArray((0x00, 0x00, 0x00)), DPTBinary(1)],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing DPTStatusDHWC with a wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTStatusDHWC.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema of DPTStatusDHWC."""
        assert DPTStatusDHWC.get_dict_schema() == [
            {"name": name, "type": "boolean", "required": False, "default": False}
            for name in DHWC_FIELDS
        ]

    def test_lookup(self) -> None:
        """Test lookup of DPTStatusDHWC."""
        assert DPTBase.parse_transcoder("22.100") is DPTStatusDHWC
        assert DPTBase.parse_transcoder("status_dhwc") is DPTStatusDHWC


class TestDPTStatusRHCC:
    """Test class for KNX DPTStatusRHCC objects."""

    @pytest.mark.parametrize(
        ("field", "raw"),
        [
            ("fault", (0x00, 0x01)),
            ("status_eco_h", (0x00, 0x02)),
            ("temp_flow_limit", (0x00, 0x04)),
            ("temp_return_limit", (0x00, 0x08)),
            ("status_morning_boost_h", (0x00, 0x10)),
            ("status_start_optim", (0x00, 0x20)),
            ("status_stop_optim", (0x00, 0x40)),
            ("heating_disabled", (0x00, 0x80)),
            ("status_eco_c", (0x02, 0x00)),
            ("status_pre_cool", (0x04, 0x00)),
            ("cooling_disabled", (0x08, 0x00)),
            ("dew_point_status", (0x10, 0x00)),
            ("frost_alarm", (0x20, 0x00)),
            ("overheat_alarm", (0x40, 0x00)),
        ],
    )
    def test_single_bit(self, field: str, raw: tuple[int, ...]) -> None:
        """Test each flag of DPTStatusRHCC (with cooling mode, bit 8 = 0)."""
        value = StatusRHCC(heat_cool_mode=HeatCool.COOL, **{field: True})
        assert DPTStatusRHCC.to_knx(value) == DPTArray(raw)
        assert DPTStatusRHCC.from_knx(DPTArray(raw)) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (StatusRHCC(), (0x01, 0x00)),  # default: heating
            (StatusRHCC(heat_cool_mode=HeatCool.HEAT), (0x01, 0x00)),
            (StatusRHCC(heat_cool_mode=HeatCool.COOL), (0x00, 0x00)),
            (StatusRHCC(**dict.fromkeys(RHCC_FLAGS, True)), (0x7F, 0xFF)),
            (
                StatusRHCC(
                    heat_cool_mode=HeatCool.COOL,
                    **dict.fromkeys(RHCC_FLAGS, True),
                ),
                (0x7E, 0xFF),
            ),
            (
                StatusRHCC(fault=True, frost_alarm=True),
                (0x21, 0x01),
            ),
        ],
    )
    def test_values(self, value: StatusRHCC, raw: tuple[int, ...]) -> None:
        """Test DPTStatusRHCC parsing and streaming."""
        assert DPTStatusRHCC.to_knx(value) == DPTArray(raw)
        assert DPTStatusRHCC.from_knx(DPTArray(raw)) == value

    def test_reserved_bit_ignored(self) -> None:
        """Test reserved bit 15 is ignored on receive."""
        assert DPTStatusRHCC.from_knx(DPTArray((0x80, 0x00))) == StatusRHCC(
            heat_cool_mode=HeatCool.COOL
        )

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            ({}, StatusRHCC()),
            ({"heat_cool_mode": "cool"}, StatusRHCC(heat_cool_mode=HeatCool.COOL)),
            ({"heat_cool_mode": "heat"}, StatusRHCC(heat_cool_mode=HeatCool.HEAT)),
            (
                {"heat_cool_mode": HeatCool.COOL, "overheat_alarm": True},
                StatusRHCC(heat_cool_mode=HeatCool.COOL, overheat_alarm=True),
            ),
            ({"fault": True}, StatusRHCC(fault=True)),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: StatusRHCC) -> None:
        """Test from_dict and as_dict methods."""
        assert StatusRHCC.from_dict(data) == value
        assert value.as_dict() == (
            dict.fromkeys(RHCC_FLAGS, False)
            | {"heat_cool_mode": value.heat_cool_mode.name.lower()}
            | {key: val for key, val in data.items() if key != "heat_cool_mode"}
        )

    @pytest.mark.parametrize(
        "data",
        [
            {"heat_cool_mode": "nodem"},
            {"heat_cool_mode": None},
            {"fault": "a"},
            {"dew_point_status": 2},
            "fault",
        ],
    )
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            StatusRHCC.from_dict(data)
        with pytest.raises(ConversionError):
            DPTStatusRHCC.to_knx(data)

    def test_to_knx_wrong_value(self) -> None:
        """Test serializing fields with a wrong value."""
        with pytest.raises(ConversionError):
            DPTStatusRHCC.to_knx(StatusRHCC(fault="a"))  # type: ignore[arg-type]
        with pytest.raises(ConversionError):
            DPTStatusRHCC.to_knx(StatusRHCC(heat_cool_mode="a"))  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "payload",
        [DPTArray((0x00,)), DPTArray((0x00, 0x00, 0x00)), DPTBinary(1)],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing DPTStatusRHCC with a wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTStatusRHCC.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema of DPTStatusRHCC."""
        boolean = {"type": "boolean", "required": False, "default": False}
        assert DPTStatusRHCC.get_dict_schema() == [
            *({"name": name} | boolean for name in RHCC_FLAGS[:8]),
            {
                "name": "heat_cool_mode",
                "type": "enum",
                "required": False,
                "default": "heat",
                "options": ["cool", "heat"],
            },
            *({"name": name} | boolean for name in RHCC_FLAGS[8:]),
        ]

    def test_lookup(self) -> None:
        """Test lookup of DPTStatusRHCC."""
        assert DPTBase.parse_transcoder("22.101") is DPTStatusRHCC
        assert DPTBase.parse_transcoder("status_rhcc") is DPTStatusRHCC


class TestDPTMedia:
    """Test class for KNX DPTMedia objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (Media(), (0x00, 0x00)),
            (Media(tp1=True), (0x00, 0x02)),
            (Media(pl110=True), (0x00, 0x04)),
            (Media(rf=True), (0x00, 0x10)),
            (Media(knx_ip=True), (0x00, 0x20)),
            (Media(tp1=True, rf=True, knx_ip=True), (0x00, 0x32)),
            (Media(tp1=True, pl110=True, rf=True, knx_ip=True), (0x00, 0x36)),
        ],
    )
    def test_values(self, value: Media, raw: tuple[int, ...]) -> None:
        """Test DPTMedia parsing and streaming."""
        assert DPTMedia.to_knx(value) == DPTArray(raw)
        assert DPTMedia.from_knx(DPTArray(raw)) == value

    def test_reserved_bits_ignored(self) -> None:
        """Test reserved bits 0, 3 and 6..15 are ignored on receive."""
        assert DPTMedia.from_knx(DPTArray((0xFF, 0xC9))) == Media()
        assert DPTMedia.from_knx(DPTArray((0xFF, 0xFF))) == Media(
            tp1=True, pl110=True, rf=True, knx_ip=True
        )

    def test_dict(self) -> None:
        """Test from_dict and as_dict methods."""
        assert Media.from_dict({"tp1": True, "knx_ip": True}) == Media(
            tp1=True, knx_ip=True
        )
        assert Media(rf=True).as_dict() == {
            "tp1": False,
            "pl110": False,
            "rf": True,
            "knx_ip": False,
        }
        assert DPTMedia.to_knx({"pl110": True}) == DPTArray((0x00, 0x04))

    @pytest.mark.parametrize("data", [{"tp1": "yes"}, {"rf": None}, 5])
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            Media.from_dict(data)
        with pytest.raises(ConversionError):
            DPTMedia.to_knx(data)

    @pytest.mark.parametrize(
        "payload",
        [DPTArray((0x00,)), DPTArray((0x00, 0x00, 0x00)), DPTBinary(1)],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing DPTMedia with a wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTMedia.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema of DPTMedia."""
        assert DPTMedia.get_dict_schema() == [
            {"name": name, "type": "boolean", "required": False, "default": False}
            for name in MEDIA_FIELDS
        ]

    def test_lookup(self) -> None:
        """Test lookup of DPTMedia."""
        assert DPTBase.parse_transcoder("22.1000") is DPTMedia
        assert DPTBase.parse_transcoder("media") is DPTMedia


class TestDPTChannelActivation16:
    """Test class for KNX DPTChannelActivation16 objects."""

    @pytest.mark.parametrize(
        ("field", "channel"), [(name, n) for n, name in enumerate(CHANNEL_FIELDS, 1)]
    )
    def test_single_channel(self, field: str, channel: int) -> None:
        """Test each channel of DPTChannelActivation16 (channel n is bit n-1)."""
        bit = 1 << (channel - 1)
        raw = (bit >> 8, bit & 0xFF)
        value = ChannelActivation16(**{field: True})
        assert DPTChannelActivation16.to_knx(value) == DPTArray(raw)
        assert DPTChannelActivation16.from_knx(DPTArray(raw)) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (ChannelActivation16(), (0x00, 0x00)),
            (ChannelActivation16(channel_1=True), (0x00, 0x01)),
            (ChannelActivation16(channel_9=True), (0x01, 0x00)),
            (ChannelActivation16(channel_16=True), (0x80, 0x00)),
            (
                ChannelActivation16(channel_1=True, channel_8=True, channel_16=True),
                (0x80, 0x81),
            ),
            (
                ChannelActivation16(**dict.fromkeys(CHANNEL_FIELDS, True)),
                (0xFF, 0xFF),
            ),
        ],
    )
    def test_values(self, value: ChannelActivation16, raw: tuple[int, ...]) -> None:
        """Test DPTChannelActivation16 parsing and streaming."""
        assert DPTChannelActivation16.to_knx(value) == DPTArray(raw)
        assert DPTChannelActivation16.from_knx(DPTArray(raw)) == value

    def test_dict(self) -> None:
        """Test from_dict and as_dict methods."""
        assert ChannelActivation16.from_dict(
            {"channel_2": True, "channel_15": True}
        ) == ChannelActivation16(channel_2=True, channel_15=True)
        assert ChannelActivation16(channel_3=True).as_dict() == dict.fromkeys(
            CHANNEL_FIELDS, False
        ) | {"channel_3": True}
        assert DPTChannelActivation16.to_knx({"channel_10": True}) == DPTArray(
            (0x02, 0x00)
        )

    @pytest.mark.parametrize("data", [{"channel_1": "on"}, {"channel_16": 3}, None])
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            ChannelActivation16.from_dict(data)
        with pytest.raises(ConversionError):
            DPTChannelActivation16.to_knx(data)

    @pytest.mark.parametrize(
        "payload",
        [DPTArray((0x00,)), DPTArray((0x00, 0x00, 0x00)), DPTBinary(1)],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing DPTChannelActivation16 with a wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTChannelActivation16.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema of DPTChannelActivation16."""
        assert DPTChannelActivation16.get_dict_schema() == [
            {"name": name, "type": "boolean", "required": False, "default": False}
            for name in CHANNEL_FIELDS
        ]

    def test_lookup(self) -> None:
        """Test lookup of DPTChannelActivation16."""
        assert DPTBase.parse_transcoder("22.1010") is DPTChannelActivation16
        assert DPTBase.parse_transcoder("channel_activation_16") is (
            DPTChannelActivation16
        )
