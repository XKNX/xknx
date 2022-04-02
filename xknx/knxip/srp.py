"""
Module for handling Search Request Parameters (SRP).

This can be used e.g. to restrict the set of devices that are expected to respond or to influence the type of DIBs
which the client is interested in.

If the M (Mandatory) bit is set, the server shall only respond to the search request if the complete SRP block
is satisfied.
"""
from __future__ import annotations

from ..exceptions import ConversionError
from .knxip_enum import DIBServiceFamily, DIBTypeCode, SearchRequestParameterType


class Srp:
    """Search request parameter for a search request extended."""

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
        data: bytes = bytes(),
    ):
        """Initialize a SRP."""
        self.type = srp_type
        self.mandatory = mandatory
        self.data = data
        self.payload_size = Srp.SRP_HEADER_SIZE

        if self.type == SearchRequestParameterType.SELECT_BY_SERVICE:
            self.validate_payload_length(Srp.SERVICE_PAYLOAD_LENGTH)
            self.payload_size = Srp.SRP_HEADER_SIZE + Srp.SERVICE_PAYLOAD_LENGTH
        elif self.type == SearchRequestParameterType.SELECT_BY_MAC_ADDRESS:
            self.validate_payload_length(Srp.MAC_ADDRESS_PAYLOAD_LENGTH)
            self.payload_size = Srp.SRP_HEADER_SIZE + Srp.MAC_ADDRESS_PAYLOAD_LENGTH
        elif self.type == SearchRequestParameterType.REQUEST_DIBS:
            if not self.data or len(self.data) < 1:
                raise ConversionError("Srp DIBs are not present.")
            # If the Client is interested in an odd number of DIBs
            # it shall add an additional Description Type 0 to make the structure length even
            if len(self.data) % 2:
                self.data = self.data + bytes([0])
            self.payload_size = Srp.SRP_HEADER_SIZE + len(self.data)

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
                        self.mandatory << Srp.MANDATORY_BIT_INDEX
                        | self.type.value & Srp.MANDATORY_BIT_INDEX
                    ),
                ]
            )
            + self.data
        )

    @staticmethod
    def from_knx(data: bytes) -> Srp:
        """Convert the bytes to a SRP object."""
        if len(data) < Srp.SRP_HEADER_SIZE:
            raise ConversionError("Data too short for SRP object.")

        size: int = data[0] & 0xFF
        if size > len(data):
            raise ConversionError("SRP is larger than actual data size.")

        return Srp(
            SearchRequestParameterType(data[1] & 0x7F),
            bool(data[1] >> Srp.MANDATORY_BIT_INDEX),
            data[2:size],
        )

    @staticmethod
    def with_programming_mode() -> Srp:
        """Create a SRP that limits the response to only devices that are currently in programming mode."""
        return Srp(SearchRequestParameterType.SELECT_BY_PROGRAMMING_MODE, True)

    @staticmethod
    def with_mac_address(mac_address: bytes) -> Srp:
        """
        Create a SRP that limits the response to only allow a device with the given MAC address.

        :param mac_address: The mac address to restrict this SRP to
        """
        return Srp(SearchRequestParameterType.SELECT_BY_MAC_ADDRESS, True, mac_address)

    @staticmethod
    def with_service(family: DIBServiceFamily, family_version: int) -> Srp:
        """
        Create a SRP that limits the response to only allow devices that support the given service family.

        :param family: DIBServiceFamily that this SRP should be limited to
        :param family_version: The minimum family version so that devices will send a search response extended back
        :return: Srp with the given parameter
        """
        return Srp(
            SearchRequestParameterType.SELECT_BY_SERVICE,
            True,
            bytes([family.value, family_version]),
        )

    @staticmethod
    def with_device_description(dibs: list[DIBTypeCode]) -> Srp:
        """
        Create a SRP with a list of DIBs to indicate the server that it should, at least, include.

        :param dibs: the description types to include in the SRP
        :return: Srp with given parameters
        """
        return Srp(
            SearchRequestParameterType.REQUEST_DIBS,
            True,
            bytes(dib.value for dib in dibs),
        )

    def __eq__(self, other: object) -> bool:
        """Define equality for SRPs."""
        if not isinstance(other, Srp):
            return False

        return (
            self.payload_size == other.payload_size
            and self.type == other.type
            and self.mandatory == other.mandatory
            and self.data == other.data
        )
