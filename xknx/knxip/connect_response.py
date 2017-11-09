"""
Module for Serialization and Deserialization of a KNX Connect Response information.

Connect requests are used to start a new tunnel connection on a KNX/IP device.
With an Connect Response the receiving party acknowledges the valid processing of the request.
"""
from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .error_code import ErrorCode
from .hpai import HPAI
from .knxip_enum import ConnectRequestType, KNXIPServiceType


class ConnectResponse(KNXIPBody):
    """Representation of a KNX Connect Response."""

    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.CONNECT_RESPONSE

    CRD_LENGTH = 4

    def __init__(self, xknx):
        """Initialize ConnectResponse class."""
        super(ConnectResponse, self).__init__(xknx)

        self.communication_channel = 0
        self.status_code = ErrorCode.E_NO_ERROR
        self.request_type = None
        self.control_endpoint = HPAI()
        self.identifier = None

    def calculated_length(self):
        """Get length of KNX/IP body."""
        return 2 + HPAI.LENGTH + \
            ConnectResponse.CRD_LENGTH

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        def crd_from_knx(crd):
            """Parse CRD (Connection Response Data Block)."""
            if crd[0] != ConnectResponse.CRD_LENGTH:
                raise CouldNotParseKNXIP("CRD has wrong length")
            if len(crd) < ConnectResponse.CRD_LENGTH:
                raise CouldNotParseKNXIP("CRD data has wrong length")
            self.request_type = ConnectRequestType(crd[1])
            self.identifier = crd[2]*256+crd[3]
            return 4

        self.communication_channel = raw[0]
        self.status_code = ErrorCode(raw[1])
        pos = 2

        pos += self.control_endpoint.from_knx(raw[pos:])
        pos += crd_from_knx(raw[pos:])
        return pos

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        def crd_to_knx():
            """Serialize CRD (Connect Response Data Block)."""
            crd = []
            crd.append(ConnectResponse.CRD_LENGTH)
            crd.append(self.request_type.value)
            crd.append((self.identifier >> 8) & 255)
            crd.append(self.identifier & 255)
            return crd
        data = []
        data.append(self.communication_channel)
        data.append(self.status_code.value)
        data.extend(self.control_endpoint.to_knx())
        data.extend(crd_to_knx())
        return data

    def __str__(self):
        """Return object as readable string."""
        return '<ConnectResponse communication_channel="{0}" ' \
            'status_code="{1}" control_endpoint="{2}" ' \
            'request_type="{3}" identifier="{4}" />' \
            .format(self.communication_channel, self.status_code,
                    self.control_endpoint, self.request_type,
                    self.identifier)
