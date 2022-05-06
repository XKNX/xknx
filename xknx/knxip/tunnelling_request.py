"""
Module for Serialization and Deserialization of a KNX Tunnelling Request information.

Tunnelling requests are used to transmit a KNX telegram within an existing KNX tunnel connection.
"""
from __future__ import annotations

import logging

from xknx.exceptions import CouldNotParseKNXIP, UnsupportedCEMIMessage
from xknx.knxip.tpdu import TPDU

from .body import KNXIPBody
from .cemi_frame import CEMIFrame, CEMIMessageCode
from .knxip_enum import KNXIPServiceType

logger = logging.getLogger("xknx.log")


class TunnellingRequest(KNXIPBody):
    """Representation of a KNX Tunnelling Request."""

    SERVICE_TYPE = KNXIPServiceType.TUNNELLING_REQUEST
    HEADER_LENGTH = 4

    def __init__(
        self,
        communication_channel_id: int = 1,
        sequence_counter: int = 0,
        pdu: CEMIFrame | TPDU | None = None,
    ):
        """Initialize TunnellingRequest object."""
        self.communication_channel_id = communication_channel_id
        self.sequence_counter = sequence_counter
        self.pdu: CEMIFrame | TPDU | None = (
            pdu if pdu is not None else CEMIFrame(code=CEMIMessageCode.L_DATA_REQ)
        )

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        assert self.pdu is not None
        return TunnellingRequest.HEADER_LENGTH + self.pdu.calculated_length()

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        assert self.pdu is not None

        def header_from_knx(header: bytes) -> int:
            """Parse header bytes."""
            if header[0] != TunnellingRequest.HEADER_LENGTH:
                raise CouldNotParseKNXIP("connection header wrong length")
            if len(header) < TunnellingRequest.HEADER_LENGTH:
                raise CouldNotParseKNXIP("connection header wrong length")
            self.communication_channel_id = header[1]
            self.sequence_counter = header[2]
            return TunnellingRequest.HEADER_LENGTH

        pos = header_from_knx(raw)
        if len(raw[pos:]) == 10:
            # TPDU
            self.pdu = TPDU()
        try:
            pos += self.pdu.from_knx(raw[pos:])
        except UnsupportedCEMIMessage as unsupported_cemi_err:
            logger.debug("CEMI not supported: %s", unsupported_cemi_err)
            # Set pdu to None - this is checked in Tunnel() to send Ack even for unsupported CEMI messages.
            self.pdu = None
            return len(raw)

        return pos

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.pdu is None:
            raise CouldNotParseKNXIP("No CEMIFrame defined.")
        return (
            bytes(
                (
                    TunnellingRequest.HEADER_LENGTH,
                    self.communication_channel_id,
                    self.sequence_counter,
                    0x00,  # Reserved
                )
            )
            + self.pdu.to_knx()
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<TunnellingRequest "
            f'communication_channel_id="{self.communication_channel_id}" '
            f'sequence_counter="{self.sequence_counter}" '
            f'pdu="{self.pdu}" />'
        )
