"""
Module for Serialization and Deserialization of a KNX Connect Response information.

Connect requests are used to start a new tunnel connection on a KNX/IP device.
With a Connect Response the receiving party acknowledges the valid processing of the request,
assigns a communication channel and an individual address for the client.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBodyResponse
from .error_code import ErrorCode
from .hpai import HPAI
from .knxip_enum import ConnectRequestType, KNXIPServiceType


class ConnectResponse(KNXIPBodyResponse):
    """Representation of a KNX Connect Response."""

    SERVICE_TYPE = KNXIPServiceType.CONNECT_RESPONSE
    CRD_LENGTH = 4

    def __init__(
        self,
        communication_channel: int = 0,
        status_code: ErrorCode = ErrorCode.E_NO_ERROR,
        request_type: ConnectRequestType = ConnectRequestType.TUNNEL_CONNECTION,
        data_endpoint: HPAI | None = None,
        identifier: int = 0,
    ):
        """Initialize ConnectResponse class."""
        self.communication_channel = communication_channel
        self.status_code = status_code
        self.request_type = request_type
        self.data_endpoint = data_endpoint or HPAI()
        # identifier shall contain KNX Individual Address assigned to this KNXnet/IP Tunnelling connection
        self.identifier = identifier

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return 2 + HPAI.LENGTH + ConnectResponse.CRD_LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""

        def crd_from_knx(crd: bytes) -> int:
            """Parse CRD (Connection Response Data Block)."""
            if crd[0] != ConnectResponse.CRD_LENGTH:
                raise CouldNotParseKNXIP("CRD has wrong length")
            if len(crd) < ConnectResponse.CRD_LENGTH:
                raise CouldNotParseKNXIP("CRD data has wrong length")
            self.request_type = ConnectRequestType(crd[1])
            self.identifier = crd[2] * 256 + crd[3]
            return 4

        self.communication_channel = raw[0]
        self.status_code = ErrorCode(raw[1])
        pos = 2

        if self.status_code == ErrorCode.E_NO_ERROR:
            pos += self.data_endpoint.from_knx(raw[pos:])
            pos += crd_from_knx(raw[pos:])
        else:
            # do not parse HPAI and CRD in case of errors - just check length
            pos = len(raw)
        return pos

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""

        def crd_to_knx() -> bytes:
            """Serialize CRD (Connect Response Data Block)."""
            assert self.identifier is not None

            return bytes(
                (ConnectResponse.CRD_LENGTH, self.request_type.value)
            ) + self.identifier.to_bytes(2, "big")

        return (
            bytes((self.communication_channel, self.status_code.value))
            + self.data_endpoint.to_knx()
            + crd_to_knx()
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<ConnectResponse "
            f'communication_channel="{self.communication_channel}" '
            f'status_code="{self.status_code}" '
            f'data_endpoint="{self.data_endpoint}" '
            f'request_type="{self.request_type}" '
            f'identifier="{self.identifier}" />'
        )
