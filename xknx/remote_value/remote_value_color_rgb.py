"""
Module for managing an RGB remote value.

DPT 232.600.
"""
from typing import TYPE_CHECKING, List, Optional, Sequence, Tuple, Union

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError

from .remote_value import AsyncCallbackType, RemoteValue

if TYPE_CHECKING:
    from xknx.telegram.address import GroupAddressableType
    from xknx.xknx import XKNX


class RemoteValueColorRGB(RemoteValue[DPTArray]):
    """Abstraction for remote value of KNX DPT 232.600 (DPT_Color_RGB)."""

    # pylint: disable=no-self-use

    def __init__(
        self,
        xknx: "XKNX",
        group_address: Optional["GroupAddressableType"] = None,
        group_address_state: Optional["GroupAddressableType"] = None,
        device_name: Optional[str] = None,
        feature_name: str = "Color RGB",
        after_update_cb: Optional[AsyncCallbackType] = None,
        passive_group_addresses: Optional[List["GroupAddressableType"]] = None,
    ):
        """Initialize remote value of KNX DPT 232.600 (DPT_Color_RGB)."""
        # pylint: disable=too-many-arguments
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
            passive_group_addresses=passive_group_addresses,
        )

    def payload_valid(
        self, payload: Optional[Union[DPTArray, DPTBinary]]
    ) -> Optional[DPTArray]:
        """Test if telegram payload may be parsed."""
        return (
            payload
            if isinstance(payload, DPTArray) and len(payload.value) == 3
            else None
        )

    def to_knx(self, value: Sequence[int]) -> DPTArray:
        """Convert value to payload."""
        if not isinstance(value, (list, tuple)):
            raise ConversionError(
                "Could not serialize RemoteValueColorRGB (wrong type)",
                value=value,
                type=type(value),
            )
        if len(value) != 3:
            raise ConversionError(
                "Could not serialize DPT 232.600 (wrong length)",
                value=value,
                type=type(value),
            )
        if (
            any(not isinstance(color, int) for color in value)
            or any(color < 0 for color in value)
            or any(color > 255 for color in value)
        ):
            raise ConversionError(
                "Could not serialize DPT 232.600 (wrong bytes)", value=value
            )

        return DPTArray(list(value))

    def from_knx(self, payload: DPTArray) -> Tuple[int, int, int]:
        """Convert current payload to value."""
        return payload.value[0], payload.value[1], payload.value[2]
