"""
Module for Serialization and Deserialization of a KNX Tunnelling Feature service.

The Tunnelling Client shall use the Tunnelling Feature services TUNNELLING_FEATURE_GET and
TUNNELLING_FEATURE_SET to read and respectively write features related to the Tunnelling
interface and the Tunnelling host device.
The Tunnelling Server shall use the service TUNNELLING_FEATURE_INFO to spontaneously report
Tunnelling Clients about relevant changes in the state of itself or the Tunnelling connection.
"""
from __future__ import annotations

import struct

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody, KNXIPBodyResponse
from .error_code import ErrorCode
from .knxip_enum import KNXIPServiceType, TunnellingFeatureType


class _TunnellingFeature:
    """Base representation of a KNX Tunnelling Feature interface request."""

    HEADER_LENGTH = 4
    FEATURE_ID_LENGTH = 2

    def __init__(
        self,
        communication_channel_id: int = 1,
        sequence_counter: int = 0,
        status_code: ErrorCode = ErrorCode.E_NO_ERROR,
        feature_type: TunnellingFeatureType = TunnellingFeatureType.SUPPORTED_EMI_TYPE,
        data: bytes = b"",
    ):
        """Initialize _TunnellingFeature object."""
        self.communication_channel_id = communication_channel_id
        self.sequence_counter = sequence_counter
        self.status_code = status_code
        self.feature_type = feature_type
        self.data = data

    def _has_data(self) -> bool:
        return True

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        data_size = len(self.data) + (len(self.data) % 2) if self._has_data() else 0
        return (
            _TunnellingFeature.HEADER_LENGTH
            + _TunnellingFeature.FEATURE_ID_LENGTH
            + data_size
        )

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if raw[0] != _TunnellingFeature.HEADER_LENGTH:  # structure_length field
            raise CouldNotParseKNXIP("TunnellingFeature header has invalid length")
        self.communication_channel_id = raw[1]
        self.sequence_counter = raw[2]
        self.status_code = ErrorCode(raw[3])
        self.feature_type = TunnellingFeatureType(raw[4])
        self.data = raw[6:]
        if self._has_data() and len(self.data) == 0:
            raise CouldNotParseKNXIP("TunnellingFeature missing data")
        if not self._has_data() and len(self.data) > 0:
            raise CouldNotParseKNXIP("TunnellingFeature unexpected data")
        return len(raw)

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        data_size = len(self.data) + (len(self.data) % 2) if self._has_data() else 0
        return struct.pack(
            # Append a NUL byte if data size is uneven
            f"!BBBBBx{data_size}s",
            _TunnellingFeature.HEADER_LENGTH,
            self.communication_channel_id,
            self.sequence_counter,
            self.status_code.value,
            self.feature_type.value,
            self.data,
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        _data = f'data="{self.data.hex()}" ' if self._has_data() else ""
        return (
            f"<{self.__class__.__name__} "
            f'communication_channel_id="{self.communication_channel_id}" '
            f'sequence_counter="{self.sequence_counter}" '
            f'feature_type="{self.feature_type}" '
            f"{_data}/>"
        )


class TunnellingFeatureGet(_TunnellingFeature, KNXIPBody):
    """Representation of a KNX Tunnelling Feature Get request."""

    SERVICE_TYPE = KNXIPServiceType.TUNNELLING_FEATURE_GET

    def __init__(
        self,
        communication_channel_id: int = 1,
        sequence_counter: int = 0,
        feature_type: TunnellingFeatureType = TunnellingFeatureType.SUPPORTED_EMI_TYPE,
    ):
        """Initialize TunnellingFeatureGet object."""
        super().__init__(
            communication_channel_id=communication_channel_id,
            sequence_counter=sequence_counter,
            feature_type=feature_type,
        )

    def _has_data(self) -> bool:
        return False


class TunnellingFeatureSet(_TunnellingFeature, KNXIPBody):
    """Representation of a KNX Tunnelling Feature Set request."""

    SERVICE_TYPE = KNXIPServiceType.TUNNELLING_FEATURE_SET

    def __init__(
        self,
        communication_channel_id: int = 1,
        sequence_counter: int = 0,
        feature_type: TunnellingFeatureType = TunnellingFeatureType.SUPPORTED_EMI_TYPE,
        data: bytes = b"",
    ):
        """Initialize TunnellingFeatureSet object."""
        super().__init__(
            communication_channel_id=communication_channel_id,
            sequence_counter=sequence_counter,
            feature_type=feature_type,
            data=data,
        )


class TunnellingFeatureInfo(_TunnellingFeature, KNXIPBody):
    """Representation of a KNX Tunnelling Feature Info indication."""

    SERVICE_TYPE = KNXIPServiceType.TUNNELLING_FEATURE_INFO

    def __init__(
        self,
        communication_channel_id: int = 1,
        sequence_counter: int = 0,
        feature_type: TunnellingFeatureType = TunnellingFeatureType.SUPPORTED_EMI_TYPE,
        data: bytes = b"",
    ):
        """Initialize TunnellingFeatureInfo object."""
        super().__init__(
            communication_channel_id=communication_channel_id,
            sequence_counter=sequence_counter,
            feature_type=feature_type,
            data=data,
        )


class TunnellingFeatureResponse(_TunnellingFeature, KNXIPBodyResponse):
    """Representation of a KNX Tunnelling Feature response."""

    SERVICE_TYPE = KNXIPServiceType.TUNNELLING_FEATURE_RESPONSE

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<TunnellingFeatureResponse "
            f'communication_channel_id="{self.communication_channel_id}" '
            f'sequence_counter="{self.sequence_counter}" '
            f'status_code="{self.status_code}" '
            f'feature_type="{self.feature_type}" '
            f'data="{self.data.hex()}" />'
        )
