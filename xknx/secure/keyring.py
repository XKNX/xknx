"""Keyring class for loading and decrypting knxkeys files."""
from __future__ import annotations

import abc
from abc import ABC
import base64
import enum
from itertools import chain
from typing import Any
from xml.dom.minidom import Attr, Document, NamedNodeMap, parse

from xknx.telegram import GroupAddress, IndividualAddress

from .util import (
    decrypt_aes128cbc,
    extract_password,
    hash_keyring_password,
    sha256_hash,
)


class InterfaceType(enum.Enum):
    """Interface type enum."""

    TUNNELING = "Tunneling"
    BACKBONE = "Backbone"
    USB = "USB"


class AttributeReader(ABC):
    """Abstract base class for modelling attribute reader capabilities."""

    @abc.abstractmethod
    def parse_attributes(self, attributes: NamedNodeMap) -> None:
        """Parse all needed attributes from the given node map."""

    def decrypt_attributes(
        self, password_hash: bytes, initialization_vector: bytes
    ) -> None:
        """Decrypt attribute data."""

    @staticmethod
    def get_attribute_value(attribute: Attr | Any) -> Any:
        """Get a given attribute value from an attribute document."""
        if isinstance(attribute, Attr):
            return attribute.value

        return attribute


class XMLAssignedGroupAddress(AttributeReader):
    """Assigned Group Addresses to an interface in a knxkeys file."""

    address: GroupAddress
    senders: list[str]

    def parse_attributes(self, attributes: NamedNodeMap) -> None:
        """Parse all needed attributes from the given node map."""
        self.address = GroupAddress(
            self.get_attribute_value(attributes.get("Address", None))
        )
        self.senders = str(
            self.get_attribute_value(attributes.get("Senders", ""))
        ).split(" ")


class XMLInterface(AttributeReader):
    """Interface in a knxkeys file."""

    type: InterfaceType
    host: str
    user_id: int
    password: str
    decrypted_password: str
    individual_address: IndividualAddress
    authentication: str
    group_addresses: list[XMLAssignedGroupAddress] = []

    def parse_attributes(self, attributes: NamedNodeMap) -> None:
        """Parse all needed attributes from the given node map."""

        self.type = InterfaceType(self.get_attribute_value(attributes.get("Type")))
        self.host = self.get_attribute_value(attributes.get("Host"))
        self.user_id = self.get_attribute_value(attributes.get("UserID"))
        self.password = self.get_attribute_value(attributes.get("Password"))
        self.individual_address = IndividualAddress(
            self.get_attribute_value(attributes.get("IndividualAddress"))
        )
        self.authentication = self.get_attribute_value(attributes.get("Authentication"))

    def decrypt_attributes(
        self, password_hash: bytes, initialization_vector: bytes
    ) -> None:
        """Decryt attributes."""

        if self.password is not None:
            self.decrypted_password = extract_password(
                decrypt_aes128cbc(
                    base64.b64decode(self.password),
                    password_hash,
                    initialization_vector,
                )
            )


class XMLBackbone(AttributeReader):
    """Backbone in a knxkeys file."""

    multicast_address: str
    latency: int
    key: str
    decrypted_key: bytes

    def parse_attributes(self, attributes: NamedNodeMap) -> None:
        """Parse all needed attributes from the given node map."""
        self.multicast_address = self.get_attribute_value(
            attributes.get("MulticastAddress")
        )
        self.latency = int(self.get_attribute_value(attributes["Latency"]))
        self.key = self.get_attribute_value(attributes.get("Key"))

    def decrypt_attributes(
        self, password_hash: bytes, initialization_vector: bytes
    ) -> None:
        """Decrypt attribute data."""
        self.decrypted_key = decrypt_aes128cbc(
            base64.b64decode(self.key), password_hash, initialization_vector
        )


class XMLGroupAddress(AttributeReader):
    """Group Address in a knxkeys file."""

    address: GroupAddress
    key: str

    def parse_attributes(self, attributes: NamedNodeMap) -> None:
        """Parse all needed attributes from the given node map."""
        self.address = GroupAddress(self.get_attribute_value(attributes.get("Address")))
        self.key = self.get_attribute_value(attributes.get("Key"))


