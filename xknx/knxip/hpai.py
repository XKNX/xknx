from .exception import CouldNotParseKNXIP, ConversionException

class HPAI():

    LENGTH = 0x08
    TYPE_UDP = 0x01

    def __init__(self, ip_addr='0.0.0.0', port=0):
        self.ip_addr = ip_addr
        self.port = port

    def from_knx(self, raw):
        """Create a new HPAI from raw data."""
        if len(raw) < HPAI.LENGTH:
            raise CouldNotParseKNXIP("wrong HPAI length")
        if raw[0] != HPAI.LENGTH:
            raise CouldNotParseKNXIP("wrong HPAI length")
        if raw[1] != HPAI.TYPE_UDP:
            raise CouldNotParseKNXIP("wrong HPAI type")

        self.ip_addr = "{0}.{1}.{2}.{3}".format(
            raw[2], raw[3], raw[4], raw[5])
        self.port = raw[6]*256 + raw[7]

        return HPAI.LENGTH

    def to_knx(self):
        """Convert the HPAI object to its byte representation."""

        def ip_addr_to_bytes(ip_addr):
            if not isinstance(ip_addr, str):
                raise ConversionException("ip_addr is not a string")
            for i in ip_addr.split("."):
                yield int(i)

        data = []
        data.append(HPAI.LENGTH)
        data.append(HPAI.TYPE_UDP)
        data.extend(ip_addr_to_bytes(self.ip_addr))
        data.append((self.port >> 8) & 255)
        data.append(self.port & 255)

        return data


    def __str__(self):
        return "<HPAI {0}:{1}>".format(self.ip_addr, self.port)


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
