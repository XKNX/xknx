"""Unit test for KNX DPT 219 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTComplex
from xknx.dpt.dpt_20 import ApplicationArea, ErrorClassHVAC, ErrorClassSystem, Priority
from xknx.dpt.dpt_219 import AlarmInfo, DPTAlarmInfo
from xknx.exceptions import ConversionError, CouldNotParseTelegram

_BITS = (
    "ack_sup",
    "time_stamp_sup",
    "alarm_text_sup",
    "error_code_sup",
    "in_alarm",
    "alarm_un_ack",
    "locked",
)


def _alarm(**kwargs: Any) -> AlarmInfo:
    """Return an AlarmInfo with defaults for the required fields."""
    defaults: dict[str, Any] = {
        "log_number": 0,
        "alarm_priority": Priority.HIGH,
        "application_area": ApplicationArea.NO_FAULT,
        "error_class": 0,
    }
    return AlarmInfo(**defaults | kwargs)


class TestAlarmInfo:
    """Test AlarmInfo class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {
                    "log_number": 7,
                    "alarm_priority": "medium",
                    "application_area": "hvac_vac",
                    "error_class": 3,
                    "ack_sup": True,
                    "time_stamp_sup": False,
                    "alarm_text_sup": True,
                    "error_code_sup": False,
                    "in_alarm": True,
                    "alarm_un_ack": True,
                    "locked": False,
                },
                AlarmInfo(
                    log_number=7,
                    alarm_priority=Priority.MEDIUM,
                    application_area=ApplicationArea.HVAC_VAC,
                    error_class=3,
                    ack_sup=True,
                    alarm_text_sup=True,
                    in_alarm=True,
                    alarm_un_ack=True,
                ),
            ),
            (
                {
                    "log_number": 255,
                    "alarm_priority": None,
                    "application_area": "lighting",
                    "error_class": 200,
                    "ack_sup": False,
                    "time_stamp_sup": True,
                    "alarm_text_sup": False,
                    "error_code_sup": True,
                    "in_alarm": False,
                    "alarm_un_ack": False,
                    "locked": True,
                },
                AlarmInfo(
                    log_number=255,
                    alarm_priority=None,
                    application_area=ApplicationArea.LIGHTING,
                    error_class=200,
                    time_stamp_sup=True,
                    error_code_sup=True,
                    locked=True,
                ),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: AlarmInfo) -> None:
        """Test from_dict and as_dict methods."""
        assert AlarmInfo.from_dict(data) == value
        assert value.as_dict() == data

    def test_dict_defaults(self) -> None:
        """Test from_dict with optional keys omitted."""
        assert AlarmInfo.from_dict(
            {
                "log_number": "1",
                "application_area": 1,
                "error_class": 2,
            }
        ) == AlarmInfo(
            log_number=1,
            alarm_priority=None,
            application_area=ApplicationArea.SYSTEM_AND_FUNCTIONS_OF_COMMON_INTEREST,
            error_class=2,
        )

    def test_dict_void_priority(self) -> None:
        """Test from_dict reads the 'void' priority as no priority (None)."""
        assert (
            AlarmInfo.from_dict(
                {
                    "log_number": 0,
                    "alarm_priority": "void",
                    "application_area": "lighting",
                    "error_class": 0,
                }
            ).alarm_priority
            is None
        )

    @pytest.mark.parametrize(
        "data",
        [
            {"application_area": "lighting", "error_class": 0},
            {"log_number": 0, "error_class": 0},
            {"log_number": 0, "application_area": "lighting"},
            {"log_number": "a", "application_area": "lighting", "error_class": 0},
            {"log_number": 0, "application_area": "invalid", "error_class": 0},
            {"log_number": 0, "application_area": 2, "error_class": 0},
            {"log_number": 0, "application_area": "lighting", "error_class": None},
            {
                "log_number": 0,
                "alarm_priority": "none",
                "application_area": "lighting",
                "error_class": 0,
            },
            {
                "log_number": 0,
                "application_area": "lighting",
                "error_class": 0,
                "locked": 2,
            },
            {
                "log_number": 0,
                "application_area": "lighting",
                "error_class": 0,
                "ack_sup": "true",
            },
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid values."""
        with pytest.raises(ValueError):
            AlarmInfo.from_dict(data)

    @pytest.mark.parametrize(
        ("application_area", "error_class", "expected"),
        [
            (
                ApplicationArea.SYSTEM_AND_FUNCTIONS_OF_COMMON_INTEREST,
                3,
                ErrorClassSystem.CONFIGURATION_FAULT,
            ),
            (
                ApplicationArea.SYSTEM_AND_FUNCTIONS_OF_COMMON_INTEREST,
                18,
                ErrorClassSystem.GROUP_OBJECT_TYPE_EXCEEDS_MAX_APDU_LENGTH,
            ),
            (ApplicationArea.SYSTEM_AND_FUNCTIONS_OF_COMMON_INTEREST, 19, None),
            (ApplicationArea.HVAC_GENERAL_FBS, 1, ErrorClassHVAC.SENSOR_FAULT),
            (
                ApplicationArea.HVAC_HOT_WATER_HEATING,
                2,
                ErrorClassHVAC.PROCESS_FAULT_CONTROLLER_FAULT,
            ),
            (
                ApplicationArea.HVAC_DIRECT_ELECTRICAL_HEATING,
                3,
                ErrorClassHVAC.ACTUATOR_FAULT,
            ),
            (ApplicationArea.HVAC_TERMINAL_UNITS, 4, ErrorClassHVAC.OTHER_FAULT),
            (ApplicationArea.HVAC_VAC, 0, ErrorClassHVAC.NO_FAULT),
            (ApplicationArea.HVAC_VAC, 5, None),
            (ApplicationArea.NO_FAULT, 0, None),
            (ApplicationArea.LIGHTING, 1, None),
            (ApplicationArea.SECURITY, 1, None),
            (ApplicationArea.LOAD_MANAGEMENT, 1, None),
            (ApplicationArea.SHUTTERS_AND_BLINDS, 1, None),
        ],
    )
    def test_error_class_enum(
        self,
        application_area: ApplicationArea,
        error_class: int,
        expected: ErrorClassSystem | ErrorClassHVAC | None,
    ) -> None:
        """Test the error class Enum depending on the application area."""
        value = _alarm(application_area=application_area, error_class=error_class)
        assert value.error_class_enum is expected


class TestDPTAlarmInfo:
    """Test class for KNX DPTAlarmInfo objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (_alarm(), (0x00, 0x00, 0x00, 0x00, 0x00, 0x00)),
            (
                AlarmInfo(
                    log_number=255,
                    alarm_priority=None,
                    application_area=ApplicationArea.SHUTTERS_AND_BLINDS,
                    error_class=255,
                    ack_sup=True,
                    time_stamp_sup=True,
                    alarm_text_sup=True,
                    error_code_sup=True,
                    in_alarm=True,
                    alarm_un_ack=True,
                    locked=True,
                ),
                (0xFF, 0x03, 0x32, 0xFF, 0x0F, 0x07),
            ),
            (
                _alarm(
                    log_number=0x12,
                    alarm_priority=Priority.LOW,
                    application_area=ApplicationArea.SYSTEM_AND_FUNCTIONS_OF_COMMON_INTEREST,
                    error_class=2,
                    ack_sup=True,
                    in_alarm=True,
                    alarm_un_ack=True,
                ),
                (0x12, 0x02, 0x01, 0x02, 0x01, 0x03),
            ),
            # attribute bits
            (_alarm(ack_sup=True), (0x00, 0x00, 0x00, 0x00, 0x01, 0x00)),
            (_alarm(time_stamp_sup=True), (0x00, 0x00, 0x00, 0x00, 0x02, 0x00)),
            (_alarm(alarm_text_sup=True), (0x00, 0x00, 0x00, 0x00, 0x04, 0x00)),
            (_alarm(error_code_sup=True), (0x00, 0x00, 0x00, 0x00, 0x08, 0x00)),
            # alarm status bits
            (_alarm(in_alarm=True), (0x00, 0x00, 0x00, 0x00, 0x00, 0x01)),
            (_alarm(alarm_un_ack=True), (0x00, 0x00, 0x00, 0x00, 0x00, 0x02)),
            (_alarm(locked=True), (0x00, 0x00, 0x00, 0x00, 0x00, 0x04)),
        ],
    )
    def test_round_trip(self, value: AlarmInfo, raw: tuple[int, ...]) -> None:
        """Test DPTAlarmInfo parsing and streaming."""
        knx_value = DPTAlarmInfo.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTAlarmInfo.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        ("raw", "priority"),
        [
            (0x00, Priority.HIGH),
            (0x01, Priority.MEDIUM),
            (0x02, Priority.LOW),
            (0x03, None),
        ],
    )
    def test_alarm_priority(self, raw: int, priority: Priority | None) -> None:
        """Test every alarm priority value."""
        payload = DPTArray((0x00, raw, 0x00, 0x00, 0x00, 0x00))
        assert DPTAlarmInfo.from_knx(payload).alarm_priority is priority
        assert DPTAlarmInfo.to_knx(_alarm(alarm_priority=priority)) == payload

    @pytest.mark.parametrize("application_area", list(ApplicationArea))
    def test_application_area(self, application_area: ApplicationArea) -> None:
        """Test every application area value."""
        payload = DPTArray((0x00, 0x00, application_area.value, 0x00, 0x00, 0x00))
        assert DPTAlarmInfo.from_knx(payload).application_area is application_area
        assert DPTAlarmInfo.to_knx(_alarm(application_area=application_area)) == payload

    def test_from_knx_reserved_bits_ignored(self) -> None:
        """Test reserved bits of attributes and alarm status are ignored."""
        assert (
            DPTAlarmInfo.from_knx(DPTArray((0x00, 0x00, 0x00, 0x00, 0xF0, 0xF8)))
            == _alarm()
        )

    @pytest.mark.parametrize(
        "raw",
        [
            (0x00, 0x04, 0x00, 0x00, 0x00, 0x00),  # reserved priority
            (0x00, 0xFF, 0x00, 0x00, 0x00, 0x00),  # reserved priority
            (0x00, 0x00, 0x02, 0x00, 0x00, 0x00),  # reserved application area
            (0x00, 0x00, 0x33, 0x00, 0x00, 0x00),  # reserved application area
            (0x00, 0x00, 0xFF, 0x00, 0x00, 0x00),  # reserved application area
        ],
    )
    def test_from_knx_unsupported(self, raw: tuple[int, ...]) -> None:
        """Test DPTAlarmInfo parsing reserved enumeration values."""
        with pytest.raises(ConversionError):
            DPTAlarmInfo.from_knx(DPTArray(raw))

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                {
                    "log_number": 5,
                    "alarm_priority": "high",
                    "application_area": "security",
                    "error_class": 1,
                    "in_alarm": True,
                },
                (0x05, 0x00, 0x1E, 0x01, 0x00, 0x01),
            ),
            (
                {
                    "log_number": 0,
                    "application_area": "load_management",
                    "error_class": 0,
                },
                (0x00, 0x03, 0x28, 0x00, 0x00, 0x00),
            ),
        ],
    )
    def test_to_knx_from_dict(
        self, value: dict[str, Any], raw: tuple[int, ...]
    ) -> None:
        """Test DPTAlarmInfo serializing from a dict."""
        assert DPTAlarmInfo.to_knx(value) == DPTArray(raw)

    @pytest.mark.parametrize(
        "value",
        [
            _alarm(log_number=-1),
            _alarm(log_number=256),
            _alarm(log_number=1.5),
            _alarm(error_class=-1),
            _alarm(error_class=256),
            _alarm(error_class="a"),
            _alarm(application_area=1),
            _alarm(application_area=Priority.HIGH),
            _alarm(alarm_priority=0),
            _alarm(alarm_priority=ApplicationArea.NO_FAULT),
            {"log_number": 0, "application_area": "lighting"},
            {"log_number": 256, "application_area": "lighting", "error_class": 0},
            None,
            1,
            (0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test DPTAlarmInfo serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTAlarmInfo.to_knx(value)

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00, 0x00, 0x00, 0x00, 0x00)),
            DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)),
            DPTBinary(1),
        ],
    )
    def test_from_knx_invalid_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test DPTAlarmInfo parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTAlarmInfo.from_knx(payload)

    @pytest.mark.parametrize("value_type", ["219.001", "alarm_info"])
    def test_lookup(self, value_type: str) -> None:
        """Test transcoder lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder(value_type) is DPTAlarmInfo
        assert DPTComplex.parse_transcoder(value_type) is DPTAlarmInfo
        assert DPTBase.parse_transcoder({"main": 219, "sub": 1}) is DPTAlarmInfo

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTAlarmInfo."""
        assert DPTAlarmInfo.get_dict_schema() == [
            {
                "name": "log_number",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 255,
            },
            {
                "name": "alarm_priority",
                "type": "enum",
                "required": False,
                "options": ["high", "medium", "low", "void"],
            },
            {
                "name": "application_area",
                "type": "enum",
                "required": True,
                "options": [
                    "no_fault",
                    "system_and_functions_of_common_interest",
                    "hvac_general_fbs",
                    "hvac_hot_water_heating",
                    "hvac_direct_electrical_heating",
                    "hvac_terminal_units",
                    "hvac_vac",
                    "lighting",
                    "security",
                    "load_management",
                    "shutters_and_blinds",
                ],
            },
            {
                "name": "error_class",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 255,
            },
            *(
                {"name": name, "type": "boolean", "required": False, "default": False}
                for name in _BITS
            ),
        ]
