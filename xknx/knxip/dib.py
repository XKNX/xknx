"""
Module for serialization and deserialization of KNX DIB information.

DIB is Description Information Block.

A KNX/IP Search Response may contain several DIBs of different types:

* DIBSuppSVCFamilies:   Supported features of device
* DIBDeviceInformation: Name, serial number, some unimportant flags
* DIBGeneric:           General Information
                        (fallback for unknown dib type codes)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import socket
from typing import NamedTuple, final

from xknx.exceptions import CouldNotParseKNXIP
from xknx.telegram import IndividualAddress

from .knxip_enum import DIBServiceFamily, DIBTypeCode, KNXMedium

DIB_HEADER_LENGTH = 2  # structure length and description type code


class DIB(ABC):
    """
    Base class for DIB (Description Information Block).

    This base class is only the interface for the derived
    classes.
    """

    @abstractmethod
    def calculated_length(self) -> int:
        """Get length of KNX/IP object."""
        # The structure shall always have an even number of octets which may have to be
        # achieved by padding with 00h in the last octet of the DIB structure.

    @abstractmethod
    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""

    @abstractmethod
    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""

    @staticmethod
    def determine_dib(raw: bytes) -> DIB:
        """Determine dib type out of dib type code."""
        if len(raw) < 2:
            raise CouldNotParseKNXIP("could not parse DIB header")
        dtc = DIBTypeCode(raw[1])

        if dtc == DIBTypeCode.DEVICE_INFO:
            return DIBDeviceInformation()
        if dtc == DIBTypeCode.SUPP_SVC_FAMILIES:
            return DIBSuppSVCFamilies()
        if dtc == DIBTypeCode.SECURED_SERVICE_FAMILIES:
            return DIBSecuredServiceFamilies()
        if dtc == DIBTypeCode.TUNNELING_INFO:
            return DIBTunnelingInfo()
        return DIBGeneric()


class DIBGeneric(DIB):
    """
    Module for serialization and deserialization of KNX DIB Generic.

    Fallback for not implemented DIBTypeCodes.
    """

    def __init__(self) -> None:
        """Initialize DIBGeneric class."""
        # DTC Description Type Code
        self.dtc: DIBTypeCode | int = 0
        # IBD Information Block Data
        self.data = b""

    def calculated_length(self) -> int:
        """Get length of KNX/IP object."""
        data_length = len(self.data)
        return DIB_HEADER_LENGTH + data_length + data_length % 2

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 2:
            raise CouldNotParseKNXIP("could not parse DIB header")

        dib_length = raw[0]
        if len(raw) < dib_length:
            raise CouldNotParseKNXIP("DIB wrong length")
        try:
            self.dtc = DIBTypeCode(raw[1])
        except ValueError:
            self.dtc = raw[1]
        self.data = raw[2:dib_length]

        return dib_length

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if not isinstance(self.dtc, DIBTypeCode):
            try:
                self.dtc = DIBTypeCode(self.dtc)
            except ValueError:
                raise CouldNotParseKNXIP("DTC invalid")
        return (
            bytes((self.calculated_length(), self.dtc.value))
            + self.data
            + bytes(len(self.data) % 2)  # padding
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return f'<DIB dtc="{self.dtc}" data="{", ".join(f"0x{i:02x}" for i in self.data)}" />'


@final
class DIBDeviceInformation(DIB):
    """Class for serialization and deserialization of KNX DIB Device Information Block."""

    LENGTH = 54

    def __init__(self) -> None:
        """Initialize DIBDeviceInformation class."""
        self.knx_medium: KNXMedium = KNXMedium.TP1
        self.programming_mode: bool = False
        self.individual_address: IndividualAddress = IndividualAddress(None)
        self.installation_number: int = 0
        self.project_number: int = 0
        self.serial_number: str = ""
        self.multicast_address: str = "224.0.23.12"
        self.mac_address: str = ""
        self.name: str = ""

    def calculated_length(self) -> int:
        """Get length of KNX/IP object."""
        return DIBDeviceInformation.LENGTH

    def from_knx(self, raw: bytes) -> int:
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
        self.individual_address = IndividualAddress.from_knx(raw[4:6])
        installation_project_identifier = raw[6] * 256 + raw[7]
        self.project_number = installation_project_identifier >> 4
        self.installation_number = installation_project_identifier & 15
        self.serial_number = raw[8:14].hex(":")
        self.multicast_address = socket.inet_ntoa(raw[14:18])
        self.mac_address = raw[18:24].hex(":")
        self.name = raw[24:54].decode(encoding="latin_1", errors="replace").rstrip("\0")
        return DIBDeviceInformation.LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""

        def hex_notation_to_knx(colon_hex: str) -> bytes:
            """Serialize hex notation."""
            return bytes.fromhex(colon_hex.replace(":", ""))

        def ip_to_knx(ip_addr: str) -> bytes:
            """Serialize ip."""
            return socket.inet_aton(ip_addr)

        def name_str_to_knx(string: str) -> bytes:
            """Serialize name string."""
            # pad with null bytes to length 30; ISO 8859-1 (latin_1) according to KNX specification
            return bytes(string[:30], "latin_1").ljust(30, b"\0")

        installation_project_identifier = (
            (self.project_number * 16) + self.installation_number
        ).to_bytes(2, "big")

        return (
            bytes(
                (
                    DIBDeviceInformation.LENGTH,
                    DIBTypeCode.DEVICE_INFO.value,
                    self.knx_medium.value,
                    self.programming_mode,
                )
            )
            + self.individual_address.to_knx()
            + installation_project_identifier
            + hex_notation_to_knx(self.serial_number)
            + ip_to_knx(self.multicast_address)
            + hex_notation_to_knx(self.mac_address)
            + name_str_to_knx(self.name)
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<DIBDeviceInformation "
            f'\n\tknx_medium="{self.knx_medium}" '
            f'\n\tprogramming_mode="{self.programming_mode}" '
            f'\n\tindividual_address="{self.individual_address}" '
            f'\n\tinstallation_number="{self.installation_number}" '
            f'\n\tproject_number="{self.project_number}" '
            f'\n\tserial_number="{self.serial_number}" '
            f'\n\tmulticast_address="{self.multicast_address}" '
            f'\n\tmac_address="{self.mac_address}" '
            f'\n\tname="{self.name}" />'
        )


class _DIBServiceFamilies(DIB):
    """Base class for serialization and deserialization of KNX DIB Service Families."""

    type_code: DIBTypeCode

    class Family:
        """Class for storing a supported device family."""

        def __init__(self, name: DIBServiceFamily, version: int):
            """Initialize DIBSuppSVCFamilies.Family."""
            self.name = name
            self.version = version

        def to_knx(self) -> bytes:
            """Serialize to KNX/IP raw data."""
            return bytes((self.name.value, self.version))

        def __repr__(self) -> str:
            """Return object as readable string."""
            return f'<Family name="{self.name}" version="{self.version}" />'

        def __eq__(self, other: object) -> bool:
            """Equal operator."""
            return self.__dict__ == other.__dict__

    def __init__(self) -> None:
        """Initialize DIBSuppSVCFamilies class."""
        self.families: list[DIBSuppSVCFamilies.Family] = []

    def supports(self, name: DIBServiceFamily, version: int | None = None) -> bool:
        """Return if device supports a given service family by name and optional minimum version."""
        return any(
            name == family.name and (version is None or family.version >= version)
            for family in self.families
        )

    def version(self, name: DIBServiceFamily) -> int | None:
        """Return version of a given service family."""
        return next(
            (family.version for family in self.families if name == family.name),
            None,
        )

    def calculated_length(self) -> int:
        """Get length of KNX/IP object."""
        return len(self.families) * 2 + DIB_HEADER_LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 2:
            raise CouldNotParseKNXIP("DIB header too small")
        length = raw[0]
        if (len(raw) < length) or (length % 2):
            raise CouldNotParseKNXIP("DIB wrong size")
        if DIBTypeCode(raw[1]) != self.type_code:
            raise CouldNotParseKNXIP(
                f"DIB has wrong type code for {self.__class__.__name__}"
            )

        for pos in range(2, length, 2):
            name = DIBServiceFamily(raw[pos])
            version = raw[pos + 1]
            self.families.append(DIBSuppSVCFamilies.Family(name, version))
        return length

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return bytes(
            (
                self.calculated_length(),
                self.type_code.value,
            )
        ) + b"".join(family.to_knx() for family in self.families)

    def __repr__(self) -> str:
        """Return object as readable string."""
        _families_str = ", ".join(
            f"{family.name} version: {family.version}" for family in self.families
        )
        return f'<{self.__class__.__name__} families="[{_families_str}]" />'


@final
class DIBSuppSVCFamilies(_DIBServiceFamilies):
    """Class for serialization and deserialization of KNX DIB Supported Services."""

    type_code = DIBTypeCode.SUPP_SVC_FAMILIES


@final
class DIBSecuredServiceFamilies(_DIBServiceFamilies):
    """Class for serialization and deserialization of KNX DIB Secured Service Families."""

    type_code = DIBTypeCode.SECURED_SERVICE_FAMILIES


class TunnelingSlotStatus(NamedTuple):
    """Class for storing tunneling slot status."""

    usable: bool
    authorized: bool
    free: bool

    def __bytes__(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return bytes(
            (
                0x00,  # reserved
                self.usable << 2 | self.authorized << 1 | self.free,
            )
        )


@final
class DIBTunnelingInfo(DIB):
    """Class for serialization and deserialization of KNX DIB Tunneling Info."""

    def __init__(
        self, slots: dict[IndividualAddress, TunnelingSlotStatus] | None = None
    ) -> None:
        """Initialize DIBTunnelingInfo class."""
        self.max_apdu_length = 248
        self.slots = slots or {}

    def calculated_length(self) -> int:
        """Get length of KNX/IP object."""
        return 2 + 2 + len(self.slots) * 4

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 4:
            raise CouldNotParseKNXIP("DIB header too small")
        length = raw[0]
        if (len(raw) < length) or (length % 4):
            raise CouldNotParseKNXIP("DIB wrong size")
        if DIBTypeCode(raw[1]) != DIBTypeCode.TUNNELING_INFO:
            raise CouldNotParseKNXIP(
                f"DIB has wrong type code for {self.__class__.__name__}"
            )

        self.max_apdu_length = int.from_bytes(raw[2:4], "big")
        for pos in range(4, length, 4):
            address = IndividualAddress.from_knx(raw[pos : pos + 2])
            status = TunnelingSlotStatus(
                usable=bool(raw[pos + 3] >> 2 & 0b1),
                authorized=bool(raw[pos + 3] >> 1 & 0b1),
                free=bool(raw[pos + 3] & 0b1),
            )
            self.slots[address] = status
        return length

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            bytes((self.calculated_length(), DIBTypeCode.TUNNELING_INFO.value))
            + self.max_apdu_length.to_bytes(2, "big")
            + b"".join(
                address.to_knx() + bytes(status)
                for address, status in self.slots.items()
            )
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            f"<{self.__class__.__name__} max_adpu_lenght={self.max_apdu_length} "
            f"slots={self.slots}/>"
        )
