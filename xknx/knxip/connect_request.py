"""
Module for Serialization and Deserialization of a KNX Connect Request information.

Connect requests are used to start a new tunnel connection on a KNX/IP device.
"""
from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import ConnectRequestType, KNXIPServiceType


class ConnectRequest(KNXIPBody):
    """Representation of a KNX Connect Request."""

    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.CONNECT_REQUEST

    CRI_LENGTH = 4

    def __init__(self, xknx):
        """Initialize ConnectRequest object."""
        super(ConnectRequest, self).__init__(xknx)
        self.request_type = None
        self.control_endpoint = HPAI()
        self.data_endpoint = HPAI()
        # KNX layer, 0x02 = TUNNEL_LINKLAYER
        self.flags = 0x02

    def calculated_length(self):
        """Get length of KNX/IP body."""
        return HPAI.LENGTH + \
            HPAI.LENGTH + \
            ConnectRequest.CRI_LENGTH

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        def cri_from_knx(cri):
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

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        def cri_to_knx():
            """Serialize CRI (Connect Request Information)."""
            cri = []
            cri.append(ConnectRequest.CRI_LENGTH)
            cri.append(self.request_type.value)
            cri.append(self.flags)
            cri.append(0x00)  # Reserved
            return cri
        data = []
        data.extend(self.control_endpoint.to_knx())
        data.extend(self.data_endpoint.to_knx())
        data.extend(cri_to_knx())
        return data

    def __str__(self):
        """Return object as readable string."""
        return '<ConnectRequest control_endpoint="{0}" data_endpoint="{1}" ' \
            'request_type="{2}" />' .format(
                self.control_endpoint,
                self.data_endpoint,
                self.request_type)
