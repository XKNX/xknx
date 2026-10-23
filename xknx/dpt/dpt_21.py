"""
Implementation of the KNX 8-bit set data point types (DPT 21.xxx).

KNX v02.02.01 - Datapoint Types 03.07.02
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from ..exceptions import ConversionError
from .dpt import DPTComplex
from .helpers.bitset import _BitsetData
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class GeneralStatus(_BitsetData):
    """Value of DPT 21.001 DPT_StatusGen."""

    out_of_service: bool = False
    fault: bool = False
    overridden: bool = False
    in_alarm: bool = False
    alarm_un_ack: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "out_of_service": 0,
        "fault": 1,
        "overridden": 2,
        "in_alarm": 3,
        "alarm_un_ack": 4,
    }


class DPTStatusGen(DPTComplex[GeneralStatus]):
    """
    Abstraction for KNX 1 octet General Status (DPT 21.001 DPT_StatusGen).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.22.1
    """

    data_type = GeneralStatus
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 1
    value_type = "general_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> GeneralStatus:
        """Parse/deserialize from KNX/IP raw data."""
        return GeneralStatus.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: GeneralStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class DeviceControl(_BitsetData):
    """Value of DPT 21.002 DPT_Device_Control."""

    user_stopped: bool = False
    own_ia: bool = False
    verify_mode: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "user_stopped": 0,
        "own_ia": 1,
        "verify_mode": 2,
    }


class DPTDeviceControl(DPTComplex[DeviceControl]):
    """
    Abstraction for KNX 1 octet Device Control (DPT 21.002 DPT_Device_Control).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.22.2
    """

    data_type = DeviceControl
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 2
    value_type = "device_control"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> DeviceControl:
        """Parse/deserialize from KNX/IP raw data."""
        return DeviceControl.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: DeviceControl) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class ForcingSignal(_BitsetData):
    """Value of DPT 21.100 DPT_ForceSign."""

    force_request: bool = False
    protection: bool = False
    oversupply: bool = False
    overrun: bool = False
    dhw_norm: bool = False
    dhw_legio: bool = False
    room_h_comf: bool = False
    room_h_max: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "force_request": 0,
        "protection": 1,
        "oversupply": 2,
        "overrun": 3,
        "dhw_norm": 4,
        "dhw_legio": 5,
        "room_h_comf": 6,
        "room_h_max": 7,
    }


class DPTForceSign(DPTComplex[ForcingSignal]):
    """
    Abstraction for KNX 1 octet Forcing Signal (DPT 21.100 DPT_ForceSign).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.4.1
    """

    data_type = ForcingSignal
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 100
    value_type = "forcing_signal"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ForcingSignal:
        """Parse/deserialize from KNX/IP raw data."""
        return ForcingSignal.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: ForcingSignal) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class ForcingSignalCool(_BitsetData):
    """Value of DPT 21.101 DPT_ForceSignCool."""

    force_request: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "force_request": 0,
    }


class DPTForceSignCool(DPTComplex[ForcingSignalCool]):
    """
    Abstraction for KNX 1 octet Forcing Signal Cool (DPT 21.101 DPT_ForceSignCool).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.4.2
    """

    data_type = ForcingSignalCool
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 101
    value_type = "forcing_signal_cool"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ForcingSignalCool:
        """Parse/deserialize from KNX/IP raw data."""
        return ForcingSignalCool.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: ForcingSignalCool) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class RoomHeatingControllerStatus(_BitsetData):
    """Value of DPT 21.102 DPT_StatusRHC."""

    fault: bool = False
    status_eco: bool = False
    temp_flow_limit: bool = False
    temp_return_limit: bool = False
    status_morning_boost: bool = False
    status_start_optim: bool = False
    status_stop_optim: bool = False
    summer_mode: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "fault": 0,
        "status_eco": 1,
        "temp_flow_limit": 2,
        "temp_return_limit": 3,
        "status_morning_boost": 4,
        "status_start_optim": 5,
        "status_stop_optim": 6,
        "summer_mode": 7,
    }


class DPTStatusRHC(DPTComplex[RoomHeatingControllerStatus]):
    """
    Abstraction for KNX 1 octet Room Heating Controller Status (DPT 21.102 DPT_StatusRHC).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.4.3
    """

    data_type = RoomHeatingControllerStatus
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 102
    value_type = "room_heating_controller_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RoomHeatingControllerStatus:
        """Parse/deserialize from KNX/IP raw data."""
        return RoomHeatingControllerStatus.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: RoomHeatingControllerStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class SolarDHWControllerStatus(_BitsetData):
    """Value of DPT 21.103 DPT_StatusSDHWC."""

    fault: bool = False
    sdhw_load_active: bool = False
    solar_load_sufficient: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "fault": 0,
        "sdhw_load_active": 1,
        "solar_load_sufficient": 2,
    }


class DPTStatusSDHWC(DPTComplex[SolarDHWControllerStatus]):
    """
    Abstraction for KNX 1 octet Solar DHW Controller Status (DPT 21.103 DPT_StatusSDHWC).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.4.4
    """

    data_type = SolarDHWControllerStatus
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 103
    value_type = "solar_dhw_controller_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> SolarDHWControllerStatus:
        """Parse/deserialize from KNX/IP raw data."""
        return SolarDHWControllerStatus.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: SolarDHWControllerStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class FuelTypeSet(_BitsetData):
    """Value of DPT 21.104 DPT_FuelTypeSet."""

    oil: bool = False
    gas: bool = False
    solid_state: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "oil": 0,
        "gas": 1,
        "solid_state": 2,
    }


class DPTFuelTypeSet(DPTComplex[FuelTypeSet]):
    """
    Abstraction for KNX 1 octet Fuel Type Set (DPT 21.104 DPT_FuelTypeSet).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.4.5
    """

    data_type = FuelTypeSet
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 104
    value_type = "fuel_type_set"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> FuelTypeSet:
        """Parse/deserialize from KNX/IP raw data."""
        return FuelTypeSet.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: FuelTypeSet) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class RoomCoolingControllerStatus(_BitsetData):
    """Value of DPT 21.105 DPT_StatusRCC."""

    fault: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "fault": 0,
    }


class DPTStatusRCC(DPTComplex[RoomCoolingControllerStatus]):
    """
    Abstraction for KNX 1 octet Room Cooling Controller Status (DPT 21.105 DPT_StatusRCC).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.4.6
    """

    data_type = RoomCoolingControllerStatus
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 105
    value_type = "room_cooling_controller_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RoomCoolingControllerStatus:
        """Parse/deserialize from KNX/IP raw data."""
        return RoomCoolingControllerStatus.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: RoomCoolingControllerStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class VentilationControllerStatus(_BitsetData):
    """Value of DPT 21.106 DPT_StatusAHU."""

    fault: bool = False
    fan_active: bool = False
    heat: bool = False
    cool: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "fault": 0,
        "fan_active": 1,
        "heat": 2,
        "cool": 3,
    }


class DPTStatusAHU(DPTComplex[VentilationControllerStatus]):
    """
    Abstraction for KNX 1 octet Ventilation Controller Status (DPT 21.106 DPT_StatusAHU).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.4.7
    """

    data_type = VentilationControllerStatus
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 106
    value_type = "ventilation_controller_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> VentilationControllerStatus:
        """Parse/deserialize from KNX/IP raw data."""
        return VentilationControllerStatus.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: VentilationControllerStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class LightActuatorErrorInfo(_BitsetData):
    """Value of DPT 21.601 DPT_LightActuatorErrorInfo."""

    load_detection_error: bool = False
    undervoltage: bool = False
    overcurrent: bool = False
    underload: bool = False
    defective_load: bool = False
    lamp_failure: bool = False
    overheat: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "load_detection_error": 0,
        "undervoltage": 1,
        "overcurrent": 2,
        "underload": 3,
        "defective_load": 4,
        "lamp_failure": 5,
        "overheat": 6,
    }


class DPTLightActuatorErrorInfo(DPTComplex[LightActuatorErrorInfo]):
    """
    Abstraction for KNX 1 octet Lighting Actuator Error Information (DPT 21.601).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.4.1
    """

    data_type = LightActuatorErrorInfo
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 601
    value_type = "light_actuator_error_info"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> LightActuatorErrorInfo:
        """Parse/deserialize from KNX/IP raw data."""
        return LightActuatorErrorInfo.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: LightActuatorErrorInfo) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class RFModeInfo(_BitsetData):
    """
    Value of DPT 21.1000 DPT_RF_ModeInfo.

    `asynchronous` shall always be set ("0 = value not allowed"), hence it
    defaults to True and `False` is rejected on send. A received 0 is kept as
    `False` rather than rejected.
    """

    asynchronous: bool = True
    bibat_master: bool = False
    bibat_slave: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "asynchronous": 0,
        "bibat_master": 1,
        "bibat_slave": 2,
    }


class DPTRFModeInfo(DPTComplex[RFModeInfo]):
    """
    Abstraction for KNX 1 octet RF Communication Mode Info (DPT 21.1000 DPT_RF_ModeInfo).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.2.1
    """

    data_type = RFModeInfo
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 1000
    value_type = "rf_mode_info"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RFModeInfo:
        """Parse/deserialize from KNX/IP raw data."""
        return RFModeInfo.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: RFModeInfo) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not value.asynchronous:
            raise ConversionError(
                f"`asynchronous` = False is not allowed for {cls.dpt_name()}",
                value=value,
            )
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class RFFilterInfo(_BitsetData):
    """Value of DPT 21.1001 DPT_RF_FilterInfo."""

    doa: bool = False
    knx_sn: bool = False
    doa_and_knx_sn: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "doa": 0,
        "knx_sn": 1,
        "doa_and_knx_sn": 2,
    }


class DPTRFFilterInfo(DPTComplex[RFFilterInfo]):
    """
    Abstraction for KNX 1 octet cEMI Server Supported RF Filtering Modes (DPT 21.1001).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.2.2
    """

    data_type = RFFilterInfo
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 1001
    value_type = "rf_filter_info"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RFFilterInfo:
        """Parse/deserialize from KNX/IP raw data."""
        return RFFilterInfo.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: RFFilterInfo) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class SecurityReport(_BitsetData):
    """Value of DPT 21.1002 DPT_Security_Report."""

    security_failure: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "security_failure": 0,
    }


class DPTSecurityReport(DPTComplex[SecurityReport]):
    """
    Abstraction for KNX 1 octet Security Report (DPT 21.1002 DPT_Security_Report).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.2.3
    """

    data_type = SecurityReport
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 1002
    value_type = "security_report"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> SecurityReport:
        """Parse/deserialize from KNX/IP raw data."""
        return SecurityReport.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: SecurityReport) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class ChannelActivation8(_BitsetData):
    """
    Value of DPT 21.1010 DPT_Channel_Activation_8.

    Bit n is channel n+1, as the spec says ("bn (n = 0 to 7): Activation state
    of channel n+1"). The master data (DPST-21-1010) lists channel 1 as the most
    significant bit instead, i.e. the opposite order; the spec is followed.
    """

    channel_1: bool = False
    channel_2: bool = False
    channel_3: bool = False
    channel_4: bool = False
    channel_5: bool = False
    channel_6: bool = False
    channel_7: bool = False
    channel_8: bool = False

    _bits: ClassVar[Mapping[str, int]] = {f"channel_{bit + 1}": bit for bit in range(8)}


class DPTChannelActivation8(DPTComplex[ChannelActivation8]):
    """
    Abstraction for KNX 1 octet Channel Activation for 8 channels (DPT 21.1010).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.2.4
    """

    data_type = ChannelActivation8
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 1010
    value_type = "channel_activation_8"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ChannelActivation8:
        """Parse/deserialize from KNX/IP raw data."""
        return ChannelActivation8.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: ChannelActivation8) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class VirtualDryContact(_BitsetData):
    """
    Value of DPT 21.1200 DPT_VirtualDryContact. True = contact closed.

    The spec names the bits "bx: Status of Virtual Dry Contact X" with x = 0..7;
    the fields count the contacts from 1 instead (`contact_1` is b0).
    """

    contact_1: bool = False
    contact_2: bool = False
    contact_3: bool = False
    contact_4: bool = False
    contact_5: bool = False
    contact_6: bool = False
    contact_7: bool = False
    contact_8: bool = False

    _bits: ClassVar[Mapping[str, int]] = {f"contact_{bit + 1}": bit for bit in range(8)}


class DPTVirtualDryContact(DPTComplex[VirtualDryContact]):
    """
    Abstraction for KNX 1 octet Virtual Dry Contact status (DPT 21.1200).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §9.6
    """

    data_type = VirtualDryContact
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 1200
    value_type = "virtual_dry_contact"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> VirtualDryContact:
        """Parse/deserialize from KNX/IP raw data."""
        return VirtualDryContact.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: VirtualDryContact) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())


@dataclass(slots=True)
class PhasesStatus(_BitsetData):
    """
    Value of DPT 21.1201 DPT_Phases_Status. True = phase present.

    The spec names the bits "bx: Status of Phase X" with x = 0..2; the fields
    count the phases from 1 instead, like L1, L2 and L3 (`phase_1` is b0).
    """

    phase_1: bool = False
    phase_2: bool = False
    phase_3: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "phase_1": 0,
        "phase_2": 1,
        "phase_3": 2,
    }


class DPTPhasesStatus(DPTComplex[PhasesStatus]):
    """
    Abstraction for KNX 1 octet Phases Status (DPT 21.1201 DPT_Phases_Status).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §9.7
    """

    data_type = PhasesStatus
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 21
    dpt_sub_number = 1201
    value_type = "phases_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> PhasesStatus:
        """Parse/deserialize from KNX/IP raw data."""
        return PhasesStatus.from_raw(cls.validate_payload(payload)[0])

    @classmethod
    def _to_knx(cls, value: PhasesStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(value.to_raw())
