"""
Module for managing a control remote value.

Examples are switching commands with priority control, relative dimming or blinds control commands.
DPT 2.yyy and DPT 3.yyy
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTControlStepCode
from xknx.exceptions import ConversionError

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueControl(RemoteValue[DPTBinary, Any]):
    """Abstraction for remote value used for controling."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool = True,
        value_type: str | None = None,
        device_name: str | None = None,
        feature_name: str = "Control",
        after_update_cb: AsyncCallbackType | None = None,
    ):
        """Initialize control remote value."""
        if value_type is None:
            raise ConversionError("no value type given", device_name=device_name)
        # TODO: typing - parse from DPTControlStepCode when parse_transcoder is a classmethod
        _dpt_class = DPTBase.parse_transcoder(value_type)
        if _dpt_class is None or not isinstance(_dpt_class(), DPTControlStepCode):
            raise ConversionError(
                "invalid value type", value_type=value_type, device_name=device_name
            )
        self.dpt_class: type[DPTControlStepCode] = _dpt_class  # type: ignore
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTBinary | None:
        """Test if telegram payload may be parsed."""
        # pylint: disable=no-self-use
        return payload if isinstance(payload, DPTBinary) else None

    def to_knx(self, value: Any) -> DPTBinary:
        """Convert value to payload."""
        return DPTBinary(self.dpt_class.to_knx(value))

    def from_knx(self, payload: DPTBinary) -> Any:
        """Convert current payload to value."""
        # TODO: DPTBinary.value is int - DPTBase.from_knx requires Tuple[int, ...] - maybe use bytes
        return self.dpt_class.from_knx((payload.value,))

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self.dpt_class.unit

    @property
    def ha_device_class(self) -> str | None:
        """Return a string representing the home assistant device class."""
        return getattr(self.dpt_class, "ha_device_class", None)  # type: ignore
