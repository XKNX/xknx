"""
Module for managing an climate mode remote values.

DPT .
"""
from abc import abstractmethod
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
    cast,
)

from xknx.dpt import (
    DPTArray,
    DPTBinary,
    DPTControllerStatus,
    DPTHVACContrMode,
    DPTHVACMode,
)
from xknx.dpt.dpt_hvac_mode import HVACControllerMode, HVACOperationMode
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import RemoteValue

if TYPE_CHECKING:
    from xknx.telegram.address import GroupAddressableType
    from xknx.xknx import XKNX

    AsyncCallback = Callable[[], Awaitable[None]]
    DPTPayload = Union[DPTArray, DPTBinary]

HVACModeType = TypeVar("HVACModeType", "HVACControllerMode", "HVACOperationMode")


class RemoteValueClimateModeBase(RemoteValue, Generic[HVACModeType]):
    """Base class for binary climate mode remote values."""

    @abstractmethod
    def supported_operation_modes(
        self,
    ) -> List["HVACModeType"]:
        """Return a list of all supported operation modes."""


class RemoteValueClimateMode(RemoteValueClimateModeBase[HVACModeType]):
    """Abstraction for remote value of KNX climate modes."""

    class ClimateModeType(Enum):
        """Implemented climate mode types."""

        CONTROLLER_STATUS = DPTControllerStatus
        HVAC_CONTR_MODE = DPTHVACContrMode
        HVAC_MODE = DPTHVACMode

    def __init__(
        self,
        xknx: "XKNX",
        group_address: Optional["GroupAddressableType"] = None,
        group_address_state: Optional["GroupAddressableType"] = None,
        sync_state: bool = True,
        device_name: Optional[str] = None,
        feature_name: str = "Climate Mode",
        climate_mode_type: Optional[ClimateModeType] = None,
        after_update_cb: Optional["AsyncCallback"] = None,
        passive_group_addresses: Optional[List["GroupAddressableType"]] = None,
    ):
        """Initialize remote value of KNX climate mode."""
        # pylint: disable=too-many-arguments
        super().__init__(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
            passive_group_addresses=passive_group_addresses,
        )
        if not isinstance(climate_mode_type, self.ClimateModeType):
            raise ConversionError(
                "invalid climate mode type",
                climate_mode_type=str(climate_mode_type),
                device_name=str(device_name),
                feature_name=feature_name,
            )
        self._climate_mode_transcoder = climate_mode_type.value

    def supported_operation_modes(self) -> List["HVACModeType"]:
        """Return a list of all supported operation modes."""
        return list(self._climate_mode_transcoder.SUPPORTED_MODES.values())

    @staticmethod
    def payload_valid(payload: Optional["DPTPayload"]) -> bool:
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTArray) and len(payload.value) == 1

    def to_knx(self, value: Any) -> "DPTPayload":
        """Convert value to payload."""
        return DPTArray(self._climate_mode_transcoder.to_knx(value))

    def from_knx(self, payload: "DPTPayload") -> Optional[HVACModeType]:
        """Convert current payload to value."""
        # TODO: typing - remove cast
        return cast(
            Optional[HVACModeType],
            self._climate_mode_transcoder.from_knx(payload.value),
        )


