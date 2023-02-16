"""
Module for Serialization and Deserialization of a KNX Connect Response information.

Connect requests are used to start a new tunnel connection on a KNX/IP device.
With a Connect Response the receiving party acknowledges the valid processing of the request,
assigns a communication channel and an individual address for the client.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP
from xknx.telegram import IndividualAddress

from .body import KNXIPBodyResponse
from .error_code import ErrorCode
from .hpai import HPAI
from .knxip_enum import ConnectRequestType, KNXIPServiceType


class ConnectResponse(KNXIPBodyResponse):
    """Representation of a KNX Connect Response."""

    SERVICE_TYPE = KNXIPServiceType.CONNECT_RESPONSE

    def __init__(
        self,
        communication_channel: int = 0,
        status_code: ErrorCode = ErrorCode.E_NO_ERROR,
        data_endpoint: HPAI | None = None,
        crd: ConnectResponseData | None = None,
    ):
        """Initialize ConnectResponse class."""
        self.communication_channel = communication_channel
        self.status_code = status_code
        self.data_endpoint = data_endpoint or HPAI()
        self.crd = crd or ConnectResponseData()

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return 2 + HPAI.LENGTH + self.crd.calculated_length()

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""

        self.communication_channel = raw[0]
        self.status_code = ErrorCode(raw[1])
        pos = 2

        if self.status_code == ErrorCode.E_NO_ERROR:
            pos += self.data_endpoint.from_knx(raw[pos:])
            pos += self.crd.from_knx(raw[pos:])
        else:
            # do not parse HPAI and CRD in case of errors - just check length
            pos = len(raw)
        return pos

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""

        return (
            bytes((self.communication_channel, self.status_code.value))
            + self.data_endpoint.to_knx()
            + self.crd.to_knx()
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<ConnectResponse "
            f'communication_channel="{self.communication_channel}" '
            f'status_code="{self.status_code}" '
            f'data_endpoint="{self.data_endpoint}" '
            f'crd="{self.crd}" />'
        )


class ConnectResponseData:
    """Representation of a KNX Connect Response Data block (CRD)."""

    CRD_LENGTH = 2
    CRD_TUNNEL_LENGTH = 4

    def __init__(
        self,
        request_type: ConnectRequestType = ConnectRequestType.TUNNEL_CONNECTION,
        individual_address: IndividualAddress | None = None,
    ):
        """Initialize ConnectResponseData object."""
        self.request_type = request_type
        self.individual_address = individual_address

    def _is_tunnel_crd(self) -> bool:
        return self.request_type == ConnectRequestType.TUNNEL_CONNECTION

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return (
            ConnectResponseData.CRD_TUNNEL_LENGTH
            if self._is_tunnel_crd()
            else ConnectResponseData.CRD_LENGTH
        )

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        crd_length = raw[0]
        if len(raw) < crd_length:
            raise CouldNotParseKNXIP("CRD has wrong length")
        if crd_length < ConnectResponseData.CRD_LENGTH:
            raise CouldNotParseKNXIP("CRD length too small")
        self.request_type = ConnectRequestType(raw[1])
        if self._is_tunnel_crd():
            if crd_length != ConnectResponseData.CRD_TUNNEL_LENGTH:
                raise CouldNotParseKNXIP("CRD has wrong length")
            self.individual_address = IndividualAddress.from_knx(raw[2:4])
        elif crd_length != ConnectResponseData.CRD_LENGTH:
            raise CouldNotParseKNXIP("CRD has wrong length")
        return crd_length

    def to_knx(self) -> bytes:
        """Serialize CRD (Connect Response Data Block)."""
        _crd = bytes(
            (
                self.calculated_length(),
                self.request_type.value,
            )
        )
        if self._is_tunnel_crd():
            assert self.individual_address is not None
            return _crd + self.individual_address.to_knx()

        return _crd

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__

    def __repr__(self) -> str:
        """Return object as readable string."""
        _address = (
            f'individual_address="{self.individual_address}" '
            if self._is_tunnel_crd() and self.individual_address
            else ""
        )
        return (
            "<ConnectResponseData "
            f'request_type="{self.request_type}" '
            f"{_address}/>"
        )
