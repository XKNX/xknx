"""
Module for handling Search Request Parameters (SRP).

This can be used e.g. to restrict the set of devices that are expected to respond or to influence the type of DIBs
which the client is interested in.

If the M (Mandatory) bit is set, the server shall only respond to the search request if the complete SRP block
is satisfied.
"""
from __future__ import annotations

from xknx.exceptions import ConversionError, CouldNotParseKNXIP

from .knxip_enum import DIBServiceFamily, DIBTypeCode, SearchRequestParameterType


class SRP:
    """Search request parameter for a SearchRequestExtended."""

    SRP_HEADER_SIZE = 2
    MANDATORY_BIT_INDEX = 0x07

    # service family and service version have 1 byte each
    SERVICE_PAYLOAD_LENGTH = 2
    # mac address has 6 bytes
    MAC_ADDRESS_PAYLOAD_LENGTH = 6

    def __init__(
        self,
        srp_type: SearchRequestParameterType,
        mandatory: bool = True,
        data: bytes = b"",
    ):
        """Initialize a SRP."""
        self.type = srp_type
        self.mandatory = mandatory
        self.data = data
        self.payload_size = SRP.SRP_HEADER_SIZE

        if self.type == SearchRequestParameterType.SELECT_BY_SERVICE:
            self.validate_payload_length(SRP.SERVICE_PAYLOAD_LENGTH)
            self.payload_size = SRP.SRP_HEADER_SIZE + SRP.SERVICE_PAYLOAD_LENGTH
        elif self.type == SearchRequestParameterType.SELECT_BY_MAC_ADDRESS:
            self.validate_payload_length(SRP.MAC_ADDRESS_PAYLOAD_LENGTH)
            self.payload_size = SRP.SRP_HEADER_SIZE + SRP.MAC_ADDRESS_PAYLOAD_LENGTH
        elif self.type == SearchRequestParameterType.REQUEST_DIBS:
            if not self.data:
                raise ConversionError("Srp DIBs are not present.")
            # If the Client is interested in an odd number of DIBs
            # it shall add an additional Description Type 0 to make the structure length even
            if len(self.data) % 2:
                self.data += bytes([0])
            self.payload_size = SRP.SRP_HEADER_SIZE + len(self.data)

    def validate_payload_length(self, size: int) -> None:
        """Validate the length of the payload."""
        if not self.data or len(self.data) != size:
            raise ConversionError(
                "Srp parameter payload size does not match.",
                expected_size=size,
                srp_type=self.type,
            )

    def __len__(self) -> int:
        """Get the payload length."""
        return self.payload_size

    def __bytes__(self) -> bytes:
        """Convert this SRP to a bytes object."""
        return (
            bytes(
                [
                    self.payload_size,
                    (
                        self.mandatory << SRP.MANDATORY_BIT_INDEX
                        | self.type.value & SRP.MANDATORY_BIT_INDEX
                    ),
                ]
            )
            + self.data
        )

    @staticmethod
    def from_knx(data: bytes) -> SRP:
        """Convert the bytes to a SRP object."""
        if len(data) < SRP.SRP_HEADER_SIZE:
            raise CouldNotParseKNXIP("Data too short for SRP object.")

        size: int = data[0]
        if size > len(data):
            raise CouldNotParseKNXIP("SRP is larger than actual data size.")

        return SRP(
            srp_type=SearchRequestParameterType(data[1] & 0x7F),
            mandatory=bool(data[1] >> SRP.MANDATORY_BIT_INDEX),
            data=data[2:size],
        )

    @staticmethod
    def with_programming_mode() -> SRP:
        """Create a SRP that limits the response to only devices that are currently in programming mode."""
        return SRP(
            srp_type=SearchRequestParameterType.SELECT_BY_PROGRAMMING_MODE,
            mandatory=True,
        )

    @staticmethod
    def with_mac_address(mac_address: bytes) -> SRP:
        """
        Create a SRP that limits the response to only allow a device with the given MAC address.

        :param mac_address: The mac address to restrict this SRP to
        """
        return SRP(
            srp_type=SearchRequestParameterType.SELECT_BY_MAC_ADDRESS,
            mandatory=True,
            data=mac_address,
        )

    @staticmethod
    def with_service(family: DIBServiceFamily, family_version: int) -> SRP:
        """
        Create a SRP that limits the response to only allow devices that support the given service family.

        :param family: DIBServiceFamily that this SRP should be limited to
        :param family_version: The minimum family version so that devices will send a search response extended back
        :return: Srp with the given parameter
        """
        return SRP(
            srp_type=SearchRequestParameterType.SELECT_BY_SERVICE,
            mandatory=True,
            data=bytes([family.value, family_version]),
        )

    @staticmethod
    def request_device_description(dibs: list[DIBTypeCode]) -> SRP:
        """
        Create a SRP with a list of DIBs the server shall include in the response.

        The server may include in addition any number of other DIBs in the response.
        The server shall ignore Description types that are not recognized or not supported.

        :param dibs: the description types to include in the SRP
        :return: Srp with given parameters
        """
        return SRP(
            srp_type=SearchRequestParameterType.REQUEST_DIBS,
            mandatory=False,
            data=bytes(dib.value for dib in dibs),
        )

    def __eq__(self, other: object) -> bool:
        """Define equality for SRPs."""
        if not isinstance(other, SRP):
            return False

        return (
            self.payload_size == other.payload_size
            and self.type == other.type
            and self.mandatory == other.mandatory
            and self.data == other.data
        )
