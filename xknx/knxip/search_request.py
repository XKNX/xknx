from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType

class SearchRequest(KNXIPBody):
    """Representation of a KNX Connect Request."""
    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.SEARCH_REQUEST

    def __init__(self):
        """SearchRequest __init__ object."""
        super(SearchRequest, self).__init__()
        self.discovery_endpoint = HPAI(ip_addr="224.0.23.12", port=3671)


    def calculated_length(self):
        return  HPAI.LENGTH


    def from_knx(self, raw):
        """Create a new SearchRequest KNXIP raw data."""
        pos = self.discovery_endpoint.from_knx(raw)
        return pos


    def to_knx(self):
        """Convert the SearchRequest to its byte representation."""
        data = []
        data.extend(self.discovery_endpoint.to_knx())
        return data


    def __str__(self):
        return "<SearchRequest discovery_endpoint={0}>" \
            .format(self.discovery_endpoint)
