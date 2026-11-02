#!/usr/bin/env python3
"""
Proof of concept: a KNXnet/IP Tunnelling Server with KNX IP Secure, built from xknx parts.

Why
---
A secure client (ETS) encrypts everything after the SESSION_RESPONSE, so Wireshark shows
only SECURE_WRAPPER frames. This script *is* the server, so it knows the session key and
logs every frame decrypted: discovery, the secure session handshake, device management
(cEMI M_Prop*), tunnelling (cEMI L_Data) and all timers/acks in between.

What it implements (KNX Standard v3.0.2, Vol 3 Part 8)
-----------------------------------------------------
* Core v2 discovery over UDP: SEARCH_REQUEST(_EXTENDED) with SRP evaluation,
  DESCRIPTION_REQUEST (03_08_02).
* KNXnet/IP Secure session over TCP: SESSION_REQUEST/RESPONSE (Curve25519 ECDH, device
  authentication code MAC), SESSION_AUTHENTICATE (user password MAC), SESSION_STATUS,
  SECURE_WRAPPER (AES-128 CCM), authentication timeout 10 s, session timeout 60 s
  (03_08_09 §2.2.3, §2.4).
* Inside the session: CONNECT/CONNECTIONSTATE/DISCONNECT for TUNNEL_CONNECTION and
  DEVICE_MGMT_CONNECTION, extended CRI with requested individual address (03_08_04 §4.2),
  TUNNELLING_REQUEST/ACK, TUNNELLING_FEATURE_GET/SET, DEVICE_CONFIGURATION_REQUEST/ACK
  with a small property store for the Device Object and the KNXnet/IP Parameter Object.
* A "virtual bus": every L_Data.req is confirmed with L_Data.con and distributed as
  L_Data.ind to the other tunnelling connections. Optionally (--backend) frames are
  bridged to a real KNX installation through a normal xknx connection.

Usage
-----
    python3 examples/poc_ip_secure_server.py --ip 192.168.1.50 \
        --device-auth MyAuthCode --user 1:MyCommissioningPw --user 2:TunnelPw1

Then in ETS: Bus > Interfaces: the server shows up as "xknx PoC Secure Server"
(discovered via multicast). Enter the device authentication code and the password.
Watch the console: every step ETS takes is logged in plain text.

This is a proof of concept for protocol observation, not a product: no persistence, no
real access control lists, no busmonitor mode, IPv4 only.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from enum import Enum
import hmac
import logging
import secrets
import socket
import sys
import time
from typing import Any

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey

from xknx import XKNX
from xknx.cemi import (
    CEMIFrame,
    CEMILData,
    CEMIMessageCode,
    CEMIMPropInfo,
    CEMIMPropReadRequest,
    CEMIMPropReadResponse,
    CEMIMPropWriteRequest,
    CEMIMPropWriteResponse,
)
from xknx.exceptions import (
    CommunicationError,
    CouldNotParseCEMI,
    CouldNotParseKNXIP,
    IncompleteKNXIPFrame,
    UnsupportedCEMIMessage,
)
from xknx.io import ConnectionConfig, ConnectionType
from xknx.io.transport import UDPTransport
from xknx.io.util import get_default_local_ip
from xknx.knxip import (
    HPAI,
    ConnectionStateRequest,
    ConnectionStateResponse,
    ConnectRequest,
    ConnectRequestType,
    ConnectResponse,
    ConnectResponseData,
    DescriptionRequest,
    DescriptionResponse,
    DeviceConfigurationAck,
    DeviceConfigurationRequest,
    DIBDeviceInformation,
    DIBGeneric,
    DIBSecuredServiceFamilies,
    DIBServiceFamily,
    DIBSuppSVCFamilies,
    DIBTypeCode,
    DisconnectRequest,
    DisconnectResponse,
    ErrorCode,
    HostProtocol,
    KNXIPFrame,
    KNXIPHeader,
    KNXMedium,
    SearchRequest,
    SearchRequestExtended,
    SearchRequestParameterType,
    SearchResponse,
    SearchResponseExtended,
    SecureWrapper,
    SessionAuthenticate,
    SessionRequest,
    SessionResponse,
    SessionStatus,
    TunnellingAck,
    TunnellingFeatureGet,
    TunnellingFeatureResponse,
    TunnellingFeatureSet,
    TunnellingFeatureType,
    TunnellingLayer,
    TunnellingRequest,
)
from xknx.knxip.knxip_enum import SecureSessionStatusCode
from xknx.profile.const import (
    ResourceDevicePropertyId,
    ResourceGenericPropertyId,
    ResourceKNXNETIPPropertyId,
    ResourceObjectType,
)
from xknx.secure.security_primitives import (
    calculate_message_authentication_code_cbc,
    decrypt_ctr,
    derive_device_authentication_password,
    derive_user_password,
    encrypt_data_ctr,
    generate_ecdh_key_pair,
)
from xknx.secure.util import bytes_xor, sha256_hash
from xknx.telegram import IndividualAddress
from xknx.telegram.apci import ReturnCode

log = logging.getLogger("poc")

KNXIP_PORT = 3671
MULTICAST_GROUP = "224.0.23.12"

# 03_08_09 §2.2.3.5.2.1.1
TIMEOUT_AUTHENTICATION = 10
TIMEOUT_SESSION = 60
# 03_08_02 §5.4 / §7.8: connection is dropped after 120 s without CONNECTIONSTATE_REQUEST
CONNECTION_ALIVE_TIME = 120

# Counter block 0 used for the MAC of SESSION_RESPONSE and SESSION_AUTHENTICATE
# 03_08_09 §2.2.3.7.4 Figure 17 / §2.2.3.8.4
COUNTER_0_HANDSHAKE = bytes(14) + b"\xff\x00"
# unicast message tag shall be 0000h - 03_08_09 §2.2.1.3.1
MESSAGE_TAG_UNICAST = bytes(2)

# Interface feature "Supported EMI type" bitset: bit 2 = cEMI
SUPPORTED_EMI_CEMI = 0x0004
ACTIVE_EMI_CEMI = 0x03
DEVICE_DESCRIPTOR_KNX_IP_SYSTEM_B = 0x57B0

# PDT sizes of the interface features (Tunnelling v2, 03_08_04 §3)
FEATURE_SIZE = {
    TunnellingFeatureType.SUPPORTED_EMI_TYPE: 2,
    TunnellingFeatureType.DEVICE_DESCRIPTOR_TYPE_0: 2,
    TunnellingFeatureType.BUS_CONNECTION_STATUS: 1,
    TunnellingFeatureType.MANUFACTURER_CODE: 2,
    TunnellingFeatureType.ACTIVE_EMI_TYPE: 1,
    TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS: 2,
    TunnellingFeatureType.MAX_APDU_LENGTH: 2,
    TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE: 1,
}


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class ServerConfig:
    """Static description of the simulated KNXnet/IP device."""

    local_ip: str
    port: int = KNXIP_PORT
    name: str = "xknx PoC Secure Server"
    serial_number: bytes = bytes.fromhex("0000786b6e78")  # 00 00 'x' 'k' 'n' 'x'
    mac_address: bytes = bytes.fromhex("02786b6e7800")
    manufacturer_id: int = 0x0000
    individual_address: IndividualAddress = field(
        default_factory=lambda: IndividualAddress("15.15.0")
    )
    tunnel_addresses: list[IndividualAddress] = field(default_factory=list)
    max_apdu_length: int = 248
    device_authentication_password: str = "authcode"
    # user id -> password. 1 is the management (commissioning) user.
    user_passwords: dict[int, str] = field(default_factory=dict)
    # password tried for user ids that are not configured (None = reject)
    any_user_password: str | None = None
    # security required for tunnelling / device management (PID_SECURED_SERVICE_FAMILIES)
    secure_tunnelling: bool = True
    secure_device_management: bool = True


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------


def fmt_frame(frame: KNXIPFrame) -> str:
    """One-line representation of a frame."""
    return f"{frame.header.service_type_ident.name} {frame.body}"


def enum_name(enum_cls: type[Enum], value: int) -> str:
    """Name of an enum member for the log, or the raw value if unknown."""
    try:
        return enum_cls(value).name
    except ValueError:
        return f"{value:#04x}"


def describe_cemi(raw: bytes) -> str:
    """Decode a cEMI frame for the log."""
    try:
        cemi = CEMIFrame.from_knx(raw)
    except (CouldNotParseCEMI, UnsupportedCEMIMessage) as err:
        code = f"{raw[0]:#04x}" if raw else "-"
        return f"cEMI code={code} (not decoded: {err}) raw={raw.hex()}"
    text = repr(cemi)
    if isinstance(cemi.data, CEMILData):
        try:
            text += f"\n            telegram: {cemi.data.telegram()}"
        except Exception as err:  # pylint: disable=broad-except
            text += f" (telegram not decodable: {err})"
    return text


# ---------------------------------------------------------------------------
# DIB / discovery helpers
# ---------------------------------------------------------------------------


def ip_bytes(ip: str) -> bytes:
    """IPv4 string to 4 bytes."""
    return socket.inet_aton(ip)


def generic_dib(dtc: DIBTypeCode, data: bytes) -> DIBGeneric:
    """Build a DIB xknx has no dedicated class for."""
    dib = DIBGeneric()
    dib.dtc = dtc
    dib.data = data
    return dib


class DeviceDescription:
    """Builds the DIBs the server announces."""

    def __init__(self, config: ServerConfig, server: SecureServer) -> None:
        """Initialize."""
        self.config = config
        self.server = server

    def device_info(self) -> DIBDeviceInformation:
        """DIB 01h Device Information."""
        dib = DIBDeviceInformation()
        dib.knx_medium = KNXMedium.TP1
        dib.programming_mode = False
        dib.individual_address = self.config.individual_address
        dib.serial_number = self.config.serial_number.hex(":")
        dib.multicast_address = MULTICAST_GROUP
        dib.mac_address = self.config.mac_address.hex(":")
        dib.name = self.config.name
        return dib

    def supported_families(self, extended: bool) -> DIBSuppSVCFamilies:
        """DIB 02h Supported Service Families. Security only in extended responses."""
        dib = DIBSuppSVCFamilies()
        dib.families = [
            DIBSuppSVCFamilies.Family(DIBServiceFamily.CORE, 2),
            DIBSuppSVCFamilies.Family(DIBServiceFamily.DEVICE_MANAGEMENT, 2),
            DIBSuppSVCFamilies.Family(DIBServiceFamily.TUNNELING, 2),
        ]
        if extended:
            dib.families.append(DIBSuppSVCFamilies.Family(DIBServiceFamily.SECURITY, 1))
        return dib

    def secured_families(self) -> DIBSecuredServiceFamilies | None:
        """DIB 06h Secured Service Families (only families that require security)."""
        dib = DIBSecuredServiceFamilies()
        if self.config.secure_device_management:
            dib.families.append(
                DIBSuppSVCFamilies.Family(DIBServiceFamily.DEVICE_MANAGEMENT, 1)
            )
        if self.config.secure_tunnelling:
            dib.families.append(
                DIBSuppSVCFamilies.Family(DIBServiceFamily.TUNNELING, 1)
            )
        return dib if dib.families else None

    def ip_config(self) -> DIBGeneric:
        """DIB 03h IP Config."""
        data = (
            ip_bytes(self.config.local_ip)
            + ip_bytes("255.255.255.0")
            + ip_bytes("0.0.0.0")
            + bytes((0x00, 0x01))  # IP capabilities: none, assignment: manual
        )
        return generic_dib(DIBTypeCode.IP_CONFIG, data)

    def ip_current_config(self) -> DIBGeneric:
        """DIB 04h IP Current Config."""
        data = (
            ip_bytes(self.config.local_ip)
            + ip_bytes("255.255.255.0")
            + ip_bytes("0.0.0.0")
            + ip_bytes("0.0.0.0")  # DHCP server
            + bytes((0x01, 0x00))  # current assignment: manual, reserved
        )
        return generic_dib(DIBTypeCode.IP_CUR_CONFIG, data)

    def knx_addresses(self) -> DIBGeneric:
        """DIB 05h KNX Addresses: own IA + additional IAs (the tunnelling addresses)."""
        data = self.config.individual_address.to_knx() + b"".join(
            ia.to_knx() for ia in self.config.tunnel_addresses
        )
        return generic_dib(DIBTypeCode.KNX_ADDRESSES, data)

    def tunnelling_info(self) -> DIBGeneric:
        """DIB 07h Tunnelling Info. Reserved status bits are 1 (03_08_02 §7.5.4.8)."""
        data = self.config.max_apdu_length.to_bytes(2, "big")
        for ia in self.config.tunnel_addresses:
            free = self.server.tunnel_free(ia)
            status = 0xFFF8 | 0b100 | 0b010 | (0b001 if free else 0)
            data += ia.to_knx() + status.to_bytes(2, "big")
        return generic_dib(DIBTypeCode.TUNNELING_INFO, data)

    def search_response(self, extended: bool) -> SearchResponse:
        """Build SEARCH_RESPONSE or SEARCH_RESPONSE_EXTENDED."""
        control_endpoint = HPAI(self.config.local_ip, self.config.port)
        response: SearchResponse = (
            SearchResponseExtended(control_endpoint=control_endpoint)
            if extended
            else SearchResponse(control_endpoint=control_endpoint)
        )
        response.dibs = [self.device_info(), self.supported_families(extended)]
        if extended:
            response.dibs += [
                self.ip_config(),
                self.ip_current_config(),
                self.knx_addresses(),
                self.tunnelling_info(),
            ]
            if secured := self.secured_families():
                response.dibs.append(secured)
        return response

    def description_response(self) -> DescriptionResponse:
        """Build DESCRIPTION_RESPONSE (Core v1 content)."""
        response = DescriptionResponse()
        response.dibs = [self.device_info(), self.supported_families(extended=False)]
        return response

    def search_request_extended_matches(self, request: SearchRequestExtended) -> bool:
        """Evaluate the SRPs of a SEARCH_REQUEST_EXTENDED (03_08_02 §7.6.2)."""
        for srp in request.srps:
            matches = True
            if srp.type == SearchRequestParameterType.SELECT_BY_PROGRAMMING_MODE:
                matches = False  # we are never in programming mode
            elif srp.type == SearchRequestParameterType.SELECT_BY_MAC_ADDRESS:
                matches = srp.data == self.config.mac_address
            elif srp.type == SearchRequestParameterType.SELECT_BY_SERVICE:
                try:
                    family = DIBServiceFamily(srp.data[0])
                except ValueError:
                    matches = False
                else:
                    matches = self.supported_families(extended=True).supports(
                        family, srp.data[1]
                    )
            elif srp.type == SearchRequestParameterType.REQUEST_DIBS:
                log.info(
                    "    client asks for DIBs %s (we always send all of ours)",
                    ", ".join(enum_name(DIBTypeCode, d) for d in srp.data if d),
                )
            log.info(
                "    SRP %s mandatory=%s -> %s", srp.type.name, srp.mandatory, matches
            )
            if srp.mandatory and not matches:
                return False
        return True


# ---------------------------------------------------------------------------
# Property store for KNXnet/IP Device Management (cEMI M_PropRead / M_PropWrite)
# ---------------------------------------------------------------------------


class PropertyStore:
    """Minimal interface object model: (object type, pid) -> list of element bytes."""

    def __init__(self, config: ServerConfig) -> None:
        """Fill in the properties ETS usually reads."""
        self.config = config
        self.props: dict[tuple[int, int], list[bytes]] = {}
        self.read_only: set[tuple[int, int]] = set()
        dev = ResourceObjectType.OBJECT_DEVICE
        knxip = ResourceObjectType.OBJECT_KNXNETIP_PARAMETER
        d = ResourceDevicePropertyId
        g = ResourceGenericPropertyId
        k = ResourceKNXNETIPPropertyId

        self.set(
            dev, ResourceGenericPropertyId.PID_OBJECT_TYPE, [bytes(2)], read_only=True
        )
        self.set(dev, g.PID_SERIAL_NUMBER, [config.serial_number], read_only=True)
        self.set(
            dev,
            g.PID_MANUFACTURER_ID,
            [config.manufacturer_id.to_bytes(2, "big")],
            read_only=True,
        )
        self.set(dev, g.PID_DEVICE_CONTROL, [bytes(1)])
        self.set(dev, g.PID_ORDER_INFO, [b"xknx-poc".ljust(10, b"\0")], read_only=True)
        self.set(dev, d.PID_PROGMODE, [bytes(1)])
        self.set(
            dev,
            d.PID_MAX_APDU_LENGTH,
            [config.max_apdu_length.to_bytes(2, "big")],
            read_only=True,
        )
        self.set(
            dev,
            d.PID_HARDWARE_TYPE,
            [bytes.fromhex("00 00 00 00 00 01")],
            read_only=True,
        )
        self.set(dev, g.PID_FIRMWARE_REVISION, [bytes((0x01,))], read_only=True)
        self.set(
            dev,
            d.PID_DEVICE_DESCRIPTOR,
            [DEVICE_DESCRIPTOR_KNX_IP_SYSTEM_B.to_bytes(2, "big")],
            read_only=True,
        )

        self.set(
            knxip,
            ResourceGenericPropertyId.PID_OBJECT_TYPE,
            [knxip.to_bytes(2, "big")],
            read_only=True,
        )
        self.set(knxip, k.PID_PROJECT_INSTALLATION_ID, [bytes(2)])
        self.set(
            knxip, k.PID_KNX_INDIVIDUAL_ADDRESS, [config.individual_address.to_knx()]
        )
        self.set(
            knxip,
            k.PID_ADDITIONAL_INDIVIDUAL_ADDRESSES,
            [ia.to_knx() for ia in config.tunnel_addresses],
        )
        self.set(
            knxip, k.PID_CURRENT_IP_ASSIGNMENT_METHOD, [bytes((0x01,))], read_only=True
        )
        self.set(knxip, k.PID_IP_ASSIGNMENT_METHOD, [bytes((0x01,))])
        self.set(knxip, k.PID_IP_CAPABILITIES, [bytes((0x00,))], read_only=True)
        self.set(
            knxip, k.PID_CURRENT_IP_ADDRESS, [ip_bytes(config.local_ip)], read_only=True
        )
        self.set(
            knxip,
            k.PID_CURRENT_SUBNET_MASK,
            [ip_bytes("255.255.255.0")],
            read_only=True,
        )
        self.set(
            knxip, k.PID_CURRENT_DEFAULT_GATEWAY, [ip_bytes("0.0.0.0")], read_only=True
        )
        self.set(knxip, k.PID_IP_ADDRESS, [ip_bytes(config.local_ip)])
        self.set(knxip, k.PID_SUBNET_MASK, [ip_bytes("255.255.255.0")])
        self.set(knxip, k.PID_DEFAULT_GATEWAY, [ip_bytes("0.0.0.0")])
        self.set(knxip, k.PID_DHCP_BOOTP_SERVER, [ip_bytes("0.0.0.0")], read_only=True)
        self.set(knxip, k.PID_MAC_ADDRESS, [config.mac_address], read_only=True)
        self.set(
            knxip,
            k.PID_SYSTEM_SETUP_MULTICAST_ADDRESS,
            [ip_bytes(MULTICAST_GROUP)],
            read_only=True,
        )
        self.set(knxip, k.PID_ROUTING_MULTICAST_ADDRESS, [ip_bytes(MULTICAST_GROUP)])
        self.set(knxip, k.PID_TTL, [bytes((16,))])
        # bit 0 device management, bit 1 tunnelling, bit 6 security (03_08_03 §2.5.19)
        self.set(
            knxip,
            k.PID_KNXNETIP_DEVICE_CAPABILITIES,
            [(0b1000011).to_bytes(2, "big")],
            read_only=True,
        )
        self.set(knxip, k.PID_KNXNETIP_DEVICE_STATE, [bytes(1)], read_only=True)
        self.set(
            knxip,
            k.PID_FRIENDLY_NAME,
            [bytes(config.name[:30], "latin_1").ljust(30, b"\0")],
        )
        # PID_TUNNELLING_USERS (97): (user id, index into additional addresses), users 2..n
        self.set(
            knxip,
            97,
            [
                bytes((user_id, index))
                for index, user_id in enumerate(
                    range(2, 2 + len(config.tunnel_addresses)), start=1
                )
            ],
        )

    def set(
        self,
        object_type: int,
        pid: int,
        elements: list[bytes],
        read_only: bool = False,
    ) -> None:
        """Store a property."""
        key = (int(object_type), int(pid))
        self.props[key] = elements
        if read_only:
            self.read_only.add(key)

    @staticmethod
    def pid_name(object_type: int, pid: int) -> str:
        """Readable property name for the log."""
        enum = (
            ResourceKNXNETIPPropertyId
            if object_type == ResourceObjectType.OBJECT_KNXNETIP_PARAMETER
            else ResourceDevicePropertyId
        )
        for candidates in (enum, ResourceGenericPropertyId):
            try:
                return candidates(pid).name
            except ValueError:
                pass
        return {
            97: "PID_TUNNELLING_USERS",
            94: "PID_SECURED_SERVICE_FAMILIES",
            92: "PID_DEVICE_AUTHENTICATION_CODE",
            93: "PID_PASSWORD_HASHES",
            91: "PID_BACKBONE_KEY",
        }.get(pid, f"PID_{pid}")

    def read(self, info: CEMIMPropInfo) -> tuple[bytes, int]:
        """
        Return (data, number_of_elements) for a read; number_of_elements 0 => error.

        start_index 0 returns the current number of elements (2 octets).
        """
        key = (int(info.object_type), int(info.property_id))
        elements = self.props.get(key)
        if elements is None:
            return bytes((0x07,)), 0  # CEMI_ERROR_VOID_DP
        if info.start_index == 0:
            return len(elements).to_bytes(2, "big"), 1
        start = info.start_index - 1
        selected = elements[start : start + info.number_of_elements]
        if len(selected) != info.number_of_elements:
            return bytes((0x09,)), 0  # CEMI_ERROR_PROP_INDEX_RANGE
        return b"".join(selected), info.number_of_elements

    def write(self, info: CEMIMPropInfo, data: bytes) -> int | None:
        """Write elements; returns a CEMI error code or None on success."""
        key = (int(info.object_type), int(info.property_id))
        elements = self.props.get(key)
        if elements is None:
            return 0x07  # CEMI_ERROR_VOID_DP
        if key in self.read_only:
            return 0x05  # CEMI_ERROR_READ_ONLY
        size = (
            len(elements[0])
            if elements
            else len(data) // max(info.number_of_elements, 1)
        )
        if info.number_of_elements * size != len(data):
            return 0x08  # CEMI_ERROR_TYPE_CONFLICT
        start = info.start_index - 1
        for i in range(info.number_of_elements):
            chunk = data[i * size : (i + 1) * size]
            if start + i < len(elements):
                elements[start + i] = chunk
            elif start + i == len(elements):
                elements.append(chunk)
            else:
                return 0x09  # CEMI_ERROR_PROP_INDEX_RANGE
        return None


# ---------------------------------------------------------------------------
# Connections (communication channels) inside a secure session
# ---------------------------------------------------------------------------


@dataclass
class Channel:
    """A KNXnet/IP communication channel (tunnelling or device management)."""

    channel_id: int
    connection_type: ConnectRequestType
    session: ClientSession
    individual_address: IndividualAddress | None = None
    layer: TunnellingLayer | None = None
    sequence_out: int = 0
    last_seen: float = field(default_factory=time.monotonic)
    feature_info_enabled: bool = False
    alive_timer: asyncio.TimerHandle | None = None

    def next_sequence(self) -> int:
        """Server side sequence counter (not evaluated over TCP, but kept correct)."""
        seq = self.sequence_out
        self.sequence_out = (seq + 1) & 0xFF
        return seq


# ---------------------------------------------------------------------------
# Secure session (one per TCP connection)
# ---------------------------------------------------------------------------


class ClientSession(asyncio.Protocol):
    """State machine of 03_08_09 §2.2.3.5.2 for one TCP client, plus the KNXnet/IP services."""

    def __init__(self, server: SecureServer) -> None:
        """Initialize."""
        self.server = server
        self.config = server.config
        self.transport: asyncio.Transport | None = None
        self.peer = "?"
        self._buffer = b""
        self.state = "IDLE"
        self.session_id = 0
        self.user_id = 0
        self._private_key: Any = None
        self.public_key = bytes(32)
        self.client_public_key = bytes(32)
        self.session_key = bytes(16)
        self.sequence_out = 0
        self.sequence_in = -1
        self._timer: asyncio.TimerHandle | None = None
        self.channels: dict[int, Channel] = {}
        self.created = time.monotonic()
        self._authenticate_received = False

    # ----- asyncio.Protocol -----

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """TCP connection accepted."""
        self.transport = transport  # type: ignore[assignment]
        host, port = transport.get_extra_info("peername")[:2]
        self.peer = f"{host}:{port}"
        log.info("=== TCP connection from %s", self.peer)
        self.server.sessions.add(self)

    def data_received(self, data: bytes) -> None:
        """Split the TCP stream into KNXnet/IP frames."""
        log.debug("<<< raw tcp from %s: %s", self.peer, data.hex())
        raw = self._buffer + data
        self._buffer = b""
        while raw:
            try:
                frame, raw = KNXIPFrame.from_knx(raw)
            except IncompleteKNXIPFrame:
                self._buffer = raw
                return
            except CouldNotParseKNXIP as err:
                log.warning(
                    "<<< %s unparsable frame: %s (%s)", self.peer, raw.hex(), err
                )
                header = KNXIPHeader()
                try:
                    header.from_knx(raw)
                except CouldNotParseKNXIP:
                    pass
                if header.total_length >= KNXIPHeader.HEADERLENGTH:
                    raw = raw[header.total_length :]
                    continue
                return
            try:
                self.handle_frame(frame)
            except Exception:  # pylint: disable=broad-except
                log.exception("error while handling %s", fmt_frame(frame))

    def connection_lost(self, exc: Exception | None) -> None:
        """TCP connection closed."""
        log.info(
            "=== TCP connection %s closed (%s) after %.1f s, state was %s",
            self.peer,
            exc or "by peer",
            time.monotonic() - self.created,
            self.state,
        )
        if self.state == "UNAUTHENTICATED" and not self._authenticate_received:
            log.warning(
                "    HINT: the client closed the connection after SESSION_RESPONSE without "
                "sending SESSION_AUTHENTICATE. ETS does this when the MAC of our "
                "SESSION_RESPONSE does not verify, i.e. the device authentication code "
                "the client uses differs from ours (%r).",
                self.config.device_authentication_password,
            )
        self._cancel_timer()
        for channel in list(self.channels.values()):
            self.server.release_channel(channel, reason="tcp connection lost")
        self.server.sessions.discard(self)
        if self.session_id:
            self.server.session_ids.discard(self.session_id)
        self.state = "IDLE"
        self.transport = None

    # ----- sending -----

    def send_plain(self, body: Any) -> None:
        """Send an unwrapped frame."""
        frame = KNXIPFrame.init_from_body(body)
        log.info(">>> %s %s", self.peer, fmt_frame(frame))
        self._write(frame)

    def send_wrapped(self, body: Any) -> None:
        """Send a frame wrapped in a SECURE_WRAPPER of this session."""
        frame = KNXIPFrame.init_from_body(body)
        wrapper = self.encrypt(frame)
        log.info(
            ">>> %s SECURE_WRAPPER(session=%d seq=%d) %s",
            self.peer,
            self.session_id,
            int.from_bytes(wrapper.body.sequence_information, "big"),  # type: ignore[attr-defined]
            fmt_frame(frame),
        )
        log.debug("    wrapper: %s", wrapper.body)
        self._write(wrapper)

    def _write(self, frame: KNXIPFrame) -> None:
        if self.transport is None or self.transport.is_closing():
            log.warning("    cannot send, transport closed: %s", fmt_frame(frame))
            return
        raw = frame.to_knx()
        log.debug(">>> raw tcp to %s: %s", self.peer, raw.hex())
        self.transport.write(raw)

    def close(self, status: SecureSessionStatusCode | None, reason: str) -> None:
        """Send a final SESSION_STATUS (if any) and close the TCP connection."""
        log.info(
            "=== closing session %d with %s: %s", self.session_id, self.peer, reason
        )
        if status is not None and self.state != "IDLE":
            self.send_wrapped(SessionStatus(status=status))
        self._cancel_timer()
        if self.transport is not None:
            self.transport.close()

    # ----- timers -----

    def _cancel_timer(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _restart_timer(self, seconds: float, status: SecureSessionStatusCode) -> None:
        self._cancel_timer()
        loop = asyncio.get_running_loop()
        self._timer = loop.call_later(
            seconds,
            lambda: self.close(
                status, f"{status.name} after {seconds:.0f} s of inactivity"
            ),
        )

    # ----- crypto -----

    def encrypt(self, plain_frame: KNXIPFrame) -> KNXIPFrame:
        """Wrap a frame: CCM with the session key (03_08_09 §2.2.1.3.2)."""
        sequence_information = self.sequence_out.to_bytes(6, "big")
        self.sequence_out += 1
        payload = plain_frame.to_knx()
        total_length = 6 + 16 + len(payload) + 16
        wrapper_header = bytes.fromhex("06 10 09 50") + total_length.to_bytes(2, "big")
        session_id = self.session_id.to_bytes(2, "big")
        nonce = sequence_information + self.config.serial_number + MESSAGE_TAG_UNICAST
        mac_cbc = calculate_message_authentication_code_cbc(
            key=self.session_key,
            additional_data=wrapper_header + session_id,
            payload=payload,
            block_0=nonce + len(payload).to_bytes(2, "big"),
        )
        encrypted_data, mac = encrypt_data_ctr(
            key=self.session_key,
            counter_0=nonce + b"\xff\x00",
            mac_cbc=mac_cbc,
            payload=payload,
        )
        return KNXIPFrame.init_from_body(
            SecureWrapper(
                secure_session_id=self.session_id,
                sequence_information=sequence_information,
                serial_number=self.config.serial_number,
                message_tag=MESSAGE_TAG_UNICAST,
                encrypted_data=encrypted_data,
                message_authentication_code=mac,
            )
        )

    def decrypt(self, wrapper_frame: KNXIPFrame) -> KNXIPFrame | None:
        """Unwrap and verify a SECURE_WRAPPER (03_08_09 §2.2.1.3.3). None if to be discarded."""
        wrapper = wrapper_frame.body
        assert isinstance(wrapper, SecureWrapper)
        if wrapper.secure_session_id != self.session_id:
            log.warning(
                "    discarded: unknown session id %d", wrapper.secure_session_id
            )
            return None
        sequence = int.from_bytes(wrapper.sequence_information, "big")
        if sequence <= self.sequence_in:
            log.warning(
                "    discarded: sequence %d <= last %d (replay?)",
                sequence,
                self.sequence_in,
            )
            return None
        nonce = (
            wrapper.sequence_information + wrapper.serial_number + wrapper.message_tag
        )
        decrypted, mac_tr = decrypt_ctr(
            key=self.session_key,
            counter_0=nonce + b"\xff\x00",
            mac=wrapper.message_authentication_code,
            payload=wrapper.encrypted_data,
        )
        mac_cbc = calculate_message_authentication_code_cbc(
            key=self.session_key,
            additional_data=wrapper_frame.header.to_knx()
            + wrapper.secure_session_id.to_bytes(2, "big"),
            payload=decrypted,
            block_0=nonce + len(decrypted).to_bytes(2, "big"),
        )
        if not hmac.compare_digest(mac_cbc, mac_tr):
            log.warning("    discarded: MAC verification failed (wrong session key?)")
            return None
        self.sequence_in = sequence
        if wrapper.message_tag != MESSAGE_TAG_UNICAST:
            log.info(
                "    note: client uses message tag %s (spec: 0000h for unicast)",
                wrapper.message_tag.hex(),
            )
        try:
            frame, _ = KNXIPFrame.from_knx(decrypted)
        except CouldNotParseKNXIP as err:
            log.warning(
                "    decrypted frame not parsable: %s (%s)", decrypted.hex(), err
            )
            return None
        log.debug("    decrypted raw: %s", decrypted.hex())
        return frame

    # ----- frame dispatch -----

    def handle_frame(self, frame: KNXIPFrame) -> None:
        """Handle a frame received on the TCP connection."""
        body = frame.body
        if isinstance(body, SecureWrapper):
            log.info(
                "<<< %s SECURE_WRAPPER(session=%d seq=%d serial=%s tag=%s, %d bytes payload)",
                self.peer,
                body.secure_session_id,
                int.from_bytes(body.sequence_information, "big"),
                body.serial_number.hex(),
                body.message_tag.hex(),
                len(body.encrypted_data),
            )
            if self.state == "IDLE":
                log.warning("    discarded: no session established on this connection")
                return
            inner = self.decrypt(frame)
            if inner is None:
                return
            log.info("    decrypted: %s", fmt_frame(inner))
            self.handle_wrapped(inner)
            return

        log.info("<<< %s (plain) %s", self.peer, fmt_frame(frame))
        if isinstance(body, SessionRequest):
            if self.state != "IDLE":
                log.warning(
                    "    SESSION_REQUEST while in state %s - ignored", self.state
                )
                return
            self.handle_session_request(body)
        elif isinstance(body, ConnectRequest):
            self.handle_plain_connect_request(body, send=self.send_plain)
        elif isinstance(body, DescriptionRequest):
            self.send_plain(self.server.description.description_response())
        elif isinstance(body, SearchRequestExtended):
            if self.server.description.search_request_extended_matches(body):
                self.send_plain(self.server.description.search_response(extended=True))
        elif isinstance(body, SearchRequest):
            self.send_plain(self.server.description.search_response(extended=False))
        else:
            log.warning(
                "    plain %s on TCP ignored (state %s)",
                frame.header.service_type_ident.name,
                self.state,
            )

    def handle_plain_connect_request(self, request: ConnectRequest, send: Any) -> None:
        """Unwrapped CONNECT_REQUEST: only allowed when the service family is not secured."""
        secured = (
            self.config.secure_tunnelling
            if request.cri.connection_type == ConnectRequestType.TUNNEL_CONNECTION
            else self.config.secure_device_management
        )
        if secured:
            log.warning(
                "    plain CONNECT_REQUEST for %s but security is required -> access denied, frame ignored"
                " (03_08_09 §2.2.1.4.2)",
                request.cri.connection_type.name,
            )
            return
        log.info("    plain connection (security not required for this service family)")
        self.handle_connect_request(request, send=send, user_id=None)

    # ----- secure session handshake -----

    def handle_session_request(self, request: SessionRequest) -> None:
        """SESSION_REQUEST -> SESSION_RESPONSE (03_08_09 §2.2.3.6 / §2.2.3.7)."""
        log.info(
            "    client control endpoint %s, client public value X=%s",
            request.control_endpoint,
            request.ecdh_client_public_key.hex(),
        )
        self.client_public_key = bytes(request.ecdh_client_public_key)
        self._private_key, self.public_key = generate_ecdh_key_pair()
        self.session_id = self.server.new_session_id()
        shared_secret = self._private_key.exchange(
            X25519PublicKey.from_public_bytes(self.client_public_key)
        )
        self.session_key = sha256_hash(shared_secret)[:16]
        pub_keys_xor = bytes_xor(self.client_public_key, self.public_key)
        # MAC with the device authentication code over header | session id | X ^ Y
        response_header = bytes.fromhex("06 10 09 52 00 38")
        mac_cbc = calculate_message_authentication_code_cbc(
            key=self.server.device_authentication_code,
            additional_data=response_header
            + self.session_id.to_bytes(2, "big")
            + pub_keys_xor,
            block_0=bytes(16),
        )
        _, mac = encrypt_data_ctr(
            key=self.server.device_authentication_code,
            counter_0=COUNTER_0_HANDSHAKE,
            mac_cbc=mac_cbc,
        )
        log.info(
            "    new session id %d, server public value Y=%s\n    session key (sha256(ECDH)[:16]) = %s",
            self.session_id,
            self.public_key.hex(),
            self.session_key.hex(),
        )
        self.sequence_out = 0
        self.sequence_in = -1
        self._authenticate_received = False
        self.state = "UNAUTHENTICATED"
        self.send_plain(
            SessionResponse(
                secure_session_id=self.session_id,
                ecdh_server_public_key=self.public_key,
                message_authentication_code=mac,
            )
        )
        self._restart_timer(
            TIMEOUT_AUTHENTICATION, SecureSessionStatusCode.STATUS_TIMEOUT
        )
        log.info(
            "    waiting up to %d s for SESSION_AUTHENTICATE", TIMEOUT_AUTHENTICATION
        )

    def handle_session_authenticate(self, auth: SessionAuthenticate) -> None:
        """SESSION_AUTHENTICATE -> SESSION_STATUS (03_08_09 §2.2.3.8)."""
        self._authenticate_received = True
        log.info(
            "    the client accepted our SESSION_RESPONSE MAC: its device authentication "
            "code matches ours"
        )
        user_id = auth.user_id
        if user_id == 0 or user_id >= 0x80:
            log.warning("    reserved user id %d -> AUTHENTICATION_FAILED", user_id)
            self.close(
                SecureSessionStatusCode.STATUS_AUTHENTICATION_FAILED, "reserved user id"
            )
            return
        candidates: list[tuple[str, str]] = []
        if user_id in self.config.user_passwords:
            candidates.append(
                ("configured password", self.config.user_passwords[user_id])
            )
        elif self.config.any_user_password is not None:
            candidates.append(("--any-user password", self.config.any_user_password))
        if not candidates:
            log.warning(
                "    user id %d has no password configured -> AUTHENTICATION_FAILED",
                user_id,
            )
            self.close(
                SecureSessionStatusCode.STATUS_AUTHENTICATION_FAILED, "unknown user"
            )
            return

        pub_keys_xor = bytes_xor(self.client_public_key, self.public_key)
        authenticate_header = bytes.fromhex("06 10 09 53 00 18")
        for label, password in candidates:
            user_key = self.server.user_key(password)
            mac_cbc = calculate_message_authentication_code_cbc(
                key=user_key,
                additional_data=authenticate_header
                + bytes(1)
                + bytes((user_id,))
                + pub_keys_xor,
                block_0=bytes(16),
            )
            _, mac_tr = decrypt_ctr(
                key=user_key,
                counter_0=COUNTER_0_HANDSHAKE,
                mac=auth.message_authentication_code,
            )
            if hmac.compare_digest(mac_cbc, mac_tr):
                self.user_id = user_id
                self.state = "AUTHENTICATED"
                log.info(
                    "    user %d authenticated with %s -> AUTHENTICATION_SUCCESS",
                    user_id,
                    label,
                )
                self.send_wrapped(
                    SessionStatus(
                        status=SecureSessionStatusCode.STATUS_AUTHENTICATION_SUCCESS
                    )
                )
                self._restart_timer(
                    TIMEOUT_SESSION, SecureSessionStatusCode.STATUS_TIMEOUT
                )
                return
        log.warning(
            "    user id %d: MAC does not match the password -> AUTHENTICATION_FAILED",
            user_id,
        )
        self.close(
            SecureSessionStatusCode.STATUS_AUTHENTICATION_FAILED, "wrong password"
        )

    # ----- services inside the session -----

    def handle_wrapped(self, frame: KNXIPFrame) -> None:
        """Dispatch a decrypted frame."""
        body = frame.body
        if self.state == "UNAUTHENTICATED":
            if isinstance(body, SessionAuthenticate):
                self.handle_session_authenticate(body)
            else:
                log.warning(
                    "    %s before authentication -> STATUS_UNAUTHENTICATED",
                    frame.header.service_type_ident.name,
                )
                self.close(
                    SecureSessionStatusCode.STATUS_UNAUTHENTICATED,
                    "service before authentication",
                )
            return

        # AUTHENTICATED: every valid frame restarts the session timer
        self._restart_timer(TIMEOUT_SESSION, SecureSessionStatusCode.STATUS_TIMEOUT)

        if isinstance(body, SessionStatus):
            if body.status == SecureSessionStatusCode.STATUS_KEEPALIVE:
                log.info(
                    "    keepalive, session timer restarted (%d s)", TIMEOUT_SESSION
                )
            elif body.status == SecureSessionStatusCode.STATUS_CLOSE:
                self.close(None, "client sent STATUS_CLOSE")
            else:
                log.info(
                    "    unexpected session status from client: %s", body.status.name
                )
        elif isinstance(body, SessionAuthenticate):
            log.info(
                "    repeated SESSION_AUTHENTICATE in authenticated session - ignored"
            )
        elif isinstance(body, DescriptionRequest):
            self.send_wrapped(self.server.description.description_response())
        elif isinstance(body, SearchRequestExtended):
            if self.server.description.search_request_extended_matches(body):
                self.send_wrapped(
                    self.server.description.search_response(extended=True)
                )
        elif isinstance(body, SearchRequest):
            self.send_wrapped(self.server.description.search_response(extended=False))
        elif isinstance(body, ConnectRequest):
            self.handle_connect_request(
                body, send=self.send_wrapped, user_id=self.user_id
            )
        elif isinstance(body, ConnectionStateRequest):
            channel = self.channels.get(body.communication_channel_id)
            status = ErrorCode.E_NO_ERROR if channel else ErrorCode.E_CONNECTION_ID
            if channel:
                self.server.touch_channel(channel)
            self.send_wrapped(
                ConnectionStateResponse(
                    communication_channel_id=body.communication_channel_id,
                    status_code=status,
                )
            )
        elif isinstance(body, DisconnectRequest):
            channel = self.channels.get(body.communication_channel_id)
            status = ErrorCode.E_NO_ERROR if channel else ErrorCode.E_CONNECTION_ID
            self.send_wrapped(
                DisconnectResponse(
                    communication_channel_id=body.communication_channel_id,
                    status_code=status,
                )
            )
            if channel:
                self.server.release_channel(
                    channel, reason="DISCONNECT_REQUEST from client"
                )
        elif isinstance(body, TunnellingRequest):
            self.handle_tunnelling_request(body)
        elif isinstance(body, TunnellingAck):
            log.info(
                "    client acknowledged our TUNNELLING_REQUEST seq=%d status=%s",
                body.sequence_counter,
                body.status_code.name,
            )
        elif isinstance(body, TunnellingFeatureGet | TunnellingFeatureSet):
            self.handle_tunnelling_feature(body)
        elif isinstance(body, DeviceConfigurationRequest):
            self.handle_device_configuration_request(body)
        elif isinstance(body, DeviceConfigurationAck):
            log.info(
                "    client acknowledged our DEVICE_CONFIGURATION_REQUEST seq=%d status=%s",
                body.sequence_counter,
                body.status_code.name,
            )
        else:
            log.warning(
                "    unhandled service %s", frame.header.service_type_ident.name
            )

    def handle_connect_request(
        self, request: ConnectRequest, send: Any, user_id: int | None
    ) -> None:
        """CONNECT_REQUEST -> CONNECT_RESPONSE with channel id and CRD."""
        cri = request.cri
        log.info(
            "    control endpoint %s, data endpoint %s, %s",
            request.control_endpoint,
            request.data_endpoint,
            cri,
        )

        def reject(status: ErrorCode, why: str) -> None:
            log.warning("    CONNECT_REQUEST rejected: %s -> %s", why, status.name)
            send(
                ConnectResponse(
                    communication_channel=0,
                    status_code=status,
                    data_endpoint=HPAI(),
                    crd=ConnectResponseData(request_type=cri.connection_type),
                )
            )

        is_mgmt_user = (
            user_id is None
            or user_id == 1
            or (
                user_id not in self.config.user_passwords
                and self.config.any_user_password is not None
            )
        )
        individual_address: IndividualAddress | None = None

        if cri.connection_type == ConnectRequestType.DEVICE_MGMT_CONNECTION:
            if self.config.secure_device_management and not is_mgmt_user:
                reject(
                    ErrorCode.E_AUTHORISATION_ERROR,
                    f"user {user_id} is not the management user",
                )
                return
        elif cri.connection_type == ConnectRequestType.TUNNEL_CONNECTION:
            if cri.knx_layer != TunnellingLayer.DATA_LINK_LAYER:
                reject(
                    ErrorCode.E_TUNNELLING_LAYER,
                    f"layer {cri.knx_layer.name} not supported by this PoC",
                )
                return
            # which tunnelling addresses may this user use? (PID_TUNNELLING_USERS: user n -> address n-1)
            if is_mgmt_user:
                allowed = list(self.config.tunnel_addresses)
            else:
                assert user_id is not None
                index = user_id - 2
                allowed = (
                    [self.config.tunnel_addresses[index]]
                    if 0 <= index < len(self.config.tunnel_addresses)
                    else []
                )
            if cri.individual_address is not None:
                log.info(
                    "    extended CRI: client requests tunnelling address %s",
                    cri.individual_address,
                )
                if cri.individual_address not in self.config.tunnel_addresses:
                    reject(
                        ErrorCode.E_NO_TUNNELLING_ADDRESS,
                        f"{cri.individual_address} is not a tunnelling address of this server",
                    )
                    return
                if cri.individual_address not in allowed:
                    reject(
                        ErrorCode.E_AUTHORISATION_ERROR,
                        f"user {user_id} may not use {cri.individual_address}",
                    )
                    return
                if not self.server.tunnel_free(cri.individual_address):
                    reject(
                        ErrorCode.E_CONNECTION_IN_USE,
                        f"{cri.individual_address} is in use",
                    )
                    return
                individual_address = cri.individual_address
            else:
                free = [ia for ia in allowed if self.server.tunnel_free(ia)]
                if not free:
                    reject(
                        ErrorCode.E_NO_MORE_CONNECTIONS,
                        "no free tunnelling address for this user",
                    )
                    return
                individual_address = free[0]
        else:
            reject(
                ErrorCode.E_CONNECTION_TYPE,
                f"connection type {cri.connection_type.name} not supported",
            )
            return

        channel = self.server.new_channel(
            self,
            cri.connection_type,
            individual_address,
            cri.knx_layer
            if cri.connection_type == ConnectRequestType.TUNNEL_CONNECTION
            else None,
        )
        if channel is None:
            reject(ErrorCode.E_NO_MORE_CONNECTIONS, "no free communication channel id")
            return
        log.info(
            "    channel %d opened: %s%s (user %s)",
            channel.channel_id,
            cri.connection_type.name,
            f" as {individual_address}" if individual_address else "",
            user_id if user_id is not None else "plain",
        )
        send(
            ConnectResponse(
                communication_channel=channel.channel_id,
                status_code=ErrorCode.E_NO_ERROR,
                data_endpoint=HPAI(
                    protocol=HostProtocol.IPV4_TCP
                ),  # route back over this TCP connection
                crd=ConnectResponseData(
                    request_type=cri.connection_type,
                    individual_address=individual_address,
                ),
            )
        )

    def handle_tunnelling_request(self, request: TunnellingRequest) -> None:
        """TUNNELLING_REQUEST: ack, confirm the cEMI and feed it into the virtual bus."""
        channel = self.channels.get(request.communication_channel_id)
        if (
            channel is None
            or channel.connection_type != ConnectRequestType.TUNNEL_CONNECTION
        ):
            log.warning(
                "    unknown tunnelling channel %d -> ack with E_CONNECTION_ID",
                request.communication_channel_id,
            )
            self.send_wrapped(
                TunnellingAck(
                    communication_channel_id=request.communication_channel_id,
                    sequence_counter=request.sequence_counter,
                    status_code=ErrorCode.E_CONNECTION_ID,
                )
            )
            return
        self.server.touch_channel(channel)
        log.info("    %s", describe_cemi(request.raw_cemi))
        # over TCP the sequence counter is not evaluated (03_08_04 §2.6)
        self.send_wrapped(
            TunnellingAck(
                communication_channel_id=channel.channel_id,
                sequence_counter=request.sequence_counter,
            )
        )
        asyncio.get_running_loop().create_task(
            self.server.bus.handle_from_client(channel, request.raw_cemi)
        )

    def send_cemi_to_client(self, channel: Channel, raw_cemi: bytes, what: str) -> None:
        """Send a cEMI frame to the client over a tunnelling or device management channel."""
        if channel.connection_type == ConnectRequestType.TUNNEL_CONNECTION:
            body: Any = TunnellingRequest(
                communication_channel_id=channel.channel_id,
                sequence_counter=channel.next_sequence(),
                raw_cemi=raw_cemi,
            )
        else:
            body = DeviceConfigurationRequest(
                communication_channel_id=channel.channel_id,
                sequence_counter=channel.next_sequence(),
                raw_cemi=raw_cemi,
            )
        log.info(
            "    -> %s on channel %d: %s",
            what,
            channel.channel_id,
            describe_cemi(raw_cemi),
        )
        self.send_wrapped(body)

    def handle_tunnelling_feature(
        self, request: TunnellingFeatureGet | TunnellingFeatureSet
    ) -> None:
        """TUNNELLING_FEATURE_GET / _SET -> TUNNELLING_FEATURE_RESPONSE (03_08_04 §3)."""
        channel = self.channels.get(request.communication_channel_id)
        if channel is None:
            log.warning(
                "    feature service on unknown channel %d - ignored",
                request.communication_channel_id,
            )
            return
        self.server.touch_channel(channel)
        feature = request.feature_type
        values: dict[TunnellingFeatureType, int] = {
            TunnellingFeatureType.SUPPORTED_EMI_TYPE: SUPPORTED_EMI_CEMI,
            TunnellingFeatureType.DEVICE_DESCRIPTOR_TYPE_0: DEVICE_DESCRIPTOR_KNX_IP_SYSTEM_B,
            TunnellingFeatureType.BUS_CONNECTION_STATUS: 1,
            TunnellingFeatureType.MANUFACTURER_CODE: self.config.manufacturer_id,
            TunnellingFeatureType.ACTIVE_EMI_TYPE: ACTIVE_EMI_CEMI,
            TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS: int.from_bytes(
                channel.individual_address.to_knx(), "big"
            )
            if channel.individual_address
            else 0,
            TunnellingFeatureType.MAX_APDU_LENGTH: self.config.max_apdu_length,
            TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE: int(
                channel.feature_info_enabled
            ),
        }
        return_code = ReturnCode.E_SUCCESS
        if isinstance(request, TunnellingFeatureSet):
            log.info(
                "    client wants to set feature %s to %s",
                feature.name,
                request.data.hex(),
            )
            if feature == TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE:
                channel.feature_info_enabled = bool(request.data[0])
                values[feature] = int(channel.feature_info_enabled)
            elif feature == TunnellingFeatureType.ACTIVE_EMI_TYPE:
                if request.data[0] != ACTIVE_EMI_CEMI:
                    return_code = ReturnCode.E_DATA_VOID
            else:
                return_code = ReturnCode.E_ACCESS_READ_ONLY
        data = values[feature].to_bytes(FEATURE_SIZE[feature], "big")
        self.send_wrapped(
            TunnellingFeatureResponse(
                communication_channel_id=channel.channel_id,
                sequence_counter=request.sequence_counter,
                feature_type=feature,
                return_code=return_code,
                data=data,
            )
        )

    def handle_device_configuration_request(
        self, request: DeviceConfigurationRequest
    ) -> None:
        """DEVICE_CONFIGURATION_REQUEST: ack and answer the cEMI M_Prop* service (03_08_03 §4)."""
        channel = self.channels.get(request.communication_channel_id)
        if (
            channel is None
            or channel.connection_type != ConnectRequestType.DEVICE_MGMT_CONNECTION
        ):
            log.warning(
                "    unknown device management channel %d -> ack with E_CONNECTION_ID",
                request.communication_channel_id,
            )
            self.send_wrapped(
                DeviceConfigurationAck(
                    communication_channel_id=request.communication_channel_id,
                    sequence_counter=request.sequence_counter,
                    status_code=ErrorCode.E_CONNECTION_ID,
                )
            )
            return
        self.server.touch_channel(channel)
        log.info("    %s", describe_cemi(request.raw_cemi))
        self.send_wrapped(
            DeviceConfigurationAck(
                communication_channel_id=channel.channel_id,
                sequence_counter=request.sequence_counter,
            )
        )
        raw = request.raw_cemi
        if not raw:
            return
        try:
            cemi = CEMIFrame.from_knx(raw)
        except (CouldNotParseCEMI, UnsupportedCEMIMessage):
            cemi = None
        store = self.server.properties
        if cemi is not None and isinstance(cemi.data, CEMIMPropReadRequest):
            info = cemi.data.property_info
            data, count = store.read(info)
            log.info(
                "    M_PropRead %s/%d %s start=%d n=%d -> %s",
                enum_name(ResourceObjectType, info.object_type),
                info.object_instance,
                store.pid_name(info.object_type, info.property_id),
                info.start_index,
                info.number_of_elements,
                f"error {data.hex()}" if count == 0 else data.hex(),
            )
            response = CEMIFrame(
                code=CEMIMessageCode.M_PROP_READ_CON,
                data=CEMIMPropReadResponse(
                    property_info=CEMIMPropInfo(
                        object_type=info.object_type,
                        object_instance=info.object_instance,
                        property_id=info.property_id,
                        number_of_elements=count,
                        start_index=info.start_index,
                    ),
                    data=data,
                ),
            )
            self.send_cemi_to_client(channel, response.to_knx(), "M_PropRead.con")
        elif cemi is not None and isinstance(cemi.data, CEMIMPropWriteRequest):
            info = cemi.data.property_info
            error = store.write(info, cemi.data.data)
            log.info(
                "    M_PropWrite %s/%d %s start=%d n=%d data=%s -> %s",
                enum_name(ResourceObjectType, info.object_type),
                info.object_instance,
                store.pid_name(info.object_type, info.property_id),
                info.start_index,
                info.number_of_elements,
                cemi.data.data.hex(),
                "ok" if error is None else f"error {error:#04x}",
            )
            response = CEMIFrame(
                code=CEMIMessageCode.M_PROP_WRITE_CON,
                data=CEMIMPropWriteResponse(
                    property_info=CEMIMPropInfo(
                        object_type=info.object_type,
                        object_instance=info.object_instance,
                        property_id=info.property_id,
                        number_of_elements=0
                        if error is not None
                        else info.number_of_elements,
                        start_index=info.start_index,
                    ),
                    error_code=error,
                ),
            )
            self.send_cemi_to_client(channel, response.to_knx(), "M_PropWrite.con")
        elif raw[0] == 0xF8 and len(raw) >= 5:  # M_FuncPropCommand.req
            log.info(
                "    M_FuncPropCommand.req (function property) -> answering E_COMMAND_INVALID"
            )
            response_raw = (
                bytes((0xFA,)) + raw[1:5] + bytes((ReturnCode.E_COMMAND_INVALID.value,))
            )
            self.send_cemi_to_client(channel, response_raw, "M_FuncPropCommand.con")
        elif raw[0] == 0xF9 and len(raw) >= 5:  # M_FuncPropStateRead.req
            log.info("    M_FuncPropStateRead.req -> answering E_COMMAND_INVALID")
            response_raw = (
                bytes((0xFA,)) + raw[1:5] + bytes((ReturnCode.E_COMMAND_INVALID.value,))
            )
            self.send_cemi_to_client(channel, response_raw, "M_FuncPropStateRead.con")
        elif raw[0] == 0xF1:  # M_Reset.req
            log.info("    M_Reset.req -> M_Reset.ind (nothing is actually reset)")
            self.send_cemi_to_client(channel, bytes((0xF0,)), "M_Reset.ind")
        else:
            log.warning(
                "    unsupported cEMI management service %#04x - no answer", raw[0]
            )


# ---------------------------------------------------------------------------
# Virtual bus (plus optional bridge to a real installation through xknx)
# ---------------------------------------------------------------------------


class VirtualBus:
    """Confirms L_Data.req, distributes L_Data.ind, optionally bridges to a real bus."""

    def __init__(self, server: SecureServer, xknx: XKNX | None) -> None:
        """Initialize."""
        self.server = server
        self.xknx = xknx

    @staticmethod
    def _rewrite(
        raw: bytes,
        code: CEMIMessageCode,
        source: IndividualAddress | None,
        error: bool = False,
    ) -> bytes:
        """Change the message code, replace source 0.0.0 and set the confirm flag."""
        data = bytearray(raw)
        data[0] = code.value
        addil = data[1]
        ctrl1 = 2 + addil
        src = ctrl1 + 2
        if len(data) >= src + 2:
            if source is not None and data[src : src + 2] == b"\x00\x00":
                data[src : src + 2] = source.to_knx()
            if code == CEMIMessageCode.L_DATA_CON:
                data[ctrl1] = (data[ctrl1] & ~0x01) | int(
                    error
                )  # bit 0: confirm flag (0 = ok)
        return bytes(data)

    async def handle_from_client(self, channel: Channel, raw: bytes) -> None:
        """Process a cEMI frame received over a tunnelling connection."""
        session = channel.session
        if not raw:
            return
        if raw[0] != CEMIMessageCode.L_DATA_REQ.value:
            log.warning(
                "    only L_Data.req is handled on tunnelling connections (got %#04x)",
                raw[0],
            )
            return
        indication = self._rewrite(
            raw, CEMIMessageCode.L_DATA_IND, channel.individual_address
        )
        error = False
        if self.xknx is not None:
            try:
                cemi = CEMIFrame.from_knx(
                    self._rewrite(
                        raw, CEMIMessageCode.L_DATA_REQ, channel.individual_address
                    )
                )
                await self.xknx.knxip_interface.send_cemi(cemi)
                log.info(
                    "    forwarded to the real bus via xknx (%s)",
                    self.xknx.knxip_interface.connection_config.connection_type.name,
                )
            except (
                CommunicationError,
                CouldNotParseCEMI,
                UnsupportedCEMIMessage,
            ) as err:
                log.warning(
                    "    forwarding to the real bus failed: %s -> negative L_Data.con",
                    err,
                )
                error = True
        confirmation = self._rewrite(
            raw, CEMIMessageCode.L_DATA_CON, channel.individual_address, error=error
        )
        session.send_cemi_to_client(channel, confirmation, "L_Data.con")
        if not error:
            self.distribute(indication, exclude=channel)

    def distribute(self, indication: bytes, exclude: Channel | None) -> None:
        """Send an L_Data.ind to all other tunnelling connections."""
        for other in self.server.tunnel_channels():
            if other is exclude:
                continue
            other.session.send_cemi_to_client(other, indication, "L_Data.ind")

    def cemi_from_backend(self, raw: bytes) -> None:
        """Distribute frames the xknx backend received from the real bus."""
        if raw and raw[0] == CEMIMessageCode.L_DATA_IND.value:
            log.info("<<< bus (xknx backend): %s", describe_cemi(raw))
            self.distribute(raw, exclude=None)


# ---------------------------------------------------------------------------
# UDP discovery endpoint (multicast + unicast control endpoint)
# ---------------------------------------------------------------------------


class DiscoveryProtocol(asyncio.DatagramProtocol):
    """Answers SEARCH_REQUEST(_EXTENDED), DESCRIPTION_REQUEST and plain CONNECT_REQUEST."""

    def __init__(self, server: SecureServer, label: str) -> None:
        """Initialize."""
        self.server = server
        self.label = label
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Store transport."""
        self.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle a UDP datagram."""
        if (
            addr[0] == self.server.config.local_ip
            and addr[1] == self.server.config.port
        ):
            return  # our own multicast echo
        log.debug("<<< raw udp %s from %s: %s", self.label, addr, data.hex())
        try:
            frame, _ = KNXIPFrame.from_knx(data)
        except CouldNotParseKNXIP as err:
            log.info(
                "<<< udp %s from %s:%d: unparsable %s (%s)",
                self.label,
                addr[0],
                addr[1],
                data.hex(),
                err,
            )
            return
        log.info(
            "<<< udp %s from %s:%d: %s", self.label, addr[0], addr[1], fmt_frame(frame)
        )
        body = frame.body
        description = self.server.description

        def reply_to(hpai: HPAI, response: Any) -> None:
            target = addr if hpai.route_back else hpai.addr_tuple
            self.server.send_udp(response, target)

        if isinstance(body, SearchRequestExtended):
            if description.search_request_extended_matches(body):
                reply_to(
                    body.discovery_endpoint, description.search_response(extended=True)
                )
            else:
                log.info("    SRPs not satisfied - no SEARCH_RESPONSE_EXTENDED sent")
        elif isinstance(body, SearchRequest):
            reply_to(
                body.discovery_endpoint, description.search_response(extended=False)
            )
        elif isinstance(body, DescriptionRequest):
            reply_to(body.control_endpoint, description.description_response())
        elif isinstance(body, ConnectRequest):
            log.warning(
                "    plain UDP CONNECT_REQUEST: this PoC only serves connections inside a secure TCP session"
            )
            if not self.server.config.secure_tunnelling:
                log.warning(
                    "    (plain UDP tunnelling is not implemented, even though --allow-plain is set)"
                )
        elif isinstance(body, SessionRequest):
            log.warning(
                "    SESSION_REQUEST over UDP ignored: secure sessions require TCP (03_08_09 §2.2.3.3)"
            )
        else:
            log.info("    ignored")

    def error_received(self, exc: Exception) -> None:
        """Log socket errors."""
        log.warning("udp %s error: %s", self.label, exc)


# ---------------------------------------------------------------------------
# The server
# ---------------------------------------------------------------------------


class SecureServer:
    """Owns the sockets, sessions, channels and shared state."""

    def __init__(self, config: ServerConfig, xknx: XKNX | None = None) -> None:
        """Initialize."""
        self.config = config
        self.device_authentication_code = derive_device_authentication_password(
            config.device_authentication_password
        )
        self._user_keys: dict[str, bytes] = {}
        self.description = DeviceDescription(config, self)
        self.properties = PropertyStore(config)
        self.bus = VirtualBus(self, xknx)
        self.sessions: set[ClientSession] = set()
        self.session_ids: set[int] = set()
        self.channels: dict[int, Channel] = {}
        self.unicast: asyncio.DatagramTransport | None = None
        self.multicast: asyncio.DatagramTransport | None = None
        self.tcp_server: asyncio.AbstractServer | None = None

    def user_key(self, password: str) -> bytes:
        """PBKDF2 of a user password, cached (65536 iterations)."""
        if password not in self._user_keys:
            self._user_keys[password] = derive_user_password(password)
        return self._user_keys[password]

    # ----- sessions and channels -----

    def new_session_id(self) -> int:
        """Return a unique non-zero session id (0 is reserved for multicast)."""
        while True:
            session_id = secrets.randbelow(0xFFFF) + 1
            if session_id not in self.session_ids:
                self.session_ids.add(session_id)
                return session_id

    def tunnel_channels(self) -> list[Channel]:
        """All open tunnelling channels."""
        return [
            c
            for c in self.channels.values()
            if c.connection_type == ConnectRequestType.TUNNEL_CONNECTION
        ]

    def tunnel_free(self, individual_address: IndividualAddress) -> bool:
        """Return True if no open tunnelling connection uses this address."""
        return all(
            c.individual_address != individual_address for c in self.tunnel_channels()
        )

    def new_channel(
        self,
        session: ClientSession,
        connection_type: ConnectRequestType,
        individual_address: IndividualAddress | None,
        layer: TunnellingLayer | None,
    ) -> Channel | None:
        """Allocate a communication channel id (1..255)."""
        for channel_id in range(1, 256):
            if channel_id not in self.channels:
                channel = Channel(
                    channel_id=channel_id,
                    connection_type=connection_type,
                    session=session,
                    individual_address=individual_address,
                    layer=layer,
                )
                self.channels[channel_id] = channel
                session.channels[channel_id] = channel
                self.touch_channel(channel)
                return channel
        return None

    def touch_channel(self, channel: Channel) -> None:
        """Restart the 120 s heartbeat timeout of a channel."""
        channel.last_seen = time.monotonic()
        if channel.alive_timer is not None:
            channel.alive_timer.cancel()
        channel.alive_timer = asyncio.get_running_loop().call_later(
            CONNECTION_ALIVE_TIME, self._channel_timeout, channel
        )

    def _channel_timeout(self, channel: Channel) -> None:
        log.warning(
            "    channel %d: no CONNECTIONSTATE_REQUEST for %d s -> DISCONNECT_REQUEST",
            channel.channel_id,
            CONNECTION_ALIVE_TIME,
        )
        channel.session.send_wrapped(
            DisconnectRequest(
                communication_channel_id=channel.channel_id,
                control_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
            )
        )
        self.release_channel(channel, reason="heartbeat timeout")

    def release_channel(self, channel: Channel, reason: str) -> None:
        """Close a channel."""
        if channel.alive_timer is not None:
            channel.alive_timer.cancel()
            channel.alive_timer = None
        self.channels.pop(channel.channel_id, None)
        channel.session.channels.pop(channel.channel_id, None)
        log.info(
            "    channel %d (%s%s) closed: %s",
            channel.channel_id,
            channel.connection_type.name,
            f" {channel.individual_address}" if channel.individual_address else "",
            reason,
        )

    # ----- sockets -----

    def send_udp(self, body: Any, target: tuple[str, int]) -> None:
        """Send a plain frame from the unicast control endpoint."""
        frame = KNXIPFrame.init_from_body(body)
        log.info(">>> udp to %s:%d: %s", target[0], target[1], fmt_frame(frame))
        assert self.unicast is not None
        self.unicast.sendto(frame.to_knx(), target)

    async def start(self) -> None:
        """Open the UDP sockets and the TCP listener."""
        loop = asyncio.get_running_loop()
        self.unicast, _ = await loop.create_datagram_endpoint(
            lambda: DiscoveryProtocol(self, "unicast"),
            local_addr=(self.config.local_ip, self.config.port),
            reuse_port=sys.platform != "win32",
        )
        try:
            sock = UDPTransport.create_multicast_sock(
                self.config.local_ip, (MULTICAST_GROUP, self.config.port)
            )
            self.multicast, _ = await loop.create_datagram_endpoint(
                lambda: DiscoveryProtocol(self, "multicast"), sock=sock
            )
        except OSError as err:
            log.warning(
                "multicast listener not available (%s) - discovery via multicast will not work",
                err,
            )
        self.tcp_server = await loop.create_server(
            lambda: ClientSession(self),
            host=self.config.local_ip,
            port=self.config.port,
        )
        log.info(
            "KNXnet/IP Secure server listening on %s:%d (udp + tcp), multicast %s",
            self.config.local_ip,
            self.config.port,
            MULTICAST_GROUP,
        )
        log.info(
            "  name %r, IA %s, tunnelling addresses %s",
            self.config.name,
            self.config.individual_address,
            ", ".join(str(ia) for ia in self.config.tunnel_addresses),
        )
        log.info(
            "  device authentication code %r, users %s%s",
            self.config.device_authentication_password,
            self.config.user_passwords,
            f", any other user: {self.config.any_user_password!r}"
            if self.config.any_user_password
            else "",
        )

    async def stop(self) -> None:
        """Close everything."""
        for session in list(self.sessions):
            session.close(SecureSessionStatusCode.STATUS_CLOSE, "server shutdown")
        if self.tcp_server:
            self.tcp_server.close()
            await self.tcp_server.wait_closed()
        if self.multicast:
            self.multicast.close()
        if self.unicast:
            self.unicast.close()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Command line."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--ip", help="local IPv4 address to bind and announce (default: auto)"
    )
    parser.add_argument(
        "--port", type=int, default=KNXIP_PORT, help="UDP/TCP port (default 3671)"
    )
    parser.add_argument(
        "--name", default="xknx PoC Secure Server", help="friendly name in discovery"
    )
    parser.add_argument(
        "--ia",
        default="15.15.0",
        help="individual address of the server device (default 15.15.0)",
    )
    parser.add_argument(
        "--tunnel-ia",
        default="15.15.1,15.15.2,15.15.3",
        help="comma separated tunnelling addresses (default 15.15.1,15.15.2,15.15.3)",
    )
    parser.add_argument(
        "--serial",
        default="0000786b6e78",
        help="KNX serial number, 6 bytes hex (default 0000786b6e78)",
    )
    parser.add_argument(
        "--mac",
        default="02786b6e7800",
        help="MAC address announced in DIBs, 6 bytes hex",
    )
    parser.add_argument(
        "--manufacturer",
        type=lambda v: int(v, 0),
        default=0,
        help="KNX manufacturer id (default 0)",
    )
    parser.add_argument(
        "--device-auth",
        default="authcode",
        help="device authentication code / password (default 'authcode')",
    )
    parser.add_argument(
        "--user",
        action="append",
        default=[],
        metavar="ID:PASSWORD",
        help="user password, repeatable. Default: 1:commissioning, 2:tunnel1, 3:tunnel2, 4:tunnel3",
    )
    parser.add_argument(
        "--any-user",
        metavar="PASSWORD",
        help="accept any user id not configured with --user if this password matches (handy to see which user id ETS tries)",
    )
    parser.add_argument(
        "--allow-plain",
        action="store_true",
        help="announce tunnelling/device management as not secured (so ETS may try plain connections)",
    )
    parser.add_argument(
        "--backend",
        choices=["none", "routing", "tunnelling"],
        default="none",
        help="bridge L_Data frames to a real bus through an xknx connection (default none)",
    )
    parser.add_argument("--gateway-ip", help="gateway for --backend tunnelling")
    parser.add_argument("--log-file", help="also write the log to this file")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="also show raw bytes and xknx debug logs",
    )
    return parser.parse_args(argv)


def setup_logging(args: argparse.Namespace) -> None:
    """Configure logging: timestamps with milliseconds, optional file."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if args.log_file:
        handlers.append(logging.FileHandler(args.log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s.%(msecs)03d %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )
    logging.getLogger("xknx").setLevel(
        logging.DEBUG if args.verbose else logging.WARNING
    )


async def run(args: argparse.Namespace) -> None:
    """Start the server (and the optional xknx backend) until Ctrl-C."""
    local_ip = args.ip or await get_default_local_ip()
    if not local_ip:
        raise SystemExit("could not determine local IP, use --ip")
    users: dict[int, str] = {}
    tunnel_addresses = [
        IndividualAddress(ia.strip()) for ia in args.tunnel_ia.split(",") if ia.strip()
    ]
    if not args.user:
        users[1] = "commissioning"
        for index in range(len(tunnel_addresses)):
            users[2 + index] = f"tunnel{index + 1}"
    for spec in args.user:
        user_id, _, password = spec.partition(":")
        users[int(user_id, 0)] = password
    config = ServerConfig(
        local_ip=local_ip,
        port=args.port,
        name=args.name,
        serial_number=bytes.fromhex(args.serial),
        mac_address=bytes.fromhex(args.mac),
        manufacturer_id=args.manufacturer,
        individual_address=IndividualAddress(args.ia),
        tunnel_addresses=tunnel_addresses,
        device_authentication_password=args.device_auth,
        user_passwords=users,
        any_user_password=args.any_user,
        secure_tunnelling=not args.allow_plain,
        secure_device_management=not args.allow_plain,
    )

    xknx: XKNX | None = None
    if args.backend != "none":
        if args.backend == "routing":
            connection_config = ConnectionConfig(
                connection_type=ConnectionType.ROUTING,
                local_ip=local_ip,
                individual_address=config.individual_address,
            )
        else:
            if not args.gateway_ip:
                raise SystemExit("--backend tunnelling needs --gateway-ip")
            connection_config = ConnectionConfig(
                connection_type=ConnectionType.TUNNELING_TCP, gateway_ip=args.gateway_ip
            )
        xknx = XKNX(connection_config=connection_config)

    server = SecureServer(config, xknx)
    if xknx is not None:
        original_cemi_received = xknx.knxip_interface.cemi_received

        def cemi_received(raw_cemi: bytes) -> None:
            server.bus.cemi_from_backend(raw_cemi)
            original_cemi_received(raw_cemi)

        xknx.knxip_interface.cemi_received = cemi_received  # type: ignore[method-assign]
        await xknx.start()
        log.info("xknx backend connected (%s)", args.backend)

    await server.start()
    log.info("Waiting for ETS. Stop with Ctrl-C.")
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        await server.stop()
        if xknx is not None:
            await xknx.stop()


def main() -> None:
    """Entry point."""
    args = parse_args()
    setup_logging(args)
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        log.info("stopped")


if __name__ == "__main__":
    main()