class RemoteValueBinaryOperationMode(RemoteValueClimateModeBase[HVACOperationMode]):
    """Abstraction for remote value of split up KNX climate modes."""

    def __init__(
        self,
        xknx: "XKNX",
        group_address: Optional["GroupAddressableType"] = None,
        group_address_state: Optional["GroupAddressableType"] = None,
        sync_state: bool = True,
        device_name: Optional[str] = None,
        feature_name: str = "Climate Mode Binary",
        after_update_cb: Optional["AsyncCallback"] = None,
        operation_mode: Optional[HVACOperationMode] = None,
    ):
        """Initialize remote value of KNX DPT 1 representing a climate operation mode."""
        # pylint: disable=too-many-arguments
        if not isinstance(operation_mode, HVACOperationMode):
            raise ConversionError(
                "Invalid operation mode type",
                operation_mode=str(operation_mode),
                device_name=str(device_name),
                feature_name=feature_name,
            )
        if operation_mode not in self.supported_operation_modes():
            raise ConversionError(
                "Operation mode not supported for binary mode object",
                operation_mode=str(operation_mode),
                device_name=str(device_name),
                feature_name=feature_name,
            )
        self.operation_mode = operation_mode
        super().__init__(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=True,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    @staticmethod
    def payload_valid(payload: Optional["DPTPayload"]) -> bool:
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    def to_knx(self, value: Any) -> "DPTPayload":
        """Convert value to payload."""
        if isinstance(value, HVACOperationMode):
            # foreign operation modes will set the RemoteValue to False
            return DPTBinary(value == self.operation_mode)
        raise ConversionError(
            "value invalid",
            value=value,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    @staticmethod
    def supported_operation_modes() -> List[HVACOperationMode]:
        """Return a list of the configured operation mode."""
        return [
            HVACOperationMode.COMFORT,
            HVACOperationMode.FROST_PROTECTION,
            HVACOperationMode.NIGHT,
            HVACOperationMode.STANDBY,
        ]

    def from_knx(self, payload: "DPTPayload") -> Optional[HVACOperationMode]:
        """Convert current payload to value."""
        if payload == DPTBinary(1):
            return self.operation_mode
        if payload == DPTBinary(0):
            return None
        raise CouldNotParseTelegram(
            "payload invalid",
            payload=str(payload),
            device_name=self.device_name,
            feature_name=self.feature_name,
        )


class RemoteValueBinaryHeatCool(RemoteValueClimateModeBase[HVACControllerMode]):
    """Abstraction for remote value of heat/cool controller mode."""

    def __init__(
        self,
        xknx: "XKNX",
        group_address: Optional["GroupAddressableType"] = None,
        group_address_state: Optional["GroupAddressableType"] = None,
        sync_state: bool = True,
        device_name: Optional[str] = None,
        feature_name: str = "Controller Mode Heat/Cool",
        after_update_cb: Optional["AsyncCallback"] = None,
        controller_mode: Optional[HVACControllerMode] = None,
    ):
        """Initialize remote value of KNX DPT 1 representing a climate controller mode."""
        # pylint: disable=too-many-arguments
        if not isinstance(controller_mode, HVACControllerMode):
            raise ConversionError(
                "Invalid controller mode type",
                controller_mode=str(controller_mode),
                device_name=str(device_name),
                feature_name=feature_name,
            )
        if controller_mode not in self.supported_operation_modes():
            raise ConversionError(
                "Controller mode not supported for binary mode object",
                controller_mode=str(controller_mode),
                device_name=str(device_name),
                feature_name=feature_name,
            )
        self.controller_mode = controller_mode
        super().__init__(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=True,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    @staticmethod
    def payload_valid(payload: Optional["DPTPayload"]) -> bool:
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    @staticmethod
    def supported_operation_modes() -> List[HVACControllerMode]:
        """Return a list of the configured operation mode."""
        return [HVACControllerMode.HEAT, HVACControllerMode.COOL]

    def to_knx(self, value: Any) -> "DPTPayload":
        """Convert value to payload."""
        if isinstance(value, HVACControllerMode):
            # foreign operation modes will set the RemoteValue to False
            return DPTBinary(value == self.controller_mode)
        raise ConversionError(
            "value invalid",
            value=value,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    def from_knx(self, payload: "DPTPayload") -> Optional[HVACControllerMode]:
        """Convert current payload to value."""
        if payload == DPTBinary(1):
            return self.controller_mode
        if payload == DPTBinary(0):
            # return the other operation mode
            return next(
                (
                    _op
                    for _op in self.supported_operation_modes()
                    if _op is not self.controller_mode
                ),
                None,
            )
        raise CouldNotParseTelegram(
            "payload invalid",
            payload=str(payload),
            device_name=self.device_name,
            feature_name=self.feature_name,
        )
