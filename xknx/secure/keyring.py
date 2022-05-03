"""Keyring class for loading and decrypting knxkeys files."""
from __future__ import annotations

import abc
from abc import ABC
import base64
import enum
from itertools import chain
import logging
from typing import Any
from xml.dom.minidom import Attr, Document, parse
from xml.etree.ElementTree import Element, ElementTree
import xml.sax
from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import AttributesImpl

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from xknx.exceptions.exception import InvalidSecureConfiguration, InvalidSignature
from xknx.telegram import GroupAddress, IndividualAddress

from .util import sha256_hash

logger = logging.getLogger("xknx.core")


class InterfaceType(enum.Enum):
    """Interface type enum."""

    TUNNELING = "Tunneling"
    BACKBONE = "Backbone"
    USB = "USB"


class AttributeReader(ABC):
    """Abstract base class for modelling attribute reader capabilities."""

    @abc.abstractmethod
    def parse_xml(self, node: Document) -> None:
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

    def parse_xml(self, node: Document) -> None:
        """Parse all needed attributes from the given node map."""
        attributes = node.attributes
        self.address = GroupAddress(
            self.get_attribute_value(attributes.get("Address", None))
        )
        self.senders = str(
            self.get_attribute_value(attributes.get("Senders", ""))
        ).split(" ")


class XMLInterface(AttributeReader):
    """Interface in a knxkeys file."""

    type: InterfaceType
    host: IndividualAddress
    user_id: int
    password: str
    decrypted_password: str
    decrypted_authentication: str
    individual_address: IndividualAddress
    authentication: str
    group_addresses: list[XMLAssignedGroupAddress] = []

    def parse_xml(self, node: Document) -> None:
        """Parse all needed attributes from the given node map."""
        attributes = node.attributes
        self.type = InterfaceType(self.get_attribute_value(attributes.get("Type")))
        self.host = IndividualAddress(self.get_attribute_value(attributes.get("Host")))
        self.user_id = int(self.get_attribute_value(attributes.get("UserID")) or 2)
        self.password = self.get_attribute_value(attributes.get("Password"))
        self.individual_address = IndividualAddress(
            self.get_attribute_value(attributes.get("IndividualAddress"))
        )
        self.authentication = self.get_attribute_value(attributes.get("Authentication"))

        for assigned_ga in filter(lambda x: x.nodeType != 3, node.childNodes):
            group_address: XMLAssignedGroupAddress = XMLAssignedGroupAddress()
            group_address.parse_xml(assigned_ga)
            self.group_addresses.append(group_address)

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

        if self.authentication is not None:
            self.decrypted_authentication = extract_password(
                decrypt_aes128cbc(
                    base64.b64decode(self.authentication),
                    password_hash,
                    initialization_vector,
                )
            )


class XMLBackbone(AttributeReader):
    """Backbone in a knxkeys file."""

    multicast_address: str
    key: str
    decrypted_key: bytes

    def parse_xml(self, node: Document) -> None:
        """Parse all needed attributes from the given node map."""
        attributes = node.attributes
        self.multicast_address = self.get_attribute_value(
            attributes.get("MulticastAddress")
        )
        self.key = self.get_attribute_value(attributes.get("Key"))

    def decrypt_attributes(
        self, password_hash: bytes, initialization_vector: bytes
    ) -> None:
        """Decrypt attribute data."""
        if self.key:
            self.decrypted_key = decrypt_aes128cbc(
                base64.b64decode(self.key), password_hash, initialization_vector
            )


class XMLGroupAddress(AttributeReader):
    """Group Address in a knxkeys file."""

    address: GroupAddress
    key: str

    def parse_xml(self, node: Document) -> None:
        """Parse all needed attributes from the given node map."""
        attributes = node.attributes
        self.address = GroupAddress(self.get_attribute_value(attributes.get("Address")))
        self.key = self.get_attribute_value(attributes.get("Key"))


class XMLDevice(AttributeReader):
    """Device in a knxkeys file."""

    individual_address: IndividualAddress
    tool_key: str
    decrypted_tool_key: bytes
    management_password: str
    decrypted_management_password: str
    decrypted_authentication: str
    authentication: str
    sequence_number: int

    def parse_xml(self, node: Document) -> None:
        """Parse all needed attributes from the given node map."""
        attributes = node.attributes
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
        if self.tool_key is not None:
            self.decrypted_tool_key = decrypt_aes128cbc(
                base64.b64decode(self.tool_key), password_hash, initialization_vector
            )

        if self.authentication is not None:
            self.decrypted_authentication = extract_password(
                decrypt_aes128cbc(
                    base64.b64decode(self.authentication),
                    password_hash,
                    initialization_vector,
                )
            )

        if self.management_password is not None:
            self.decrypted_management_password = extract_password(
                decrypt_aes128cbc(
                    base64.b64decode(self.management_password),
                    password_hash,
                    initialization_vector,
                )
            )


