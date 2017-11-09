"""
Module for Serialization and Deserialization of a KNX Tunnel ACK information.

Connect requests are used to transmit a KNX telegram within an existing KNX tunnel connection.
With an Tunnel ACK the receiving party acknowledges the valid processing of the request.
"""
from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .error_code import ErrorCode
from .knxip_enum import KNXIPServiceType


class TunnellingAck(KNXIPBody):
    """Representation of a KNX Connect Request."""

    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.TUNNELLING_ACK

    BODY_LENGTH = 4

    def __init__(self, xknx):
        """Initialize TunnellingAck object."""
        super(TunnellingAck, self).__init__(xknx)
        self.communication_channel_id = 1
        self.sequence_counter = 0
        self.status_code = ErrorCode.E_NO_ERROR

    def calculated_length(self):
        """Get length of KNX/IP body."""
        return TunnellingAck.BODY_LENGTH

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        def ack_from_knx(header):
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

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        def ack_to_knx():
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

    def __str__(self):
        """Return object as readable string."""
        return '<TunnellingAck communication_channel_id="{0}" ' \
            'sequence_counter="{1}" status_code="{2}" />' \
            .format(self.communication_channel_id, self.sequence_counter,
                    self.status_code)