class XMLDevice(AttributeReader):
    """Device in a knxkeys file."""

    individual_address: IndividualAddress
    tool_key: str
    decrypted_tool_key: bytes
    management_password: str
    decrypted_management_password: str
    authentication: str
    sequence_number: int

    def parse_attributes(self, attributes: NamedNodeMap) -> None:
        """Parse all needed attributes from the given node map."""
        self.individual_address = IndividualAddress(
            self.get_attribute_value(attributes.get("IndividualAddress"))
        )
        self.tool_key = self.get_attribute_value(attributes.get("ToolKey"))
        self.management_password = self.get_attribute_value(
            attributes.get("ManagementPassword")
        )
        self.authentication = self.get_attribute_value(attributes.get("Authentication"))
        self.sequence_number = int(
            self.get_attribute_value(attributes.get("SequenceNumber", 0))
        )

    def decrypt_attributes(
        self, password_hash: bytes, initialization_vector: bytes
    ) -> None:
        """Decrypt attributes."""
        self.decrypted_tool_key = decrypt_aes128cbc(
            base64.b64decode(self.tool_key), password_hash, initialization_vector
        )


class Keyring(AttributeReader):
    """Class for loading and decrypting knxkeys XML files."""

    backbone: XMLBackbone
    interfaces: list[XMLInterface] = []
    group_addresses: list[XMLGroupAddress] = []
    devices: list[XMLDevice] = []
    created_by: str
    created: str
    signature: bytes
    xmlns: str

    def parse_attributes(self, attributes: NamedNodeMap) -> None:
        """Parse all needed attributes from the given node map."""
        self.created_by = self.get_attribute_value(attributes.get("CreatedBy"))
        self.created = self.get_attribute_value(attributes.get("Created"))
        self.signature = base64.b64decode(
            self.get_attribute_value(attributes.get("Signature"))
        )
        self.xmlns = self.get_attribute_value(attributes.get("xmlns"))

    def decrypt(self, password: str) -> None:
        """Decrypt all data."""
        hashed_password = hash_keyring_password(password.encode("utf-8"))
        initialization_vector = sha256_hash(self.created.encode("utf-8"))[:16]

        for xml_element in chain(self.interfaces, self.group_addresses, self.devices):
            xml_element.decrypt_attributes(hashed_password, initialization_vector)

        if self.backbone is not None:
            self.backbone.decrypt_attributes(hashed_password, initialization_vector)


def load_key_ring(path: str, password: str) -> Keyring:
    """Load a .knxkeys file from the given path."""

    keyring: Keyring = Keyring()
    with open(path, encoding="utf-8") as file:
        xml: Document = parse(file)
        node: Document
        # root node - keyring
        for node in xml.childNodes:
            attributes: NamedNodeMap = node.attributes
            keyring.parse_attributes(attributes)

            sub_node: Document
            for sub_node in filter(lambda x: x.nodeType != 3, node.childNodes):
                if sub_node.nodeName == "Interface":
                    interface: XMLInterface = XMLInterface()
                    interface.parse_attributes(sub_node.attributes)
                    assigned_ga: Document
                    for assigned_ga in filter(
                        lambda x: x.nodeType != 3, sub_node.childNodes
                    ):
                        group_address: XMLAssignedGroupAddress = (
                            XMLAssignedGroupAddress()
                        )
                        group_address.parse_attributes(assigned_ga.attributes)
                        interface.group_addresses.append(group_address)

                    keyring.interfaces.append(interface)
                if sub_node.nodeName == "Backbone":
                    backbone: XMLBackbone = XMLBackbone()
                    backbone.parse_attributes(sub_node.attributes)
                    keyring.backbone = backbone
                if sub_node.nodeName == "GroupAddresses":
                    ga_doc: Document
                    for ga_doc in filter(
                        lambda x: x.nodeType != 3, sub_node.childNodes
                    ):
                        xml_ga: XMLGroupAddress = XMLGroupAddress()
                        xml_ga.parse_attributes(ga_doc.attributes)
                        keyring.group_addresses.append(xml_ga)
                if sub_node.nodeName == "Devices":
                    device_doc: Document
                    for device_doc in filter(
                        lambda x: x.nodeType != 3, sub_node.childNodes
                    ):
                        device: XMLDevice = XMLDevice()
                        device.parse_attributes(device_doc.attributes)
                        keyring.devices.append(device)

    keyring.decrypt(password)
    return keyring
