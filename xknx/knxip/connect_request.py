"""
Module for Serialization and Deserialization of a KNX Connect Request information.

Connect requests are used to start a new tunnel connection on a KNX/IP device.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import ConnectRequestType, KNXIPServiceType


class ConnectRequest(KNXIPBody):
    """Representation of a KNX Connect Request."""

    SERVICE_TYPE = KNXIPServiceType.CONNECT_REQUEST
    CRI_LENGTH = 4

    def __init__(
        self,
        request_type: ConnectRequestType = ConnectRequestType.TUNNEL_CONNECTION,
        control_endpoint: HPAI = HPAI(),
        data_endpoint: HPAI = HPAI(),
    ):
        """Initialize ConnectRequest object."""
        self.request_type = request_type
        self.control_endpoint = control_endpoint
        self.data_endpoint = data_endpoint
        # KNX layer, 0x02 = TUNNEL_LINKLAYER
        self.flags = 0x02

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return HPAI.LENGTH + HPAI.LENGTH + ConnectRequest.CRI_LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""

        def cri_from_knx(cri: bytes) -> int:
            """Parse CRI (Connection Request Information)."""
            if cri[0] != ConnectRequest.CRI_LENGTH:
                raise CouldNotParseKNXIP("CRI has wrong length")
            if len(cri) < ConnectRequest.CRI_LENGTH:
                raise CouldNotParseKNXIP("CRI data has wrong length")
            self.request_type = ConnectRequestType(cri[1])
            self.flags = cri[2]
            return 4

        pos = self.control_endpoint.from_knx(raw)
        pos += self.data_endpoint.from_knx(raw[pos:])
        pos += cri_from_knx(raw[pos:])
        return pos

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""

        def cri_to_knx() -> bytes:
            """Serialize CRI (Connect Request Information)."""
            return bytes(
                (
                    ConnectRequest.CRI_LENGTH,
                    self.request_type.value,
                    self.flags,
                    0x00,  # Reserved
                )
            )

        return (
            self.control_endpoint.to_knx() + self.data_endpoint.to_knx() + cri_to_knx()
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<ConnectRequest "
            f'control_endpoint="{self.control_endpoint}" '
            f'data_endpoint="{self.data_endpoint}" '
            f'request_type="{self.request_type}" '
            f'flags="{hex(self.flags)}" />'
        )
