"""
Module for serialization and deserialization of KNX DIB information.

DIB is Description Information Block.

A KNX/IP Search Response may contain several DIBs of different types:

* DIBSuppSVCFamilies:   Supported features of device
* DIBDeviceInformation: Name, serial number, some unimportant flags
* DIBGeneric:           General Information
                        (fallback for unknown dib type codes)
"""

from xknx.exceptions import CouldNotParseKNXIP
from xknx.telegram import PhysicalAddress

from .knxip_enum import DIBServiceFamily, DIBTypeCode, KNXMedium


class DIB():
    """
    Base class for DIB (Description Information Block).

    This base class is only the interface for the derived
    classes.
    """

    def __init__(self):
        """Initialize DIB class."""

    def calculated_length(self):
        """Get length of KNX/IP object."""

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""

    def to_knx(self):
        """Serialize to KNX/IP raw data."""

    @staticmethod
    def determine_dib(raw):
        """Determine dib type out of dib type code."""
        if len(raw) < 2:
            raise CouldNotParseKNXIP("could not parse DIB header")
        dtc = DIBTypeCode(raw[1])

        if dtc == DIBTypeCode.DEVICE_INFO:
            return DIBDeviceInformation()
        if dtc == DIBTypeCode.SUPP_SVC_FAMILIES:
            return DIBSuppSVCFamilies()
        return DIBGeneric()


class DIBGeneric(DIB):
    """
    Module for serialization and deserialization of KNX DIB Generic.

    Fallback for not implemented DIBTypeCodes.
    """

    def __init__(self):
        """Initialize DIBGeneric class."""
        super().__init__()
        # DTC Description Type Code
        self.dtc = None
        # IBD Information Block Data
        self.data = []

    def calculated_length(self):
        """Get length of KNX/IP object."""
        return len(self.data)

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 2:
            raise CouldNotParseKNXIP("could not parse DIB header")

        dib_length = raw[0]
        if len(raw) < dib_length:
            raise CouldNotParseKNXIP("DIB wrong length")

        self.dtc = DIBTypeCode(raw[1])
        self.data = raw[:dib_length]

        return dib_length

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        data = []
        data.append(len(self.data))
        data.append(self.dtc.value)
        data.extend(self.data[2:])
        return data

    def __str__(self):
        """Return object as readable string."""
        return '<DIB dtc="{0}" data="{1}" />'.format(
            self.dtc,
            ', '.join('0x%02x' % i for i in self.data))


class DIBSuppSVCFamilies(DIB):
    """Class for serialization and deserialization of KNX DIB Supported Services."""

    # pylint: disable=too-few-public-methods

    class Family:
        """Class for storing a supported device family."""

        def __init__(self, name=None, version=None):
            """Initialize DIBSuppSVCFamilies.Family."""
            self.name = name
            self.version = version

        def __str__(self):
            """Return object as readable string."""
            return '<Family name="{0}" version="{1}" />' \
                .format(self.name, self.version)

        def __eq__(self, other):
            """Equal operator."""
            return self.__dict__ == other.__dict__

    def __init__(self):
        """Initialize DIBSuppSVCFamilies class."""
        super().__init__()
        self.families = []

    def supports(self, name):
        """Return if device supports a given service family by name."""
        for family in self.families:
            if name == family.name:
                return True
        return False

    def calculated_length(self):
        """Get length of KNX/IP object."""
        return len(self.families)*2+2

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 2:
            raise CouldNotParseKNXIP("DIB header too small")
        length = raw[0]
        if len(raw) < length:
            raise CouldNotParseKNXIP("DIB wrong size")
        if DIBTypeCode(raw[1]) != DIBTypeCode.SUPP_SVC_FAMILIES:
            raise CouldNotParseKNXIP("DIB is no device info")

        for i in range(0, int((length-2)/2)):
            name = DIBServiceFamily(raw[i*2+2])
            version = raw[i*2+3]
            self.families.append(DIBSuppSVCFamilies.Family(name, version))
        return length

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        data = []
        data.append(len(self.families)*2+2)
        data.append(DIBTypeCode.SUPP_SVC_FAMILIES.value)
        for family in self.families:
            data.append(family.name.value)
            data.append(family.version)
        return data

    def __str__(self):
        """Return object as readable string."""
        return '<DIBSuppSVCFamilies families="[{0}]" />' \
            .format(", ".join("{0} version: {1}".format(
                family.name, family.version) for family in self.families))


