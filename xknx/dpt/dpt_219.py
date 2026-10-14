"""Implementation of the KNX 219 data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..exceptions import ConversionError
from .dpt import DPTComplex, DPTComplexData, DPTEnumData
from .helpers.metadata import RANGE_UINT8
from .payload import DPTArray, DPTBinary

_PRIORITY_VOID = 0x03


class AlarmPriority(DPTEnumData):
    """Alarm priority according to DPT_Priority (20.004); 0 is the highest priority."""

    HIGH = 0
    MEDIUM = 1
    LOW = 2


class ApplicationArea(DPTEnumData):
    """
    Application area of an alarm according to DPT_ApplicationArea (20.006).

    The codes correspond to the numbering of the parts in Volume 7 of the KNX
    Standard; other values are reserved.
    """

    NO_FAULT = 0
    SYSTEM_AND_FUNCTIONS_OF_COMMON_INTEREST = 1
    HVAC_GENERAL_FBS = 10
    HVAC_HOT_WATER_HEATING = 11
    HVAC_DIRECT_ELECTRICAL_HEATING = 12
    HVAC_TERMINAL_UNITS = 13
    HVAC_VAC = 14
    LIGHTING = 20
    SECURITY = 30
    LOAD_MANAGEMENT = 40
    SHUTTERS_AND_BLINDS = 50


class AlarmErrorClassSystem(DPTEnumData):
    """
    Error class of an alarm in the application area 'system'.

    Encoding of DPT_ErrorClass_System (20.011), which is the encoding used in
    the FB Technical Alarm; values 19 to 255 are reserved.
    """

    NO_FAULT = 0
    GENERAL_DEVICE_FAULT = 1
    COMMUNICATION_FAULT = 2
    CONFIGURATION_FAULT = 3
    HARDWARE_FAULT = 4
    SOFTWARE_FAULT = 5
    INSUFFICIENT_NON_VOLATILE_MEMORY = 6
    INSUFFICIENT_VOLATILE_MEMORY = 7
    MEMORY_ALLOCATION_COMMAND_WITH_SIZE_0_RECEIVED = 8
    CRC_ERROR = 9
    WATCHDOG_RESET_DETECTED = 10
    INVALID_OPCODE_DETECTED = 11
    GENERAL_PROTECTION_FAULT = 12
    MAXIMAL_TABLE_LENGTH_EXCEEDED = 13
    UNDEFINED_LOAD_COMMAND_RECEIVED = 14
    GROUP_ADDRESS_TABLE_IS_NOT_SORTED = 15
    INVALID_CONNECTION_NUMBER = 16
    INVALID_GROUP_OBJECT_NUMBER = 17
    GROUP_OBJECT_TYPE_EXCEEDS_MAX_APDU_LENGTH = 18


class AlarmErrorClassHVAC(DPTEnumData):
    """
    Error class of an alarm in the HVAC application areas.

    Encoding of DPT_ErrorClass_HVAC (20.012), which is the encoding used in
    the FB Technical Alarm; values 5 to 255 are reserved.
    """

    NO_FAULT = 0
    SENSOR_FAULT = 1
    PROCESS_FAULT_CONTROLLER_FAULT = 2
    ACTUATOR_FAULT = 3
    OTHER_FAULT = 4


_HVAC_AREAS = frozenset(
    (
        ApplicationArea.HVAC_GENERAL_FBS,
        ApplicationArea.HVAC_HOT_WATER_HEATING,
        ApplicationArea.HVAC_DIRECT_ELECTRICAL_HEATING,
        ApplicationArea.HVAC_TERMINAL_UNITS,
        ApplicationArea.HVAC_VAC,
    )
)
_ATTRIBUTE_BITS = ("ack_sup", "time_stamp_sup", "alarm_text_sup", "error_code_sup")
_STATUS_BITS = ("in_alarm", "alarm_un_ack", "locked")


@dataclass(slots=True)
class AlarmInfo(DPTComplexData):
    """
    Representation of an alarm information.

    `log_number`: int 0..255
    `alarm_priority`: AlarmPriority; None for 'no priority' (void)
    `application_area`: ApplicationArea
    `error_class`: int 0..255; its meaning depends on `application_area`,
        see `error_class_enum`
    `ack_sup`, `time_stamp_sup`, `alarm_text_sup`, `error_code_sup`: bool
        attributes - the alarm supports acknowledge, time stamp, alarm text
        and error code
    `in_alarm`, `alarm_un_ack`, `locked`: bool alarm status attributes
    """

    log_number: int = field(metadata=RANGE_UINT8)
    alarm_priority: AlarmPriority | None
    application_area: ApplicationArea
    error_class: int = field(metadata=RANGE_UINT8)
    ack_sup: bool = False
    time_stamp_sup: bool = False
    alarm_text_sup: bool = False
    error_code_sup: bool = False
    in_alarm: bool = False
    alarm_un_ack: bool = False
    locked: bool = False

    @property
    def error_class_enum(self) -> AlarmErrorClassSystem | AlarmErrorClassHVAC | None:
        """
        Return the error class as Enum of its application area.

        Error classes are standardised for the application areas 'system' and
        HVAC only. None for other application areas and for reserved codes.
        """
        try:
            if self.application_area is (
                ApplicationArea.SYSTEM_AND_FUNCTIONS_OF_COMMON_INTEREST
            ):
                return AlarmErrorClassSystem(self.error_class)
            if self.application_area in _HVAC_AREAS:
                return AlarmErrorClassHVAC(self.error_class)
        except ValueError:
            pass
        return None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AlarmInfo:
        """Init from a dictionary."""
        try:
            log_number = int(data["log_number"])
            _priority = data.get("alarm_priority")
            alarm_priority = (
                AlarmPriority.parse(_priority) if _priority is not None else None
            )
            application_area = ApplicationArea.parse(data["application_area"])
            error_class = int(data["error_class"])
        except KeyError as err:
            raise ValueError(f"Missing required key: {err}") from err
        except (AttributeError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for AlarmInfo: {err}") from err
        bits: dict[str, bool] = {}
        for name in _ATTRIBUTE_BITS + _STATUS_BITS:
            bit = data.get(name, False)
            if not isinstance(bit, bool):
                raise ValueError(f"Invalid value for {name}: {bit!r}")
            bits[name] = bit
        return cls(
            log_number=log_number,
            alarm_priority=alarm_priority,
            application_area=application_area,
            error_class=error_class,
            ack_sup=bits["ack_sup"],
            time_stamp_sup=bits["time_stamp_sup"],
            alarm_text_sup=bits["alarm_text_sup"],
            error_code_sup=bits["error_code_sup"],
            in_alarm=bits["in_alarm"],
            alarm_un_ack=bits["alarm_un_ack"],
            locked=bits["locked"],
        )

    def as_dict(self) -> dict[str, int | str | bool | None]:
        """Create a JSON serializable dictionary."""
        return {
            "log_number": self.log_number,
            "alarm_priority": (
                self.alarm_priority.name.lower()
                if self.alarm_priority is not None
                else None
            ),
            "application_area": self.application_area.name.lower(),
            "error_class": self.error_class,
            "ack_sup": self.ack_sup,
            "time_stamp_sup": self.time_stamp_sup,
            "alarm_text_sup": self.alarm_text_sup,
            "error_code_sup": self.error_code_sup,
            "in_alarm": self.in_alarm,
            "alarm_un_ack": self.alarm_un_ack,
            "locked": self.locked,
        }


class DPTAlarmInfo(DPTComplex[AlarmInfo]):
    """
    Abstraction for KNX 6 octet alarm information (DPT 219.001).

    DPT_AlarmInfo - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.29
    """

    data_type = AlarmInfo
    payload_type = DPTArray
    payload_length = 6
    dpt_main_number = 219
    dpt_sub_number = 1
    value_type = "alarm_info"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> AlarmInfo:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        try:
            alarm_priority = AlarmPriority(raw[1]) if raw[1] != _PRIORITY_VOID else None
            application_area = ApplicationArea(raw[2])
        except ValueError:
            raise ConversionError(
                f"Payload not supported for {cls.dpt_name()}", raw=raw
            ) from None
        attributes = raw[4]  # reserved bits 4..7 are ignored
        status = raw[5]  # reserved bits 3..7 are ignored
        return AlarmInfo(
            log_number=raw[0],
            alarm_priority=alarm_priority,
            application_area=application_area,
            error_class=raw[3],
            ack_sup=bool(attributes & 0x01),
            time_stamp_sup=bool(attributes & 0x02),
            alarm_text_sup=bool(attributes & 0x04),
            error_code_sup=bool(attributes & 0x08),
            in_alarm=bool(status & 0x01),
            alarm_un_ack=bool(status & 0x02),
            locked=bool(status & 0x04),
        )

    @classmethod
    def _to_knx(cls, value: AlarmInfo) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        for name, number in (
            ("log_number", value.log_number),
            ("error_class", value.error_class),
        ):
            if not isinstance(number, int) or not 0 <= number <= 255:
                raise ConversionError(
                    f"{name} out of range 0..255 for {cls.dpt_name()}", value=value
                )
        if not isinstance(value.application_area, ApplicationArea) or not (
            value.alarm_priority is None
            or isinstance(value.alarm_priority, AlarmPriority)
        ):
            raise ConversionError(
                f"Invalid application area or alarm priority for {cls.dpt_name()}",
                value=value,
            )
        attributes = (
            bool(value.error_code_sup) << 3
            | bool(value.alarm_text_sup) << 2
            | bool(value.time_stamp_sup) << 1
            | bool(value.ack_sup)
        )
        status = (
            bool(value.locked) << 2
            | bool(value.alarm_un_ack) << 1
            | bool(value.in_alarm)
        )
        return DPTArray(
            (
                value.log_number,
                (
                    value.alarm_priority.value
                    if value.alarm_priority is not None
                    else _PRIORITY_VOID
                ),
                value.application_area.value,
                value.error_class,
                attributes,
                status,
            )
        )
