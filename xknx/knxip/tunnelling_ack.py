"""
Module for Serialization and Deserialization of a KNX Tunnelling ACK information.

Tunneling requests are used to transmit a KNX telegram within an existing KNX tunnel connection.
With a Tunnelling ACK the receiving party acknowledges the valid processing of the request.
"""
from typing import TYPE_CHECKING, List

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBodyResponse
from .error_code import ErrorCode
from .knxip_enum import KNXIPServiceType

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class TunnellingAck(KNXIPBodyResponse):
    """Representation of a KNX Tunnelling Ack."""

    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.TUNNELLING_ACK

    BODY_LENGTH = 4

    def __init__(
        self, xknx: "XKNX", communication_channel_id: int = 1, sequence_counter: int = 0
    ):
        """Initialize TunnellingAck object."""
        super().__init__(xknx)
        self.communication_channel_id = communication_channel_id
        self.sequence_counter = sequence_counter
        self.status_code = ErrorCode.E_NO_ERROR

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return TunnellingAck.BODY_LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""

        def ack_from_knx(header: bytes) -> int:
            """Parse ACK information."""
            if header[0] != TunnellingAck.BODY_LENGTH:
                raise CouldNotParseKNXIP("connection header wrong length")
            if len(header) < TunnellingAck.BODY_LENGTH:
                raise CouldNotParseKNXIP("connection header wrong length")
            self.communication_channel_id = header[1]
            self.sequence_counter = header[2]
            self.status_code = ErrorCode(header[3])
            return 4

        pos = ack_from_knx(raw)
        return pos

    def to_knx(self) -> List[int]:
        """Serialize to KNX/IP raw data."""

        def ack_to_knx() -> List[int]:
            """Serialize ACK information."""
            ack = []
            ack.append(TunnellingAck.BODY_LENGTH)
            ack.append(self.communication_channel_id)
            ack.append(self.sequence_counter)
            ack.append(self.status_code.value)
            return ack

        data = []
        data.extend(ack_to_knx())
        return data

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            '<TunnellingAck communication_channel_id="{}" '
            'sequence_counter="{}" status_code="{}" />'.format(
                self.communication_channel_id, self.sequence_counter, self.status_code
            )
        )