class Keyring(AttributeReader):
    """Class for loading and decrypting knxkeys XML files."""

    backbone: XMLBackbone
    interfaces: list[XMLInterface]
    group_addresses: list[XMLGroupAddress]
    devices: list[XMLDevice]
    created_by: str
    created: str
    signature: bytes
    xmlns: str

    def __init__(self) -> None:
        """Initialize the Keyring."""
        self.interfaces = []
        self.devices = []
        self.group_addresses = []

    def get_device_by_interface(self, interface: XMLInterface) -> XMLDevice | None:
        """Get the device for a given interface."""
        for device in self.devices:
            if device.individual_address == interface.host:
                return device

        return None

    def get_interface_by_user_id(self, user_id: int) -> XMLInterface | None:
        """Get the interface with the given user id."""
        for interface in self.interfaces:
            if interface.user_id == user_id:
                return interface

        return None

    def parse_xml(self, node: Document) -> None:
        """Parse all needed attributes from the given node map."""
        attributes = node.attributes
        self.created_by = self.get_attribute_value(attributes.get("CreatedBy"))
        self.created = self.get_attribute_value(attributes.get("Created"))
        self.signature = base64.b64decode(
            self.get_attribute_value(attributes.get("Signature"))
        )
        self.xmlns = self.get_attribute_value(attributes.get("xmlns"))

        for sub_node in filter(lambda x: x.nodeType != 3, node.childNodes):
            if sub_node.nodeName == "Interface":
                interface: XMLInterface = XMLInterface()
                interface.parse_xml(sub_node)
                if interface.password is not None:
                    self.interfaces.append(interface)
            if sub_node.nodeName == "Backbone":
                backbone: XMLBackbone = XMLBackbone()
                backbone.parse_xml(sub_node)
                self.backbone = backbone
            if sub_node.nodeName == "GroupAddresses":
                ga_doc: Document
                for ga_doc in filter(lambda x: x.nodeType != 3, sub_node.childNodes):
                    xml_ga: XMLGroupAddress = XMLGroupAddress()
                    xml_ga.parse_xml(ga_doc)
                    self.group_addresses.append(xml_ga)
            if sub_node.nodeName == "Devices":
                device_doc: Document
                for device_doc in filter(
                    lambda x: x.nodeType != 3, sub_node.childNodes
                ):
                    device: XMLDevice = XMLDevice()
                    device.parse_xml(device_doc)
                    self.devices.append(device)

    def decrypt(self, password: str) -> None:
        """Decrypt all data."""
        hashed_password = hash_keyring_password(password.encode("utf-8"))
        initialization_vector = sha256_hash(self.created.encode("utf-8"))[:16]

        for xml_element in chain(self.interfaces, self.group_addresses, self.devices):
            xml_element.decrypt_attributes(hashed_password, initialization_vector)

        if self.backbone is not None:
            self.backbone.decrypt_attributes(hashed_password, initialization_vector)


def load_key_ring(path: str, password: str, validate_signature: bool = True) -> Keyring:
    """Load a .knxkeys file from the given path."""

    if validate_signature:
        if not verify_keyring_signature(path, password):
            raise InvalidSignature()

    keyring: Keyring = Keyring()
    try:
        with open(path, encoding="utf-8") as file:
            dom: Document = parse(file)
            keyring.parse_xml(dom.getElementsByTagName("Keyring")[0])

        keyring.decrypt(password)

        return keyring
    except Exception as exception:
        logger.exception("There was an error during loading the knxkeys file.")
        raise InvalidSecureConfiguration() from exception


class KeyringSAXContentHandler(ContentHandler):
    """SAX parser for keyring signature verification."""

    _attribute_blacklist = ["xmlns", "Signature"]

    def __init__(self, keyring_password: str):
        """Initialize."""
        self.hashed_password = hash_keyring_password(keyring_password.encode("utf-8"))
        self.output = bytearray()
        super().__init__()

    def endDocument(self) -> None:
        """Receive notification of the end of a document."""
        self.append_string(base64.b64encode(self.hashed_password))

    def startElement(self, name: str, attrs: AttributesImpl) -> None:
        """Start Element."""
        self.output.append(1)
        self.append_string(name)

        for attr_name, attr_value in sorted(attrs.items()):  # type: ignore[no-untyped-call]
            if attr_name not in self._attribute_blacklist:
                self.append_string(attr_name)
                self.append_string(attr_value)

    def endElement(self, name: str) -> None:
        """Receive notification of the end of an element."""
        self.output.append(2)

    def append_string(self, value: str | bytes) -> None:
        """Append a string to a byte array for signature verification."""
        self.output.append(len(value))

        if isinstance(value, str):
            self.output.extend(value.encode("utf-8"))
        if isinstance(value, bytes):
            self.output.extend(value)


def verify_keyring_signature(path: str, password: str) -> bool:
    """Verify the signature of the given knxkeys file."""
    handler = KeyringSAXContentHandler(password)
    signature: bytes
    with open(path, encoding="utf-8") as file:
        element: Element = ElementTree().parse(file)
        signature = base64.b64decode(element.attrib.get("Signature", ""))

    with open(path, encoding="utf-8") as file:
        parser = xml.sax.make_parser()
        parser.setContentHandler(handler)  # type: ignore[no-untyped-call]
        parser.parse(file)  # type: ignore[no-untyped-call]

    return sha256_hash(handler.output)[:16] == signature


def decrypt_aes128cbc(
    encrypted_data: bytes, key: bytes, initialization_vector: bytes
) -> bytes:
    """Decrypt data with AES 128 CBC."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(initialization_vector))
    decryptor = cipher.decryptor()
    return bytes(decryptor.update(encrypted_data) + decryptor.finalize())


def hash_keyring_password(password: bytes) -> bytes:
    """Hash a given keyring password."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=16,
        salt=b"1.keyring.ets.knx.org",
        iterations=65_536,
    )

    return kdf.derive(password)


def extract_password(data: bytes) -> str:
    """Extract the password."""
    if not data:
        return ""

    length: int = data[-1]
    res: bytes = data[8:-length]
    return res.decode("utf-8")
