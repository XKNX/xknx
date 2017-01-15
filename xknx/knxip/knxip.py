from .knxip_enum import KNXIPServiceType
from .header import KNXIPHeader
from .cemi_frame import CEMIFrame

class KNXIPFrame:
    """Abstraction for KNX IP Frames"""


    def __init__(self):
        """Initialize object."""

        self.header = KNXIPHeader()
        self.body = None

        self.payload = None



    def init(self, service_type_ident):
        if service_type_ident == \
            KNXIPServiceType.ROUTING_INDICATION:

            self.body = CEMIFrame()

        elif service_type_ident == \
            KNXIPServiceType.CONNECT_REQUEST:

            # TODO
            print("CONNECT REQUEST")

        else:
            raise TypeError()

    def from_knx(self, data):

        self.header.from_knx(data[0:6])

        if self.header.service_type_ident == \
                KNXIPServiceType.ROUTING_INDICATION:

            self.body = CEMIFrame()
            self.body.from_knx(data[6:])

        elif self.header.service_type_ident == \
                KNXIPServiceType.CONNECT_REQUEST:

            #TODO
            print("CONNECT REQUEST")

        else:
            raise TypeError()

    def __str__(self):
        return "<KNXIPFrame header={0}\n body={1}>" \
            .format(self.header, self.body)


    def normalize(self):
        self.header.set_length(self.body)

    def to_knx(self):

        data = []
        data.extend(self.header.to_knx())
        data.extend(self.body.to_knx())
        return data
