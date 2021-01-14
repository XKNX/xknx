"""
Module for managing an DPT Up/Down remote value.

DPT 1.008.
"""
from enum import Enum
from typing import List

from xknx.dpt import DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import RemoteValue


class RemoteValueUpDown(RemoteValue):
    """Abstraction for remote value of KNX DPT 1.008 / DPT_UpDown."""

    class Direction(Enum):
        """Enum for indicating the direction."""

        # pylint: disable=invalid-name
        UP = 0
        DOWN = 1

    def __init__(
        self,
        xknx,
        group_address=None,
        group_address_state=None,
        device_name=None,
        feature_name="Up/Down",
        after_update_cb=None,
        invert=False,
        passive_group_addresses: List[str] = None,
    ):
        """Initialize remote value of KNX DPT 1.008."""
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
        self.invert = invert

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    def to_knx(self, value):
        """Convert value to payload."""
        if value == self.Direction.UP:
            return DPTBinary(1) if self.invert else DPTBinary(0)
        if value == self.Direction.DOWN:
            return DPTBinary(0) if self.invert else DPTBinary(1)
        raise ConversionError(
            "value invalid",
            value=value,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    def from_knx(self, payload):
        """Convert current payload to value."""
        if payload == DPTBinary(0):
            return self.Direction.DOWN if self.invert else self.Direction.UP
        if payload == DPTBinary(1):
            return self.Direction.UP if self.invert else self.Direction.DOWN
        raise CouldNotParseTelegram(
            "payload invalid",
            payload=payload,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    async def down(self) -> None:
        """Set value to down."""
        await self.set(self.Direction.DOWN)

    async def up(self) -> None:
        """Set value to UP."""
        # pylint: disable=invalid-name
        await self.set(self.Direction.UP)