class DIBDeviceInformation(DIB):
    """Class for serialization and deserialization of KNX DIB Device Information Block."""

    # pylint: disable=too-many-instance-attributes

    LENGTH = 54

    def __init__(self):
        """Initialize DIBDeviceInformation class."""
        super().__init__()
        self.knx_medium = KNXMedium.TP1
        self.programming_mode = False
        self.individual_address = PhysicalAddress(None)
        self.installation_number = 0
        self.project_number = 0
        self.serial_number = ""
        self.multicast_address = "224.0.23.12"
        self.mac_address = ""
        self.name = ""

    def calculated_length(self):
        """Get length of KNX/IP object."""
        return DIBDeviceInformation.LENGTH

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < DIBDeviceInformation.LENGTH:
            raise CouldNotParseKNXIP("wrong connection header length")
        if raw[0] != DIBDeviceInformation.LENGTH:
            raise CouldNotParseKNXIP("wrong connection header length")
        if DIBTypeCode(raw[1]) != DIBTypeCode.DEVICE_INFO:
            raise CouldNotParseKNXIP("DIB is no device info")

        self.knx_medium = KNXMedium(raw[2])
        # last bit of device_status. All other bits are unused
        self.programming_mode = bool(raw[3])
        self.individual_address = \
            PhysicalAddress((raw[4], raw[5]))
        installation_project_identifier = raw[6]*256+raw[7]
        self.project_number = installation_project_identifier >> 4
        self.installation_number = installation_project_identifier & 15
        self.serial_number = ":".join('%02x' % i for i in raw[8:14])
        self.multicast_address = ".".join('%i' % i for i in raw[14:18])
        self.mac_address = ":".join('%02x' % i for i in raw[18:24])
        self.name = "".join(map(chr, raw[24:54])).rstrip('\0')
        return DIBDeviceInformation.LENGTH

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        def hex_notation_to_knx(serial_number):
            """Serialize hex notation."""
            for part in serial_number.split(":"):
                yield int(part, 16)

        def ip_to_knx(ip_addr):
            """Serialize ip."""
            for part in ip_addr.split("."):
                yield int(part)

        def str_to_knx(string, length):
            """Serialize string."""
            if len(string) > length-1:
                string = string[:length-1]
            for char in string:
                yield ord(char)
            for _ in range(0, 30-len(string)):
                yield 0x00
        installation_project_identifier = \
            (self.project_number * 16) + \
            self.installation_number
        data = []
        data.append(DIBDeviceInformation.LENGTH)
        data.append(DIBTypeCode.DEVICE_INFO.value)
        data.append(self.knx_medium.value)
        data.append(int(self.programming_mode))
        data.extend(self.individual_address.to_knx())
        data.append((installation_project_identifier >> 8) & 255)
        data.append(installation_project_identifier & 255)
        data.extend(hex_notation_to_knx(self.serial_number))
        data.extend(ip_to_knx(self.multicast_address))
        data.extend(hex_notation_to_knx(self.mac_address))
        data.extend(str_to_knx(self.name, 30))
        return data

    def __str__(self):
        """Return object as readable string."""
        return '<DIBDeviceInformation ' \
               '\n\tknx_medium="{0}" ' \
               '\n\tprogramming_mode="{1}" ' \
               '\n\tindividual_address="{2}" ' \
               '\n\tinstallation_number="{3}" ' \
               '\n\tproject_number="{4}" ' \
               '\n\tserial_number="{5}" ' \
               '\n\tmulticast_address="{6}" ' \
               '\n\tmac_address="{7}" ' \
               '\n\tname="{8}" />'.format(
                   self.knx_medium, self.programming_mode,
                   self.individual_address, self.installation_number,
                   self.project_number, self.serial_number,
                   self.multicast_address, self.mac_address, self.name)
