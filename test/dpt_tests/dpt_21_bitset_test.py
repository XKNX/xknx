"""Unit test for KNX DPT 21 8-bit set objects."""

from __future__ import annotations

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt import DPTComplex
from xknx.dpt.dpt_21 import (
    ChannelActivation8,
    DeviceControl,
    DPTChannelActivation8,
    DPTDeviceControl,
    DPTForceSign,
    DPTForceSignCool,
    DPTFuelTypeSet,
    DPTLightActuatorErrorInfo,
    DPTPhasesStatus,
    DPTRFFilterInfo,
    DPTRFModeInfo,
    DPTSecurityReport,
    DPTStatusAHU,
    DPTStatusGen,
    DPTStatusRCC,
    DPTStatusRHC,
    DPTStatusSDHWC,
    DPTVirtualDryContact,
    FuelTypeSet,
    GeneralStatus,
    PhasesStatus,
    RFModeInfo,
    SecurityReport,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram

# transcoder, sub number, value_type, field names ordered by bit number (b0 first)
BITSETS: list[tuple[type[DPTComplex[Any]], int, str, tuple[str, ...]]] = [
    (
        DPTStatusGen,
        1,
        "general_status",
        ("out_of_service", "fault", "overridden", "in_alarm", "alarm_un_ack"),
    ),
    (
        DPTDeviceControl,
        2,
        "device_control",
        ("user_stopped", "own_ia", "verify_mode"),
    ),
    (
        DPTForceSign,
        100,
        "forcing_signal",
        (
            "force_request",
            "protection",
            "oversupply",
            "overrun",
            "dhw_norm",
            "dhw_legio",
            "room_h_comf",
            "room_h_max",
        ),
    ),
    (DPTForceSignCool, 101, "forcing_signal_cool", ("force_request",)),
    (
        DPTStatusRHC,
        102,
        "room_heating_controller_status",
        (
            "fault",
            "status_eco",
            "temp_flow_limit",
            "temp_return_limit",
            "status_morning_boost",
            "status_start_optim",
            "status_stop_optim",
            "summer_mode",
        ),
    ),
    (
        DPTStatusSDHWC,
        103,
        "solar_dhw_controller_status",
        ("fault", "sdhw_load_active", "solar_load_sufficient"),
    ),
    (DPTFuelTypeSet, 104, "fuel_type_set", ("oil", "gas", "solid_state")),
    (DPTStatusRCC, 105, "room_cooling_controller_status", ("fault",)),
    (
        DPTStatusAHU,
        106,
        "ventilation_controller_status",
        ("fault", "fan_active", "heat", "cool"),
    ),
    (
        DPTLightActuatorErrorInfo,
        601,
        "light_actuator_error_info",
        (
            "load_detection_error",
            "undervoltage",
            "overcurrent",
            "underload",
            "defective_load",
            "lamp_failure",
            "overheat",
        ),
    ),
    (
        DPTRFModeInfo,
        1000,
        "rf_mode_info",
        ("asynchronous", "bibat_master", "bibat_slave"),
    ),
    (DPTRFFilterInfo, 1001, "rf_filter_info", ("doa", "knx_sn", "doa_and_knx_sn")),
    (DPTSecurityReport, 1002, "security_report", ("security_failure",)),
    (
        DPTChannelActivation8,
        1010,
        "channel_activation_8",
        tuple(f"channel_{n}" for n in range(1, 9)),
    ),
    (
        DPTVirtualDryContact,
        1200,
        "virtual_dry_contact",
        tuple(f"contact_{n}" for n in range(1, 9)),
    ),
    (DPTPhasesStatus, 1201, "phases_status", ("phase_1", "phase_2", "phase_3")),
]

BIT_CASES = [
    pytest.param(transcoder, bit, name, id=f"{transcoder.__name__}-{name}")
    for transcoder, _, _, names in BITSETS
    for bit, name in enumerate(names)
]


def _all_false(transcoder: type[DPTComplex[Any]]) -> dict[str, bool]:
    names = next(names for cls, _, _, names in BITSETS if cls is transcoder)
    return dict.fromkeys(names, False)


@pytest.mark.parametrize(
    ("transcoder", "sub", "value_type", "names"),
    BITSETS,
    ids=[entry[0].__name__ for entry in BITSETS],
)
class TestDPT21Common:
    """Tests shared by all DPT 21 transcoders."""

    def test_lookup(
        self,
        transcoder: type[DPTComplex[Any]],
        sub: int,
        value_type: str,
        names: tuple[str, ...],
    ) -> None:
        """Test lookup by DPT number and value_type."""
        assert transcoder.dpt_main_number == 21
        assert transcoder.dpt_sub_number == sub
        assert DPTBase.parse_transcoder(f"21.{sub:03}") is transcoder
        assert DPTBase.parse_transcoder({"main": 21, "sub": sub}) is transcoder
        assert DPTBase.parse_transcoder(value_type) is transcoder

    def test_fields(
        self,
        transcoder: type[DPTComplex[Any]],
        sub: int,
        value_type: str,
        names: tuple[str, ...],
    ) -> None:
        """Test field order and dict schema."""
        assert tuple(transcoder.data_type().as_dict()) == names
        schema = transcoder.get_dict_schema()
        assert [entry["name"] for entry in schema] == list(names)
        for entry in schema:
            assert entry["type"] == "boolean"
            assert entry["required"] is False

    def test_all_bits(
        self,
        transcoder: type[DPTComplex[Any]],
        sub: int,
        value_type: str,
        names: tuple[str, ...],
    ) -> None:
        """Test all defined bits set and reserved bits."""
        all_set = transcoder.data_type.from_dict(dict.fromkeys(names, True))
        raw = (1 << len(names)) - 1
        assert transcoder.to_knx(all_set) == DPTArray(raw)
        assert transcoder.from_knx(DPTArray(raw)) == all_set
        # reserved bits are ignored on receive
        assert transcoder.from_knx(DPTArray(0xFF)) == all_set
        assert transcoder.from_knx(DPTArray(0xFF & ~raw)) == (
            transcoder.data_type.from_dict(dict.fromkeys(names, False))
        )

    def test_round_trip(
        self,
        transcoder: type[DPTComplex[Any]],
        sub: int,
        value_type: str,
        names: tuple[str, ...],
    ) -> None:
        """Test every raw value of the defined bits."""
        for raw in range(1 << len(names)):
            value = transcoder.from_knx(DPTArray(raw))
            assert transcoder.to_knx(value) == DPTArray(raw)
            assert transcoder.to_knx(value.as_dict()) == DPTArray(raw)

    def test_from_knx_wrong_payload(
        self,
        transcoder: type[DPTComplex[Any]],
        sub: int,
        value_type: str,
        names: tuple[str, ...],
    ) -> None:
        """Test parsing of wrong payloads."""
        with pytest.raises(CouldNotParseTelegram):
            transcoder.from_knx(DPTArray((0x01, 0x00)))
        with pytest.raises(CouldNotParseTelegram):
            transcoder.from_knx(DPTArray(()))
        with pytest.raises(CouldNotParseTelegram):
            transcoder.from_knx(DPTBinary(1))

    def test_to_knx_invalid(
        self,
        transcoder: type[DPTComplex[Any]],
        sub: int,
        value_type: str,
        names: tuple[str, ...],
    ) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            transcoder.to_knx({names[0]: 2})
        with pytest.raises(ConversionError):
            transcoder.to_knx({names[0]: "true"})
        with pytest.raises(ConversionError):
            transcoder.to_knx(1)  # type: ignore[arg-type]
        with pytest.raises(ConversionError):
            transcoder.to_knx(transcoder.data_type(**{names[0]: 2}))

    def test_dict_values(
        self,
        transcoder: type[DPTComplex[Any]],
        sub: int,
        value_type: str,
        names: tuple[str, ...],
    ) -> None:
        """Test from_dict accepts 0 and 1 and ignores unknown keys."""
        data_type = transcoder.data_type
        assert data_type.from_dict({names[-1]: 1}) == data_type.from_dict(
            {names[-1]: True}
        )
        assert data_type.from_dict({names[-1]: 0}) == data_type.from_dict(
            {names[-1]: False}
        )
        assert data_type.from_dict({names[-1]: 1}).as_dict()[names[-1]] is True
        assert data_type.from_dict({"unknown": True}) == data_type()
        assert transcoder.to_knx({"unknown": True}) == transcoder.to_knx(data_type())

    def test_dict_invalid(
        self,
        transcoder: type[DPTComplex[Any]],
        sub: int,
        value_type: str,
        names: tuple[str, ...],
    ) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            transcoder.data_type.from_dict({names[0]: None})
        with pytest.raises(ValueError):
            transcoder.data_type.from_dict({names[0]: 1.0})
        with pytest.raises(ValueError):
            transcoder.data_type.from_dict([names[0]])  # type: ignore[arg-type]


@pytest.mark.parametrize(("transcoder", "bit", "name"), BIT_CASES)
def test_single_bit(transcoder: type[DPTComplex[Any]], bit: int, name: str) -> None:
    """Test every bit maps to its field."""
    value = transcoder.data_type.from_dict({name: True})
    expected = _all_false(transcoder) | {name: True}
    if transcoder is DPTRFModeInfo and name != "asynchronous":
        # asynchronous defaults to True
        expected["asynchronous"] = True
        raw = 1 << bit | 0x01
    else:
        raw = 1 << bit
    assert value.as_dict() == expected
    assert transcoder.to_knx(value) == DPTArray(raw)
    assert transcoder.from_knx(DPTArray(raw)) == value


class TestDPT21Specific:
    """Tests for single DPT 21 transcoders."""

    def test_general_status(self) -> None:
        """Test DPT 21.001 bit layout."""
        assert DPTStatusGen.to_knx(GeneralStatus(fault=True)) == DPTArray(0x02)
        assert DPTStatusGen.from_knx(DPTArray(0x18)) == GeneralStatus(
            in_alarm=True, alarm_un_ack=True
        )
        assert DPTStatusGen.from_knx(DPTArray(0xE0)) == GeneralStatus()

    def test_device_control(self) -> None:
        """Test DPT 21.002 bit layout."""
        assert DPTDeviceControl.to_knx(DeviceControl(verify_mode=True)) == DPTArray(
            0x04
        )
        assert DPTDeviceControl.from_knx(DPTArray(0x03)) == DeviceControl(
            user_stopped=True, own_ia=True
        )

    def test_fuel_type_set(self) -> None:
        """Test DPT 21.104 bit layout."""
        assert DPTFuelTypeSet.to_knx(FuelTypeSet(oil=True, gas=True)) == DPTArray(0x03)
        assert DPTFuelTypeSet.from_knx(DPTArray(0x04)) == FuelTypeSet(solid_state=True)

    def test_rf_mode_info(self) -> None:
        """Test DPT 21.1000 defaults and bit layout."""
        assert RFModeInfo() == RFModeInfo(
            asynchronous=True, bibat_master=False, bibat_slave=False
        )
        assert DPTRFModeInfo.to_knx(RFModeInfo()) == DPTArray(0x01)
        assert DPTRFModeInfo.to_knx({}) == DPTArray(0x01)
        assert DPTRFModeInfo.to_knx({"bibat_master": True}) == DPTArray(0x03)
        # 0 is not allowed for asynchronous but still decoded
        assert DPTRFModeInfo.from_knx(DPTArray(0x04)) == RFModeInfo(
            asynchronous=False, bibat_slave=True
        )
        assert DPTRFModeInfo.get_dict_schema()[0] == {
            "name": "asynchronous",
            "type": "boolean",
            "required": False,
            "default": True,
        }

    def test_security_report(self) -> None:
        """Test DPT 21.1002 bit layout."""
        assert DPTSecurityReport.to_knx(SecurityReport(True)) == DPTArray(0x01)
        assert DPTSecurityReport.from_knx(DPTArray(0x00)) == SecurityReport(False)
        assert DPTSecurityReport.from_knx(DPTArray(0xFE)) == SecurityReport(False)

    def test_channel_activation_8(self) -> None:
        """Test DPT 21.1010 bit n is channel n+1."""
        assert DPTChannelActivation8.to_knx(
            ChannelActivation8(channel_1=True, channel_8=True)
        ) == DPTArray(0x81)
        assert DPTChannelActivation8.from_knx(DPTArray(0x02)) == ChannelActivation8(
            channel_2=True
        )

    def test_phases_status(self) -> None:
        """Test DPT 21.1201 bit layout."""
        assert DPTPhasesStatus.to_knx(PhasesStatus(phase_3=True)) == DPTArray(0x04)
        assert DPTPhasesStatus.from_knx(DPTArray(0xF8)) == PhasesStatus()

    def test_dict(self) -> None:
        """Test from_dict and as_dict."""
        value = GeneralStatus(out_of_service=True, overridden=True)
        assert value.as_dict() == {
            "out_of_service": True,
            "fault": False,
            "overridden": True,
            "in_alarm": False,
            "alarm_un_ack": False,
        }
        assert GeneralStatus.from_dict(value.as_dict()) == value
        assert GeneralStatus.from_dict(
            {"overridden": True, "out_of_service": True}
        ) == (value)
        assert GeneralStatus.from_dict({}) == GeneralStatus()
