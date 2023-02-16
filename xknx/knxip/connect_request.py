"""
Module for Serialization and Deserialization of a KNX Connect Request information.

Connect requests are used to start a new tunnel connection on a KNX/IP device.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP
from xknx.telegram import IndividualAddress

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import ConnectRequestType, KNXIPServiceType, TunnellingLayer


class ConnectRequest(KNXIPBody):
    """Representation of a KNX Connect Request."""

    SERVICE_TYPE = KNXIPServiceType.CONNECT_REQUEST

    def __init__(
        self,
        control_endpoint: HPAI | None = None,
        data_endpoint: HPAI | None = None,
        cri: ConnectRequestInformation | None = None,
    ):
        """Initialize ConnectRequest object."""
        self.control_endpoint = control_endpoint or HPAI()
        self.data_endpoint = data_endpoint or HPAI()
        self.cri = cri or ConnectRequestInformation()

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return HPAI.LENGTH + HPAI.LENGTH + self.cri.calculated_length()

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        pos = self.control_endpoint.from_knx(raw)
        pos += self.data_endpoint.from_knx(raw[pos:])
        pos += self.cri.from_knx(raw[pos:])
        return pos

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            self.control_endpoint.to_knx()
            + self.data_endpoint.to_knx()
            + self.cri.to_knx()
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<ConnectRequest "
            f'control_endpoint="{self.control_endpoint}" '
            f'data_endpoint="{self.data_endpoint}" '
            f'cri="{self.cri}" />'
        )


class ConnectRequestInformation:
    """
    Representation of a KNX Connect Request Information (CRI).

    A Basic CRI requests a tunnel without requesting any specific IA.
    Using `individual_address` yields an Extended CRI which is only
    supported by Tunnelling v2 devices.
    """

    CRI_LENGTH = 2
    CRI_TUNNEL_LENGTH = 4
    CRI_TUNNEL_EXT_LENGTH = 6

    def __init__(
        self,
        connection_type: ConnectRequestType = ConnectRequestType.TUNNEL_CONNECTION,
        knx_layer: TunnellingLayer = TunnellingLayer.DATA_LINK_LAYER,
        individual_address: IndividualAddress | None = None,
    ):
        """Initialize ConnectRequest object."""
        self.connection_type = connection_type
        self.knx_layer = knx_layer
        self.individual_address = individual_address

    def _is_tunnel_cri(self) -> bool:
        return self.connection_type == ConnectRequestType.TUNNEL_CONNECTION

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        if self._is_tunnel_cri():
            return (
                ConnectRequestInformation.CRI_TUNNEL_EXT_LENGTH
                if self.individual_address
                else ConnectRequestInformation.CRI_TUNNEL_LENGTH
            )
        return ConnectRequestInformation.CRI_LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        cri_length = raw[0]
        if len(raw) < cri_length:
            raise CouldNotParseKNXIP("CRI data has wrong length")
        if cri_length < ConnectRequestInformation.CRI_LENGTH:
            raise CouldNotParseKNXIP("CRI length too small")
        self.connection_type = ConnectRequestType(raw[1])
        if self._is_tunnel_cri():
            if cri_length == ConnectRequestInformation.CRI_TUNNEL_LENGTH:
                extended = False
            elif cri_length == ConnectRequestInformation.CRI_TUNNEL_EXT_LENGTH:
                extended = True
            else:
                raise CouldNotParseKNXIP("CRI has wrong length")
            self.knx_layer = TunnellingLayer(raw[2])
            self.individual_address = (
                IndividualAddress.from_knx(raw[4:6]) if extended else None
            )
        elif cri_length != ConnectRequestInformation.CRI_LENGTH:
            raise CouldNotParseKNXIP("CRI has wrong length")
        return cri_length

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        _cri = bytes(
            (
                self.calculated_length(),
                self.connection_type.value,
            )
        )
        if self._is_tunnel_cri():
            _cri = _cri + bytes(
                (
                    self.knx_layer.value,
                    0x00,  # Reserved
                )
            )
            if self.individual_address:
                _cri = _cri + self.individual_address.to_knx()

        return _cri

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__

    def __repr__(self) -> str:
        """Return object as readable string."""
        _tunnel_layer = (
            f'knx_layer="{self.knx_layer.name}" ' if self._is_tunnel_cri() else ""
        )
        _extended = (
            f'individual_address="{self.individual_address}" '
            if self._is_tunnel_cri() and self.individual_address
            else ""
        )
        return (
            "<ConnectRequestInformation "
            f'connection_type="{self.connection_type.name}" '
            f"{_tunnel_layer}"
            f"{_extended}/>"
        )
