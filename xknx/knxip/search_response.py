from .body import KNXIPBody
from .hpai import HPAI
from .dib import DIB, DIBDeviceInformation
from .knxip_enum import KNXIPServiceType

class SearchResponse(KNXIPBody):
    """Representation of a KNX Connect Request."""
    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.SEARCH_RESPONSE

    def __init__(self):
        """SearchResponse __init__ object."""
        super(SearchResponse, self).__init__()
        self.control_endpoint = HPAI()
        self.dibs = []

    def calculated_length(self):
        return HPAI.LENGTH + \
            sum([dib.calculated_length() for dib in self.dibs])


    def from_knx(self, raw):
        """Create a new SearchResponse KNXIP raw data."""
        pos = self.control_endpoint.from_knx(raw)
        while len(raw[pos:]) > 0:
            dib = DIB.determine_dib(raw[pos:])
            pos += dib.from_knx(raw[pos:])
            self.dibs.append(dib)
        return pos


    @property
    def device_name(self):
        for dib in self.dibs:
            if isinstance(dib, DIBDeviceInformation):
                return dib.name
        return "UKNOWN"


    def to_knx(self):
        """Convert the SearchResponse to its byte representation."""
        data = []
        data.extend(self.control_endpoint.to_knx())
        for dib in self.dibs:
            data.extend(dib.to_knx())
        return data


    def __str__(self):
        return "<SearchResponse control_endpoint={0} dibs=[\n{1}\n]>" \
            .format(self.control_endpoint,
                    ',\n'.join(dib.__str__() for dib in self.dibs))
