"""Module for Serialization and Deserialization of a KNX Device Configuration Request."""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType


class DeviceConfigurationRequest(KNXIPBody):
    """Representation of a KNX Device Configuration Request."""

    SERVICE_TYPE = KNXIPServiceType.DEVICE_CONFIGURATION_REQUEST
    HEADER_LENGTH = 4

    def __init__(
        self,
        communication_channel_id: int = 1,
        sequence_counter: int = 0,
        raw_cemi: bytes = b"",
    ):
        """Initialize DeviceConfigurationRequest object."""
        self.communication_channel_id = communication_channel_id
        self.sequence_counter = sequence_counter
        self.raw_cemi = raw_cemi

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return DeviceConfigurationRequest.HEADER_LENGTH + len(self.raw_cemi)

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if raw[0] != DeviceConfigurationRequest.HEADER_LENGTH:
            raise CouldNotParseKNXIP("connection header wrong length")
        if len(raw) < DeviceConfigurationRequest.HEADER_LENGTH:
            raise CouldNotParseKNXIP("connection header wrong length")
        self.communication_channel_id = raw[1]
        self.sequence_counter = raw[2]
        # raw[3] is reserved
        self.raw_cemi = raw[DeviceConfigurationRequest.HEADER_LENGTH :]
        return len(raw)

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            bytes(
                (
                    DeviceConfigurationRequest.HEADER_LENGTH,
                    self.communication_channel_id,
                    self.sequence_counter,
                    0x00,  # Reserved
                )
            )
            + self.raw_cemi
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<DeviceConfigurationRequest "
            f'communication_channel_id="{self.communication_channel_id}" '
            f'sequence_counter="{self.sequence_counter}" '
            f'cemi="{self.raw_cemi.hex()}" />'
        )
