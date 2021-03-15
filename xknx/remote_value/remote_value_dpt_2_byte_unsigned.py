"""
Module for managing a DTP 7001 remote value.

DPT 7.001.
"""
from typing import TYPE_CHECKING, Optional, Union

from xknx.dpt import DPT2ByteUnsigned, DPTArray, DPTBinary

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueDpt2ByteUnsigned(RemoteValue[DPTArray]):
    """Abstraction for remote value of KNX DPT 7.001."""

    # pylint: disable=no-self-use

    def __init__(
        self,
        xknx: "XKNX",
        group_address: Optional[GroupAddressesType] = None,
        group_address_state: Optional[GroupAddressesType] = None,
        device_name: Optional[str] = None,
        feature_name: str = "Value",
        after_update_cb: Optional[AsyncCallbackType] = None,
    ):
        """Initialize remote value of KNX DPT 7.001."""
        # pylint: disable=too-many-arguments
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    def payload_valid(
        self, payload: Optional[Union[DPTArray, DPTBinary]]
    ) -> Optional[DPTArray]:
        """Test if telegram payload may be parsed."""
        return (
            payload
            if isinstance(payload, DPTArray) and len(payload.value) == 2
            else None
        )

    def to_knx(self, value: int) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(DPT2ByteUnsigned.to_knx(value))

    def from_knx(self, payload: DPTArray) -> int:
        """Convert current payload to value."""
        return DPT2ByteUnsigned.from_knx(payload.value)
