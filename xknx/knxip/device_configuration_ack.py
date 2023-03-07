"""Module for Serialization and Deserialization of a KNX Device Configuration ACK."""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBodyResponse
from .error_code import ErrorCode
from .knxip_enum import KNXIPServiceType


class DeviceConfigurationAck(KNXIPBodyResponse):
    """Representation of a KNX Device Configuration Ack."""

    SERVICE_TYPE = KNXIPServiceType.DEVICE_CONFIGURATION_ACK
    BODY_LENGTH = 4

    def __init__(
        self,
        communication_channel_id: int = 1,
        sequence_counter: int = 0,
        status_code: ErrorCode = ErrorCode.E_NO_ERROR,
    ):
        """Initialize DeviceConfigurationAck object."""
        self.communication_channel_id = communication_channel_id
        self.sequence_counter = sequence_counter
        self.status_code = status_code

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return DeviceConfigurationAck.BODY_LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if raw[0] != DeviceConfigurationAck.BODY_LENGTH:  # structure_length field
            raise CouldNotParseKNXIP("DeviceConfigurationAck body has invalid length")
        if len(raw) != DeviceConfigurationAck.BODY_LENGTH:
            raise CouldNotParseKNXIP("DeviceConfigurationAck body has wrong length")
        self.communication_channel_id = raw[1]
        self.sequence_counter = raw[2]
        self.status_code = ErrorCode(raw[3])
        return DeviceConfigurationAck.BODY_LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return bytes(
            (
                DeviceConfigurationAck.BODY_LENGTH,
                self.communication_channel_id,
                self.sequence_counter,
                self.status_code.value,
            )
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<DeviceConfigurationAck "
            f'communication_channel_id="{self.communication_channel_id}" '
            f'sequence_counter="{self.sequence_counter}" '
            f'status_code="{self.status_code}" />'
        )
