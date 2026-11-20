"""
A KNXnet/IP tunnelling server in front of the bus connection of an XKNX instance.

KNXnet/IP tunnelling clients - another xknx, Home Assistant, a commissioning
tool - connect to the server and send and receive their telegrams through the
interface the XKNX instance is connected with, e.g. a KNX USB interface: the
server makes that interface a KNXnet/IP interface ("USB to IP bridge").
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
import logging
import random
import socket
import sys
from typing import TYPE_CHECKING, Final, cast
import uuid

from xknx.cemi import CEMIFrame, CEMIMessageCode
from xknx.core.connection_state import XknxConnectionState, XknxConnectionType
from xknx.exceptions import (
    CommunicationError,
    ConversionError,
    CouldNotParseCEMI,
    CouldNotParseKNXIP,
    IncompleteKNXIPFrame,
    UnsupportedCEMIMessage,
)
from xknx.io.const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT, XKNX_SERIAL_NUMBER
from xknx.io.data_connection import SequenceVerdict
from xknx.io.transport import UDPTransport
from xknx.knxip import (
    DIB,
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
    DIBServiceFamily,
    DIBSuppSVCFamilies,
    DIBTunnelingInfo,
    DIBTypeCode,
    DisconnectRequest,
    DisconnectResponse,
    ErrorCode,
    HostProtocol,
    KNXIPBody,
    KNXIPFrame,
    KNXIPHeader,
    KNXIPServiceType,
    KNXMedium,
    SearchRequest,
    SearchRequestExtended,
    SearchRequestParameterType,
    SearchResponse,
    SearchResponseExtended,
    TunnellingAck,
    TunnellingFeatureGet,
    TunnellingFeatureInfo,
    TunnellingFeatureResponse,
    TunnellingFeatureSet,
    TunnellingFeatureType,
    TunnellingLayer,
    TunnellingRequest,
)
from xknx.knxip.dib import TunnelingSlotStatus
from xknx.profile.const import (
    ResourceDevicePropertyId,
    ResourceGenericPropertyId,
    ResourceKNXNETIPPropertyId,
    ResourceObjectType,
)
from xknx.telegram import IndividualAddress
from xknx.telegram.apci import ReturnCode

from .connection import Peer, ServerConnection, TunnelInfo
from .properties import (
    PropertyElements,
    property_info_indication,
    property_service_response,
)
from .raw_cemi import LDataFrame

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")
knx_logger = logging.getLogger("xknx.knx")

# Device Descriptor Type 0 "IP (prim) TP1 (sec)" - KNX v01.10.01 - Resources 03.05.01 -
# §4.1.2.2
DEFAULT_DEVICE_DESCRIPTOR: Final = 0x091A
# without a value reported by the interface: what a standard frame carries
DEFAULT_MAX_APDU_LENGTH: Final = 15
# a server waits this long for the DISCONNECT_RESPONSEs when it stops
DISCONNECT_RESPONSE_TIMEOUT: Final = 1.0
# A TCP connection without KNXnet/IP connection is closed after 10 s without
# received octets - KNX v01.06.02 - Core 03.08.02 - §8.4.3.2
TCP_IDLE_TIMEOUT: Final = 10.0
# A mapped point-to-point partner stays with its tunnel this long after the last frame:
# the connection_timeout_timer of the transport layer - KNX v01.02.03 - Transport
# Layer 03.03.04 - §4
POINT_TO_POINT_TIMEOUT: Final = 6.0
# TPCI of T_Disconnect - KNX v01.02.03 - Transport Layer 03.03.04 - §2
_T_DISCONNECT: Final = 0x81
MAX_DEVICE_MANAGEMENT_CONNECTIONS: Final = 4
_EPHEMERAL_PORT_ATTEMPTS: Final = 20
_DYNAMIC_PORTS_START: Final = 49152

# Interface Feature values - KNX v01.07.01 - Tunnelling 03.08.04 - §3.6:
# only cEMI is allowed for KNXnet/IP Tunnelling (§3.6.2, §3.6.6)
_SUPPORTED_EMI_TYPE_CEMI: Final = 0x0004
_ACTIVE_EMI_TYPE_CEMI: Final = 0x03
_FEATURE_SIZES: Final = {
    TunnellingFeatureType.SUPPORTED_EMI_TYPE: 2,
    TunnellingFeatureType.DEVICE_DESCRIPTOR_TYPE_0: 2,
    TunnellingFeatureType.BUS_CONNECTION_STATUS: 1,
    TunnellingFeatureType.MANUFACTURER_CODE: 2,
    TunnellingFeatureType.ACTIVE_EMI_TYPE: 1,
    TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS: 2,
    TunnellingFeatureType.MAX_APDU_LENGTH: 2,
    TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE: 1,
}

# PID_KNXNETIP_DEVICE_CAPABILITIES: Device Management, Tunnelling -
# KNX v01.07.03 - Device Management 03.08.03 - §2.5.19
_DEVICE_CAPABILITIES: Final = 0x0003
# PID_KNXNETIP_DEVICE_STATE bit 0 "KNX Fault" - KNX v01.07.03 - Device Management
# 03.08.03 - §2.5.20
_DEVICE_STATE_KNX_FAULT: Final = 0x01


def _refusal(status_code: ErrorCode, connection_type: ConnectRequestType) -> KNXIPFrame:
    """
    Return the CONNECT_RESPONSE refusing a connection.

    Communication channel 0, an empty HPAI and for a tunnel a CRD with address
    0.0.0 - clients evaluate the status code only.
    """
    return KNXIPFrame.init_from_body(
        ConnectResponse(
            status_code=status_code,
            crd=ConnectResponseData(
                request_type=connection_type,
                individual_address=IndividualAddress(0),
            ),
        )
    )


class _Refused(Exception):
    """A CONNECT_REQUEST is refused with this status code."""

    def __init__(self, status_code: ErrorCode) -> None:
        """Initialize _Refused exception."""
        super().__init__(status_code.name)
        self.status_code = status_code


class _UDPPeer(Peer):
    """A UDP endpoint of a client, reached from the server's socket."""

    protocol = HostProtocol.IPV4_UDP

    __slots__ = ("_address", "_server")

    def __init__(self, server: KNXIPTunnellingServer, address: tuple[str, int]) -> None:
        """Initialize _UDPPeer class."""
        self._server = server
        self._address = address

    @property
    def address(self) -> tuple[str, int]:
        """Return the IP address and port of the client endpoint."""
        return self._address

    def send(self, knxipframe: KNXIPFrame) -> None:
        """Send a KNX/IP frame to the endpoint."""
        self._server.send_udp(knxipframe, self._address)


class _UDPProtocol(asyncio.DatagramProtocol):
    """Hand the datagrams received on a socket of the server to the server."""

    def __init__(self, server: KNXIPTunnellingServer) -> None:
        """Initialize _UDPProtocol class."""
        self._server = server

    def datagram_received(self, data: bytes, addr: tuple[str | int, int]) -> None:
        """Handle a received datagram. Callback."""
        self._server.datagram_received(data, (str(addr[0]), addr[1]))

    def error_received(self, exc: Exception) -> None:
        """Log an error of the socket. Callback."""
        logger.debug("KNXnet/IP server UDP socket error: %s", exc)


class _TCPStream(asyncio.Protocol, Peer):
    """
    A TCP connection of a client.

    The KNXnet/IP frames are framed by the total length of their header; a frame
    with a header that isn't well-formed closes the connection, a frame of an
    unsupported service is skipped - KNX v01.06.02 - Core 03.08.02 - §8.4.3.3.
    """

    protocol = HostProtocol.IPV4_TCP

    def __init__(self, server: KNXIPTunnellingServer) -> None:
        """Initialize _TCPStream class."""
        self._server = server
        self._transport: asyncio.Transport | None = None
        self._buffer = b""
        self._peername: tuple[str, int] = ("", 0)
        self._idle_handle: asyncio.TimerHandle | None = None

    @property
    def address(self) -> tuple[str, int]:
        """Return the IP address and port of the client."""
        return self._peername

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Register the connection. Callback."""
        self._transport = cast(asyncio.Transport, transport)
        peername = transport.get_extra_info("peername")
        if peername:
            self._peername = (str(peername[0]), int(peername[1]))
        self._server.tcp_stream_opened(self)
        self.restart_idle_timeout()

    def data_received(self, data: bytes) -> None:
        """Handle received octets. Callback."""
        # the ProactorEventLoop on Windows may pass a bytearray
        raw = self._buffer + bytes(data)
        self._buffer = b""
        if not self._server.has_connections(self):
            self.restart_idle_timeout()
        while raw and self._transport is not None:
            try:
                knxipframe, raw = KNXIPFrame.from_knx(raw)
            except IncompleteKNXIPFrame:
                self._buffer = raw
                return
            except (CouldNotParseKNXIP, ConversionError) as err:
                header_valid = (
                    len(raw) >= KNXIPHeader.HEADERLENGTH
                    and raw[0] == KNXIPHeader.HEADERLENGTH
                    and raw[1] == KNXIPHeader.PROTOCOLVERSION
                )
                total_length = int.from_bytes(raw[4:6], "big") if header_valid else 0
                if total_length < KNXIPHeader.HEADERLENGTH:
                    logger.debug(
                        "KNXnet/IP server: invalid KNX/IP header from %s, closing: %s",
                        self._peername,
                        raw.hex(),
                    )
                    self.close()
                    return
                if len(raw) < total_length:
                    self._buffer = raw
                    return
                knx_logger.debug(
                    "KNXnet/IP server: skipping unsupported frame from %s: %s",
                    self._peername,
                    err,
                )
                raw = raw[total_length:]
                continue
            self._server.frame_received(knxipframe, self)

    def connection_lost(self, exc: Exception | None) -> None:
        """Close the connections of this TCP connection. Callback."""
        self._transport = None
        self._buffer = b""
        if self._idle_handle is not None:
            self._idle_handle.cancel()
            self._idle_handle = None
        self._server.tcp_stream_closed(self)

    def send(self, knxipframe: KNXIPFrame) -> None:
        """Send a KNX/IP frame over the connection."""
        if self._transport is None or self._transport.is_closing():
            return
        knx_logger.debug("Sending to %s: %s", self._peername, knxipframe)
        self._transport.write(knxipframe.to_knx())

    def restart_idle_timeout(self) -> None:
        """Close the connection after TCP_IDLE_TIMEOUT seconds unless a KNXnet/IP connection opens."""
        if self._idle_handle is not None:
            self._idle_handle.cancel()
        self._idle_handle = asyncio.get_running_loop().call_later(
            TCP_IDLE_TIMEOUT, self._idle_timeout
        )

    def _idle_timeout(self) -> None:
        """Close the connection if it carries no KNXnet/IP connection. Callback."""
        self._idle_handle = None
        if not self._server.has_connections(self):
            logger.debug(
                "KNXnet/IP server: closing idle TCP connection %s", self._peername
            )
            self.close()

    def close(self) -> None:
        """Close the TCP connection."""
        if self._transport is not None:
            self._transport.close()


def _default_mac_address() -> bytes:
    """Return the MAC address of this host - or a random one if it can't be found."""
    return uuid.getnode().to_bytes(6, "big")


class KNXIPTunnellingServer:
    """
    A KNXnet/IP tunnelling server forwarding to the bus connection of an XKNX instance.

    Tunnelling clients connect over UDP or TCP (KNX v01.07.01 - Tunnelling
    03.08.04 - §2). Each tunnel gets one of `individual_addresses`; their L_Data.req
    frames are sent through the interface of `xknx` - frames with source 0.0.0
    with the tunnel's address - and the L_Data.con goes back to the tunnel that
    sent the frame. L_Data.ind frames from the bus go to every tunnel, a frame a
    tunnel or `xknx` itself sent goes to the other tunnels as L_Data.ind as well;
    a point-to-point frame only to the tunnel with its destination address
    (§2.2.2). `xknx` receives everything as before and also sees the frames the
    tunnels send.

    `busmonitor=True` is for an interface in bus monitor mode (e.g.
    `USBTunnel(busmonitor=True)`): then only one bus monitor tunnel is accepted
    and gets the L_Busmon.ind frames. Device management connections
    (KNX v01.07.03 - Device Management 03.08.03 - §4.2) read the server's own Device
    Object and KNXnet/IP Parameter Object; every Property is read-only.

    The interface of `xknx` receives point-to-point frames for its own address
    only (and acknowledges only those on the bus). So with `map_point_to_point`
    (the default, but for a routing connection, which receives every frame) a
    tunnel's point-to-point frames go out with the interface's own address, and
    the partner's frames to it go back to that tunnel only, not to `xknx`. A
    partner belongs to one tunnel until `POINT_TO_POINT_TIMEOUT` after the last
    frame or a T_Disconnect; another tunnel's frames to it get a negative
    L_Data.con meanwhile. The source address is part of the MAC of a Data Secure
    frame, so a tunnel's mapped Data Secure frames can't be verified by the
    partner; and while a tunnel is connected to a partner, `xknx`'s own
    connection to it gets no answers.
    """

    __slots__ = (
        "_bus_connected",
        "_channel",
        "_connections",
        "_disconnect_responses",
        "_forwarder",
        "_mac_address",
        "_multicast_transport",
        "_partners",
        "_port",
        "_send_queue",
        "_serial_number",
        "_tcp_server",
        "_tcp_streams",
        "_transport",
        "_unregister_callbacks",
        "busmonitor",
        "device_descriptor",
        "discovery",
        "heartbeat_timeout",
        "individual_address",
        "individual_addresses",
        "local_ip",
        "manufacturer_code",
        "map_point_to_point",
        "max_apdu_length",
        "medium",
        "multicast_group",
        "multicast_port",
        "name",
        "tcp",
        "xknx",
    )

    def __init__(
        self,
        xknx: XKNX,
        individual_addresses: Sequence[IndividualAddress | str],
        local_ip: str = "0.0.0.0",
        port: int = DEFAULT_MCAST_PORT,
        name: str = "xknx bridge",
        discovery: bool = True,
        tcp: bool = True,
        busmonitor: bool = False,
        multicast_group: str = DEFAULT_MCAST_GRP,
        multicast_port: int = DEFAULT_MCAST_PORT,
        individual_address: IndividualAddress | str | None = None,
        serial_number: bytes | None = None,
        mac_address: bytes | None = None,
        medium: KNXMedium | None = None,
        device_descriptor: int = DEFAULT_DEVICE_DESCRIPTOR,
        manufacturer_code: int = 0x0000,
        max_apdu_length: int | None = None,
        heartbeat_timeout: float = 120.0,
        map_point_to_point: bool | None = None,
    ) -> None:
        """
        Initialize KNXIPTunnellingServer class.

        `individual_addresses` are the addresses of the tunnels, one per tunnel
        (PID_ADDITIONAL_INDIVIDUAL_ADDRESSES); `individual_address` is the
        server's own address, by default `xknx.current_address`. `port` is the
        UDP and TCP port of the control and data endpoints; with `discovery` the
        server also answers SEARCH_REQUESTs sent to `multicast_group` on
        `multicast_port`. The MAC address defaults to the host's, the serial
        number is derived from it. `medium` and `max_apdu_length` default to
        what a KNX USB interface reported, else TP1 and 15. `map_point_to_point`
        (None: unless `xknx` is connected by routing) sends the tunnels'
        point-to-point frames with the interface's own address, see above.
        """
        self.xknx = xknx
        self.individual_addresses = [
            IndividualAddress(address) for address in individual_addresses
        ]
        if not self.individual_addresses:
            raise ConversionError("A tunnelling server needs individual addresses")
        if len(set(self.individual_addresses)) != len(self.individual_addresses):
            raise ConversionError(
                "The individual addresses of the tunnels must be unique"
            )
        self.local_ip = local_ip
        self.name = name
        self.discovery = discovery
        self.tcp = tcp
        self.busmonitor = busmonitor
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port
        self.individual_address = (
            IndividualAddress(individual_address)
            if individual_address is not None
            else None
        )
        self._mac_address = mac_address or _default_mac_address()
        if len(self._mac_address) != 6:
            raise ConversionError("A MAC address has 6 octets")
        self._serial_number = serial_number or (
            XKNX_SERIAL_NUMBER[:2] + self._mac_address[2:]
        )
        if len(self._serial_number) != 6:
            raise ConversionError("A KNX serial number has 6 octets")
        self.medium = medium
        self.device_descriptor = device_descriptor
        self.manufacturer_code = manufacturer_code
        self.max_apdu_length = max_apdu_length
        self.heartbeat_timeout = heartbeat_timeout
        self.map_point_to_point = map_point_to_point

        self._port = port
        self._transport: asyncio.DatagramTransport | None = None
        self._multicast_transport: asyncio.DatagramTransport | None = None
        self._tcp_server: asyncio.Server | None = None
        self._tcp_streams: set[_TCPStream] = set()
        self._connections: dict[int, ServerConnection] = {}
        self._channel = 0
        self._disconnect_responses: dict[int, asyncio.Future[None]] = {}
        self._send_queue: asyncio.Queue[tuple[ServerConnection, LDataFrame]] = (
            asyncio.Queue()
        )
        self._forwarder: asyncio.Task[None] | None = None
        self._unregister_callbacks: list[Callable[[], None]] = []
        self._bus_connected = False
        # mapped point-to-point partners: the tunnel and the time of the last frame
        self._partners: dict[IndividualAddress, tuple[ServerConnection, float]] = {}

    ####################
    #
    # START STOP
    #
    ####################

    @property
    def port(self) -> int:
        """Return the port of the control and data endpoints - the bound one after `start()`."""
        return self._port

    @property
    def tunnels(self) -> list[TunnelInfo]:
        """Return the open tunnels."""
        return [
            connection.info()
            for connection in self._connections.values()
            if connection.is_tunnel
        ]

    async def start(self) -> None:
        """Open the UDP (and TCP) endpoints. Raise OSError when a socket can't be opened."""
        if self._transport is not None:
            return
        requested_port = self._port
        # The port of an ephemeral TCP port may be unusable for UDP - on Windows
        # ranges of ports are excluded per protocol -, then a random port of the
        # dynamic range is tried.
        attempts = _EPHEMERAL_PORT_ATTEMPTS if requested_port == 0 and self.tcp else 1
        for attempt in range(1, attempts + 1):
            try:
                await self._open_endpoints(
                    requested_port
                    if attempt == 1
                    else random.randrange(_DYNAMIC_PORTS_START, 65536)
                )
            except OSError:
                await self.stop()
                self._port = requested_port
                if attempt == attempts:
                    raise
            except BaseException:
                await self.stop()
                self._port = requested_port
                raise
            else:
                break
        self._bus_connected = self._bus_is_connected()
        self._unregister_callbacks = [
            self.xknx.cemi_handler.register_cemi_received_cb(self._cemi_received),
            self.xknx.connection_manager.register_connection_state_changed_cb(
                self._connection_state_changed
            ),
        ]
        self._forwarder = asyncio.create_task(
            self._forward_requests(), name="KNXnet/IP server forwarder"
        )
        logger.info(
            "KNXnet/IP tunnelling server listening on %s:%s",
            self.local_ip,
            self._port,
        )

    async def _open_endpoints(self, port: int) -> None:
        """Open the UDP socket, the multicast listener and the TCP server on a port."""
        loop = asyncio.get_running_loop()
        join_multicast = self.discovery and self.multicast_port == port
        if self.tcp:
            # an ephemeral port is taken from TCP
            self._tcp_server = await loop.create_server(
                lambda: _TCPStream(self),
                host=self.local_ip,
                port=port,
            )
            port = self._tcp_server.sockets[0].getsockname()[1]
        sock = self._create_udp_socket(join_multicast, port)
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: _UDPProtocol(self), sock=sock
        )
        self._port = self._transport.get_extra_info("sockname")[1]
        if self.discovery and not join_multicast:
            await self._start_multicast_listener()

    def _create_udp_socket(self, join_multicast: bool, port: int) -> socket.socket:
        """
        Return the socket of the control and data endpoints.

        Joined to the multicast group it is the discovery endpoint as well. Bound to
        a specific address Linux and macOS don't deliver multicast datagrams to it,
        so it is bound to all interfaces then.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            if join_multicast and sys.platform != "win32":
                # share the discovery port with other multicast listeners
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("" if join_multicast else self.local_ip, port))
            if join_multicast:
                try:
                    sock.setsockopt(
                        socket.IPPROTO_IP,
                        socket.IP_ADD_MEMBERSHIP,
                        socket.inet_aton(self.multicast_group)
                        + socket.inet_aton(self.local_ip),
                    )
                except OSError as err:
                    logger.warning(
                        "KNXnet/IP server could not join %s for discovery: %s",
                        self.multicast_group,
                        err,
                    )
            if self.local_ip != "0.0.0.0":
                # search responses to a multicast HPAI leave through this interface
                sock.setsockopt(
                    socket.IPPROTO_IP,
                    socket.IP_MULTICAST_IF,
                    socket.inet_aton(self.local_ip),
                )
            sock.setblocking(False)
        except BaseException:
            sock.close()
            raise
        return sock

    async def _start_multicast_listener(self) -> None:
        """Receive the SEARCH_REQUESTs on a discovery port other than the server's port."""
        try:
            sock = UDPTransport.create_multicast_sock(
                self.local_ip, (self.multicast_group, self.multicast_port)
            )
        except OSError as err:
            logger.warning(
                "KNXnet/IP server could not listen on %s:%s for discovery: %s",
                self.multicast_group,
                self.multicast_port,
                err,
            )
            return
        (
            self._multicast_transport,
            _,
        ) = await asyncio.get_running_loop().create_datagram_endpoint(
            lambda: _UDPProtocol(self), sock=sock
        )

    async def stop(self) -> None:
        """Disconnect every client and close the endpoints."""
        for unregister in self._unregister_callbacks:
            unregister()
        self._unregister_callbacks = []
        connections = list(self._connections.values())
        waiting: list[asyncio.Future[None]] = []
        loop = asyncio.get_running_loop()
        for connection in connections:
            response: asyncio.Future[None] = loop.create_future()
            self._disconnect_responses[connection.communication_channel] = response
            waiting.append(response)
            self._send_disconnect_request(connection)
        if waiting:
            await asyncio.wait(waiting, timeout=DISCONNECT_RESPONSE_TIMEOUT)
        self._disconnect_responses.clear()
        for connection in connections:
            self._remove_connection(connection)
        if self._forwarder is not None:
            self._forwarder.cancel()
            self._forwarder = None
        for stream in list(self._tcp_streams):
            stream.close()
        if self._tcp_server is not None:
            self._tcp_server.close()
            await self._tcp_server.wait_closed()
            self._tcp_server = None
        if self._multicast_transport is not None:
            self._multicast_transport.close()
            self._multicast_transport = None
        if self._transport is not None:
            self._transport.close()
            self._transport = None

    ####################
    #
    # RECEIVING
    #
    ####################

    def send_udp(self, knxipframe: KNXIPFrame, address: tuple[str, int]) -> None:
        """Send a KNX/IP frame from the server's UDP socket."""
        if self._transport is None:
            return
        knx_logger.debug("Sending to %s:%s: %s", address[0], address[1], knxipframe)
        try:
            self._transport.sendto(knxipframe.to_knx(), address)
        except OSError as err:
            logger.debug("KNXnet/IP server could not send to %s: %s", address, err)

    def datagram_received(self, data: bytes, address: tuple[str, int]) -> None:
        """Parse and handle a datagram received on a UDP socket."""
        try:
            knxipframe, _ = KNXIPFrame.from_knx(data)
        except (CouldNotParseKNXIP, ConversionError) as err:
            knx_logger.debug(
                "KNXnet/IP server: unsupported frame from %s: %s in %s",
                address,
                err,
                data.hex(),
            )
            self._refuse_unparsable_connect_request(data, address)
            return
        self.frame_received(knxipframe, _UDPPeer(self, address))

    def frame_received(self, knxipframe: KNXIPFrame, source: Peer) -> None:
        """Handle a received KNX/IP frame."""
        knx_logger.debug("Received from %s: %s", source.address, knxipframe)
        try:
            self._handle_frame(knxipframe.body, source)
        except Exception:  # pylint: disable=broad-exception-caught
            # a bug must not stop the receiving of the socket or connection
            logger.exception("KNXnet/IP server could not handle %s", knxipframe)

    def _handle_frame(self, body: KNXIPBody, source: Peer) -> None:
        """Handle the body of a received KNX/IP frame by its service."""
        if isinstance(body, TunnellingRequest):
            self._tunnelling_request_received(body, source)
        elif isinstance(body, TunnellingAck | DeviceConfigurationAck):
            if (
                connection := self._connection(body.communication_channel_id, source)
            ) and not connection.tcp:
                connection.alive()
                connection.ack_received(body.sequence_counter, body.status_code)
        elif isinstance(body, ConnectionStateRequest):
            self._connectionstate_request_received(body, source)
        elif isinstance(body, SearchRequestExtended):
            self._search_request_received(body.discovery_endpoint, source, body)
        elif isinstance(body, SearchRequest):
            self._search_request_received(body.discovery_endpoint, source, None)
        elif isinstance(body, DescriptionRequest):
            self._description_request_received(body, source)
        elif isinstance(body, ConnectRequest):
            self._connect_request_received(body, source)
        elif isinstance(body, DisconnectRequest):
            self._disconnect_request_received(body, source)
        elif isinstance(body, DisconnectResponse):
            if response := self._disconnect_responses.get(
                body.communication_channel_id
            ):
                if not response.done():
                    response.set_result(None)
        elif isinstance(body, TunnellingFeatureGet | TunnellingFeatureSet):
            self._tunnelling_feature_received(body, source)
        elif isinstance(body, DeviceConfigurationRequest):
            self._device_configuration_request_received(body, source)
        else:
            knx_logger.debug("KNXnet/IP server ignores %s", body)

    def _resolve(self, hpai: HPAI, source: Peer) -> Peer | None:
        """
        Return where a client's endpoint is reached, or None for an invalid HPAI.

        A route back HPAI is the source of the frame; over TCP only route back is
        allowed, a UDP frame with a TCP HPAI is discarded, an HPAI with only the
        IP address or only the port zero is invalid - KNX v01.06.02 - Core
        03.08.02 - §8.6.2.
        """
        if source.protocol is HostProtocol.IPV4_TCP:
            if hpai.protocol is HostProtocol.IPV4_TCP and not hpai.route_back:
                return None
            return source
        if hpai.protocol is not HostProtocol.IPV4_UDP:
            return None
        if hpai.route_back and hpai.port == 0:
            return source
        if hpai.route_back or hpai.port == 0:
            return None
        return _UDPPeer(self, hpai.addr_tuple)

    def _connection(
        self, communication_channel: int, source: Peer
    ) -> ServerConnection | None:
        """Return the connection of a channel - only through the TCP connection or over UDP it was opened with."""
        connection = self._connections.get(communication_channel)
        if connection is None:
            return None
        if connection.tcp:
            return connection if connection.data_peer is source else None
        return connection if source.protocol is HostProtocol.IPV4_UDP else None

    def _sequenced(
        self,
        connection: ServerConnection,
        sequence_counter: int,
        ack: Callable[[], KNXIPBody],
    ) -> bool:
        """
        Acknowledge a request of a client and return whether to process it.

        The expected sequence counter is acknowledged and processed, one less than
        expected is acknowledged again and discarded, any other is discarded -
        KNX v01.07.01 - Tunnelling 03.08.04 - §2.6.1. On TCP the sequence counter
        isn't evaluated and nothing is acknowledged (§2.6.2).
        """
        if connection.tcp:
            connection.alive()
            return True
        verdict = connection.sequence_in.evaluate(sequence_counter)
        if verdict is SequenceVerdict.OUT_OF_ORDER:
            knx_logger.debug(
                "KNXnet/IP server: discarding frame of channel %s with sequence counter %s, expected %s",
                connection.communication_channel,
                sequence_counter,
                connection.sequence_in.expected,
            )
            return False
        connection.data_peer.send(KNXIPFrame.init_from_body(ack()))
        if verdict is SequenceVerdict.REPEATED:
            return False
        connection.alive()
        return True

    ####################
    #
    # DISCOVERY AND SELF DESCRIPTION
    #
    ####################

    def _local_ip_for(self, peer: Peer) -> str:
        """Return the server's IP address the peer reaches it at."""
        if self.local_ip != "0.0.0.0":
            return self.local_ip
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            try:
                # connecting a UDP socket only selects the route
                sock.connect((peer.address[0], DEFAULT_MCAST_PORT))
                return str(sock.getsockname()[0])
            except OSError:
                return "0.0.0.0"

    def _control_endpoint(self, peer: Peer) -> HPAI:
        """Return the HPAI of the server's control and data endpoint for a peer."""
        if peer.protocol is HostProtocol.IPV4_TCP:
            return HPAI(protocol=HostProtocol.IPV4_TCP)
        return HPAI(ip_addr=self._local_ip_for(peer), port=self._port)

    def _service_families(self) -> DIBSuppSVCFamilies:
        """
        Return the supported service families.

        Core v2 and Tunnelling v2 need TCP - KNX v01.06.02 - Core 03.08.02 - §9.2.
        """
        version = 2 if self.tcp else 1
        dib = DIBSuppSVCFamilies()
        dib.families = [
            DIBSuppSVCFamilies.Family(DIBServiceFamily.CORE, version),
            DIBSuppSVCFamilies.Family(DIBServiceFamily.DEVICE_MANAGEMENT, 1),
            DIBSuppSVCFamilies.Family(DIBServiceFamily.TUNNELING, version),
        ]
        return dib

    def _device_information(self) -> DIBDeviceInformation:
        """
        Return the Device information DIB - KNX v01.06.02 - Core 03.08.02 - §7.5.4.2.

        A device without KNXnet/IP Routing sets the routing multicast address to 0.0.0.0.
        """
        dib = DIBDeviceInformation()
        dib.knx_medium = self._medium()
        dib.programming_mode = False
        dib.individual_address = self._own_address()
        dib.serial_number = self._serial_number.hex(":")
        dib.multicast_address = "0.0.0.0"
        dib.mac_address = self._mac_address.hex(":")
        dib.name = self.name
        return dib

    def _extended_device_information(self) -> DIB:
        """Return the Extended Device Information DIB - KNX v01.06.02 - Core 03.08.02 - §7.5.4.9."""
        dib = DIBGeneric()
        dib.dtc = DIBTypeCode.ADDITIONAL_DEVICE_INFO
        dib.data = (
            # Medium Status: COMMUNICATION_IMPOSSIBLE
            bytes((0x00 if self._bus_is_connected() else 0x01, 0x00))
            + self._max_apdu_length().to_bytes(2, "big")
            + self.device_descriptor.to_bytes(2, "big")
        )
        return dib

    def _tunnelling_information(self) -> DIBTunnelingInfo:
        """Return the Tunnelling Information DIB - KNX v01.06.02 - Core 03.08.02 - §7.5.4.8."""
        used = self._used_addresses()
        dib = DIBTunnelingInfo(
            slots={
                address: TunnelingSlotStatus(
                    usable=True, authorized=True, free=address not in used
                )
                for address in self.individual_addresses
            }
        )
        dib.max_apdu_length = self._max_apdu_length()
        return dib

    def _search_request_received(
        self,
        discovery_endpoint: HPAI,
        source: Peer,
        extended: SearchRequestExtended | None,
    ) -> None:
        """
        Answer a SEARCH_REQUEST or SEARCH_REQUEST_EXTENDED - KNX v01.06.02 - Core 03.08.02 - §7.6.

        Discovery is UDP only. The server is never in programming mode, so it
        doesn't answer a "Select By Programming Mode" SRP, nor one with an unknown
        type and the mandatory bit set.
        """
        if source.protocol is not HostProtocol.IPV4_UDP:
            return
        if (peer := self._resolve(discovery_endpoint, source)) is None:
            return
        response: SearchResponse
        if extended is None:
            response = SearchResponse(control_endpoint=self._control_endpoint(peer))
            response.dibs = [self._device_information(), self._service_families()]
        else:
            families = self._service_families()
            for srp in extended.srps:
                if srp.type is SearchRequestParameterType.SELECT_BY_PROGRAMMING_MODE:
                    return
                if srp.type is SearchRequestParameterType.SELECT_BY_MAC_ADDRESS:
                    if srp.data != self._mac_address:
                        return
                elif srp.type is SearchRequestParameterType.SELECT_BY_SERVICE:
                    try:
                        family = DIBServiceFamily(srp.data[0])
                    except ValueError:
                        return
                    if not families.supports(family, srp.data[1]):
                        return
                elif (
                    srp.type is not SearchRequestParameterType.REQUEST_DIBS
                    and srp.mandatory
                ):
                    return
            response = SearchResponseExtended(
                control_endpoint=self._control_endpoint(peer)
            )
            # the basic set and the Tunnelling Information - supported DIBs that
            # a "Request DIBs" SRP lists are among them
            response.dibs = [
                self._device_information(),
                self._extended_device_information(),
                families,
                self._tunnelling_information(),
            ]
        peer.send(KNXIPFrame.init_from_body(response))

    def _description_request_received(
        self, request: DescriptionRequest, source: Peer
    ) -> None:
        """
        Answer a DESCRIPTION_REQUEST - KNX v01.06.02 - Core 03.08.02 - §7.7.

        The Tunnelling Information DIB is not allowed in a DESCRIPTION_RESPONSE (§7.5.4.8).
        """
        if (peer := self._resolve(request.control_endpoint, source)) is None:
            return
        response = DescriptionResponse()
        response.dibs = [self._device_information(), self._service_families()]
        peer.send(KNXIPFrame.init_from_body(response))

    ####################
    #
    # CONNECTIONS
    #
    ####################

    def _connect_request_received(self, request: ConnectRequest, source: Peer) -> None:
        """Answer a CONNECT_REQUEST - KNX v01.06.02 - Core 03.08.02 - §7.8.1."""
        control_peer = self._resolve(request.control_endpoint, source)
        data_peer = self._resolve(request.data_endpoint, source)
        if control_peer is None or data_peer is None:
            return
        try:
            connection = self._open_connection(request, control_peer, data_peer)
        except _Refused as refused:
            logger.debug(
                "KNXnet/IP server refuses connection from %s: %s",
                control_peer.address,
                refused.status_code.name,
            )
            control_peer.send(
                _refusal(refused.status_code, request.cri.connection_type)
            )
            return
        control_peer.send(
            KNXIPFrame.init_from_body(
                ConnectResponse(
                    communication_channel=connection.communication_channel,
                    data_endpoint=self._control_endpoint(data_peer),
                    crd=ConnectResponseData(
                        request_type=connection.connection_type,
                        individual_address=connection.individual_address,
                    ),
                )
            )
        )
        logger.info(
            "KNXnet/IP server opened channel %s for %s%s",
            connection.communication_channel,
            data_peer.address,
            f" with {connection.individual_address}"
            if connection.individual_address is not None
            else "",
        )

    def _open_connection(
        self, request: ConnectRequest, control_peer: Peer, data_peer: Peer
    ) -> ServerConnection:
        """Return a new connection for a CONNECT_REQUEST. Raise _Refused with the status code otherwise."""
        cri = request.cri
        individual_address: IndividualAddress | None = None
        if cri.connection_type is ConnectRequestType.TUNNEL_CONNECTION:
            individual_address = self._tunnel_address(
                cri.knx_layer, cri.individual_address
            )
        elif cri.connection_type is ConnectRequestType.DEVICE_MGMT_CONNECTION:
            if (
                sum(
                    not connection.is_tunnel
                    for connection in self._connections.values()
                )
                >= MAX_DEVICE_MANAGEMENT_CONNECTIONS
            ):
                raise _Refused(ErrorCode.E_NO_MORE_CONNECTIONS)
        else:
            raise _Refused(ErrorCode.E_CONNECTION_TYPE)
        channel = self._free_channel()
        connection = ServerConnection(
            communication_channel=channel,
            connection_type=cri.connection_type,
            control_peer=control_peer,
            data_peer=data_peer,
            local_ip=self._local_ip_for(data_peer),
            heartbeat_timeout=self.heartbeat_timeout,
            on_failure=self._connection_failed,
            individual_address=individual_address,
            layer=cri.knx_layer,
        )
        self._connections[channel] = connection
        connection.start()
        return connection

    def _tunnel_address(
        self, layer: TunnellingLayer, requested: IndividualAddress | None
    ) -> IndividualAddress:
        """
        Return the individual address of a new tunnel. Raise _Refused otherwise.

        KNX v01.07.01 - Tunnelling 03.08.04 - §5.4.3.3: no free address at all is
        E_NO_MORE_CONNECTIONS, an unsupported layer E_TUNNELLING_LAYER; with an
        Extended CRI an address that is no tunnelling address is
        E_NO_TUNNELLING_ADDRESS, one in use E_CONNECTION_IN_USE. Only one
        tunnel is open with an interface in bus monitor mode (§2.2.4), and
        without a bus connection a tunnel is refused with E_KNX_CONNECTION
        (§5.4.3.3.3).
        """
        used = self._used_addresses()
        free = [address for address in self.individual_addresses if address not in used]
        if not free or (self.busmonitor and used):
            raise _Refused(ErrorCode.E_NO_MORE_CONNECTIONS)
        supported_layer = (
            TunnellingLayer.BUSMONITOR_LAYER
            if self.busmonitor
            else TunnellingLayer.DATA_LINK_LAYER
        )
        if layer is not supported_layer:
            raise _Refused(ErrorCode.E_TUNNELLING_LAYER)
        if not self._bus_is_connected():
            raise _Refused(ErrorCode.E_KNX_CONNECTION)
        if requested is None:
            return free[0]
        if requested not in self.individual_addresses:
            raise _Refused(ErrorCode.E_NO_TUNNELLING_ADDRESS)
        if requested in used:
            raise _Refused(ErrorCode.E_CONNECTION_IN_USE)
        return requested

    def _used_addresses(self) -> set[IndividualAddress]:
        """Return the individual addresses of the open tunnels."""
        return {
            connection.individual_address
            for connection in self._connections.values()
            if connection.individual_address is not None
        }

    def _free_channel(self) -> int:
        """Return an unused communication channel id - the ids are handed out in turn."""
        for _ in range(255):
            self._channel = self._channel % 255 + 1
            if self._channel not in self._connections:
                return self._channel
        raise _Refused(ErrorCode.E_NO_MORE_CONNECTIONS)

    def _connectionstate_request_received(
        self, request: ConnectionStateRequest, source: Peer
    ) -> None:
        """
        Answer a CONNECTIONSTATE_REQUEST - KNX v01.06.02 - Core 03.08.02 - §7.8.4.

        E_CONNECTION_ID for an unknown channel, E_KNX_CONNECTION for a tunnel while
        the interface has no bus connection.
        """
        if (peer := self._resolve(request.control_endpoint, source)) is None:
            return
        channel = request.communication_channel_id
        status_code = ErrorCode.E_NO_ERROR
        if (connection := self._connection(channel, source)) is None:
            status_code = ErrorCode.E_CONNECTION_ID
        else:
            connection.alive()
            if connection.is_tunnel and not self._bus_is_connected():
                status_code = ErrorCode.E_KNX_CONNECTION
        peer.send(
            KNXIPFrame.init_from_body(
                ConnectionStateResponse(
                    communication_channel_id=channel, status_code=status_code
                )
            )
        )

    def _disconnect_request_received(
        self, request: DisconnectRequest, source: Peer
    ) -> None:
        """Answer a DISCONNECT_REQUEST and close the connection - KNX v01.06.02 - Core 03.08.02 - §5.5."""
        channel = request.communication_channel_id
        connection = self._connection(channel, source)
        peer = self._resolve(request.control_endpoint, source)
        if peer is None:
            if connection is None:
                return
            peer = connection.control_peer
        peer.send(
            KNXIPFrame.init_from_body(
                DisconnectResponse(
                    communication_channel_id=channel,
                    status_code=ErrorCode.E_NO_ERROR
                    if connection is not None
                    else ErrorCode.E_CONNECTION_ID,
                )
            )
        )
        if connection is not None:
            logger.info("KNXnet/IP server: client closed channel %s", channel)
            self._remove_connection(connection)

    def _send_disconnect_request(self, connection: ServerConnection) -> None:
        """Send a DISCONNECT_REQUEST to the client's control endpoint."""
        connection.control_peer.send(
            KNXIPFrame.init_from_body(
                DisconnectRequest(
                    communication_channel_id=connection.communication_channel,
                    control_endpoint=self._control_endpoint(connection.control_peer),
                )
            )
        )

    def _connection_failed(self, connection: ServerConnection) -> None:
        """
        Terminate a connection whose heartbeat timed out or whose request stayed unacknowledged.

        A TCP connection whose last KNXnet/IP connection the server closes due to
        a timeout is closed immediately - KNX v01.06.02 - Core 03.08.02 - §8.4.3.2.
        """
        if self._connections.get(connection.communication_channel) is not connection:
            return
        logger.info(
            "KNXnet/IP server terminates channel %s",
            connection.communication_channel,
        )
        self._send_disconnect_request(connection)
        self._remove_connection(connection)
        if isinstance(connection.data_peer, _TCPStream) and not self.has_connections(
            connection.data_peer
        ):
            connection.data_peer.close()

    def _remove_connection(self, connection: ServerConnection) -> None:
        """Forget a closed connection; its individual address is free again."""
        if self._connections.get(connection.communication_channel) is connection:
            del self._connections[connection.communication_channel]
        for partner, (owner, _) in list(self._partners.items()):
            if owner is connection:
                del self._partners[partner]
        connection.stop()
        if isinstance(connection.data_peer, _TCPStream) and not self.has_connections(
            connection.data_peer
        ):
            connection.data_peer.restart_idle_timeout()

    def has_connections(self, stream: _TCPStream) -> bool:
        """Return whether a TCP connection carries a KNXnet/IP connection."""
        return any(
            connection.data_peer is stream for connection in self._connections.values()
        )

    def tcp_stream_opened(self, stream: _TCPStream) -> None:
        """Track a new TCP connection."""
        self._tcp_streams.add(stream)

    def tcp_stream_closed(self, stream: _TCPStream) -> None:
        """Close the KNXnet/IP connections of a closed TCP connection - KNX v01.06.02 - Core 03.08.02 - §8.4.3.5."""
        self._tcp_streams.discard(stream)
        for connection in list(self._connections.values()):
            if connection.data_peer is stream:
                self._remove_connection(connection)

    ####################
    #
    # TUNNELLING
    #
    ####################

    def _tunnelling_request_received(
        self, request: TunnellingRequest, source: Peer
    ) -> None:
        """Acknowledge and handle a TUNNELLING_REQUEST of a tunnel."""
        connection = self._connection(request.communication_channel_id, source)
        if connection is None or not connection.is_tunnel:
            return
        if not self._sequenced(
            connection,
            request.sequence_counter,
            lambda: TunnellingAck(
                communication_channel_id=connection.communication_channel,
                sequence_counter=request.sequence_counter,
            ),
        ):
            return
        self._tunnel_cemi_received(connection, request.raw_cemi)

    def _tunnel_cemi_received(self, connection: ServerConnection, raw: bytes) -> None:
        """
        Handle the cEMI frame of a tunnel.

        An L_Data.req is queued for the interface - with source 0.0.0 with the
        tunnel's address (KNX v01.07.01 - Tunnelling 03.08.04 - §2.2.2); a bus
        monitor tunnel sends nothing (§2.4). M_PropRead.req and M_PropWrite.req
        are answered for the server's own Interface Objects. M_Reset.req doesn't
        restart the interface, which the other clients use as well.
        """
        code = raw[0] if raw else None
        if code == CEMIMessageCode.L_DATA_REQ.value:
            if connection.layer is TunnellingLayer.BUSMONITOR_LAYER:
                logger.debug("KNXnet/IP server: a bus monitor tunnel can't send")
                return
            if (frame := LDataFrame.parse(raw)) is None:
                logger.debug("KNXnet/IP server: invalid L_Data.req %s", raw.hex())
                return
            if frame.source.raw == 0 and connection.individual_address is not None:
                frame = frame.with_source(connection.individual_address)
            self._send_queue.put_nowait((connection, frame))
            return
        if (
            response := property_service_response(
                raw, self._property_elements(connection)
            )
        ) is not None:
            self._send_cemi(connection, response)
            return
        logger.debug("KNXnet/IP server ignores cEMI frame of a tunnel: %s", raw.hex())

    def _send_cemi(self, connection: ServerConnection, raw: bytes) -> None:
        """Queue a cEMI frame for a client - TUNNELLING_REQUEST or DEVICE_CONFIGURATION_REQUEST."""
        channel = connection.communication_channel
        if connection.is_tunnel:
            connection.send_request(
                lambda sequence_counter: TunnellingRequest(
                    communication_channel_id=channel,
                    sequence_counter=sequence_counter,
                    raw_cemi=raw,
                )
            )
        else:
            connection.send_request(
                lambda sequence_counter: DeviceConfigurationRequest(
                    communication_channel_id=channel,
                    sequence_counter=sequence_counter,
                    raw_cemi=raw,
                )
            )

    async def _forward_requests(self) -> None:
        """
        Send the L_Data.req frames of the tunnels through the interface. Worker task.

        The L_Data.con goes back to the tunnel that sent the frame - a negative one
        when the interface couldn't send it; a frame sent goes to the other tunnels
        and to `xknx` as L_Data.ind.
        """
        while True:
            connection, frame = await self._send_queue.get()
            if (
                self._connections.get(connection.communication_channel)
                is not connection
            ):
                continue
            tunnel_source = frame.source
            if (mapped := self._map_outgoing(connection, frame)) is None:
                logger.debug(
                    "KNXnet/IP server: %s is connected to another tunnel",
                    frame.destination,
                )
                self._send_cemi(
                    connection,
                    frame.with_code(CEMIMessageCode.L_DATA_CON, confirm_error=True).raw,
                )
                continue
            try:
                raw_confirmation = await self.xknx.cemi_handler.send_cemi_frame(
                    mapped.cemi_frame()
                )
            except (CommunicationError, ConversionError) as err:
                logger.debug("KNXnet/IP server could not send %s: %s", frame, err)
                raw_confirmation = frame.with_code(
                    CEMIMessageCode.L_DATA_CON, confirm_error=True
                ).raw
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception("KNXnet/IP server could not send %s", frame)
                raw_confirmation = frame.with_code(
                    CEMIMessageCode.L_DATA_CON, confirm_error=True
                ).raw
            if (
                mapped is not frame
                and (sent := LDataFrame.parse(raw_confirmation)) is not None
            ):
                # the tunnel sees its own address in its confirmation
                raw_confirmation = sent.with_source(tunnel_source).raw
            if self._connections.get(connection.communication_channel) is connection:
                self._send_cemi(connection, raw_confirmation)
            confirmation = LDataFrame.parse(raw_confirmation)
            if confirmation is None or confirmation.confirm_error:
                continue
            indication = confirmation.with_code(CEMIMessageCode.L_DATA_IND)
            self._indicate(indication, exclude=connection)
            self._indicate_locally(indication)

    def _map_outgoing(
        self, connection: ServerConnection, frame: LDataFrame
    ) -> LDataFrame | None:
        """
        Return the frame to send for a tunnel's L_Data.req - None: its partner is another tunnel's.

        A point-to-point frame from the tunnel's own address gets the interface's
        address, and its partner is mapped to the tunnel (see the class docstring).
        """
        own_address = self._own_address()
        destination = frame.destination
        if (
            not self._maps_point_to_point()
            or not isinstance(destination, IndividualAddress)
            or connection.individual_address is None
            or frame.source != connection.individual_address
            or frame.source == own_address
        ):
            return frame
        now = asyncio.get_running_loop().time()
        if (entry := self._partners.get(destination)) is not None:
            owner, last_frame = entry
            if (
                owner is not connection
                and self._connections.get(owner.communication_channel) is owner
                and now - last_frame < POINT_TO_POINT_TIMEOUT
            ):
                return None
        if frame.tpci == _T_DISCONNECT:
            self._partners.pop(destination, None)
        else:
            self._partners[destination] = (connection, now)
        return frame.with_source(own_address)

    def _maps_point_to_point(self) -> bool:
        """Return whether point-to-point frames of the tunnels are mapped to the interface's address."""
        if self.map_point_to_point is not None:
            return self.map_point_to_point
        return self.xknx.connection_manager.connection_type not in (
            XknxConnectionType.ROUTING,
            XknxConnectionType.ROUTING_SECURE,
        )

    def _partner_frame_received(self, frame: LDataFrame) -> bool:
        """Pass a frame of a mapped point-to-point partner to its tunnel only; whether it was one."""
        source = frame.source
        if (
            not isinstance(frame.destination, IndividualAddress)
            or frame.destination != self._own_address()
            or (entry := self._partners.get(source)) is None
        ):
            return False
        connection, _ = entry
        if self._connections.get(connection.communication_channel) is not connection:
            del self._partners[source]
            return False
        assert connection.individual_address is not None
        if frame.tpci == _T_DISCONNECT:
            del self._partners[source]
        else:
            self._partners[source] = (connection, asyncio.get_running_loop().time())
        self._send_cemi(
            connection, frame.with_destination(connection.individual_address).raw
        )
        return True

    def _cemi_received(self, raw: bytes) -> bool:
        """
        Pass a cEMI frame from the interface on to the tunnels. Callback.

        An L_Data.con here confirms a frame `xknx` itself sent, which goes to the
        tunnels as L_Data.ind. A frame of a mapped point-to-point partner goes to
        its tunnel only and is taken from `xknx` (returns True).
        """
        code = raw[0] if raw else None
        if code == CEMIMessageCode.L_DATA_IND.value:
            if (frame := LDataFrame.parse(raw)) is not None:
                if self._partner_frame_received(frame):
                    return True
                self._indicate(frame)
        elif code == CEMIMessageCode.L_DATA_CON.value:
            if (frame := LDataFrame.parse(raw)) is not None and not frame.confirm_error:
                self._indicate(frame.with_code(CEMIMessageCode.L_DATA_IND))
        elif code == CEMIMessageCode.L_BUSMON_IND.value:
            for connection in list(self._connections.values()):
                if connection.layer is TunnellingLayer.BUSMONITOR_LAYER:
                    self._send_cemi(connection, raw)
        return False

    def _indicate(
        self, frame: LDataFrame, exclude: ServerConnection | None = None
    ) -> None:
        """
        Send an L_Data.ind to the data link layer tunnels.

        Group frames go to every tunnel, a point-to-point frame only to the tunnel
        with its destination address - KNX v01.07.01 - Tunnelling 03.08.04 - §2.2.2.
        """
        destination = frame.destination
        for connection in list(self._connections.values()):
            if (
                connection is exclude
                or not connection.is_tunnel
                or connection.layer is not TunnellingLayer.DATA_LINK_LAYER
            ):
                continue
            if (
                isinstance(destination, IndividualAddress)
                and destination != connection.individual_address
            ):
                continue
            self._send_cemi(connection, frame.raw)

    def _indicate_locally(self, frame: LDataFrame) -> None:
        """Let `xknx` receive a frame a tunnel sent, as if it came from the bus."""
        try:
            cemi = CEMIFrame.from_knx(frame.raw)
        except (CouldNotParseCEMI, UnsupportedCEMIMessage):
            return
        self.xknx.cemi_handler.handle_cemi_frame(cemi)

    ####################
    #
    # TUNNELLING FEATURES
    #
    ####################

    def _tunnelling_feature_received(
        self, request: TunnellingFeatureGet | TunnellingFeatureSet, source: Peer
    ) -> None:
        """
        Answer a TUNNELLING_FEATURE_GET or TUNNELLING_FEATURE_SET - KNX v01.07.01 - Tunnelling 03.08.04 - §3.

        They are acknowledged like a TUNNELLING_REQUEST (§3.1).
        """
        connection = self._connection(request.communication_channel_id, source)
        if connection is None or not connection.is_tunnel:
            return
        if not self._sequenced(
            connection,
            request.sequence_counter,
            lambda: TunnellingAck(
                communication_channel_id=connection.communication_channel,
                sequence_counter=request.sequence_counter,
            ),
        ):
            return
        feature = request.feature_type
        address_before = connection.individual_address
        if isinstance(request, TunnellingFeatureSet):
            return_code, data = self._set_feature(connection, feature, request.data)
        else:
            # every Interface Feature xknx parses is supported - an unknown one
            # can't be parsed and is ignored without acknowledgement (§3.5)
            return_code = ReturnCode.E_SUCCESS
            data = self._feature_value(connection, feature)
        channel = connection.communication_channel
        connection.send_request(
            lambda sequence_counter: TunnellingFeatureResponse(
                communication_channel_id=channel,
                sequence_counter=sequence_counter,
                feature_type=feature,
                return_code=return_code,
                data=data,
            )
        )
        if connection.individual_address != address_before:
            self._send_feature_info(
                connection, TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS
            )

    def _feature_value(
        self, connection: ServerConnection, feature: TunnellingFeatureType
    ) -> bytes:
        """Return the value of an Interface Feature - KNX v01.07.01 - Tunnelling 03.08.04 - §3.6."""
        if feature is TunnellingFeatureType.SUPPORTED_EMI_TYPE:
            return _SUPPORTED_EMI_TYPE_CEMI.to_bytes(2, "big")
        if feature is TunnellingFeatureType.DEVICE_DESCRIPTOR_TYPE_0:
            return self.device_descriptor.to_bytes(2, "big")
        if feature is TunnellingFeatureType.BUS_CONNECTION_STATUS:
            return bytes((self._bus_is_connected(),))
        if feature is TunnellingFeatureType.MANUFACTURER_CODE:
            return self.manufacturer_code.to_bytes(2, "big")
        if feature is TunnellingFeatureType.ACTIVE_EMI_TYPE:
            return bytes((_ACTIVE_EMI_TYPE_CEMI,))
        if feature is TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS:
            assert connection.individual_address is not None
            return connection.individual_address.to_knx()
        if feature is TunnellingFeatureType.MAX_APDU_LENGTH:
            return self._max_apdu_length().to_bytes(2, "big")
        # TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE
        return bytes((connection.feature_info_enabled,))

    def _set_feature(
        self, connection: ServerConnection, feature: TunnellingFeatureType, data: bytes
    ) -> tuple[ReturnCode, bytes]:
        """
        Set an Interface Feature and return the Return Code and value of the response.

        Only the tunnel's individual address and the Interface Feature Info service
        Enable can be set; a value of wrong size is E_DATA_TYPE_CONFLICT, an
        invalid one E_DATA_VOID - KNX v01.07.01 - Tunnelling 03.08.04 - §3.3. A
        new individual address must not be used in the server: one of the tunnel
        addresses or the server's own is E_DATA_VOID (§3.6.7).
        """
        size = _FEATURE_SIZES[feature]
        if feature not in (
            TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS,
            TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE,
        ):
            return ReturnCode.E_ACCESS_READ_ONLY, data
        # an odd value is sent padded to an even length
        value = (
            data[:size]
            if len(data) == size + size % 2 and not any(data[size:])
            else data
        )
        if len(value) != size:
            return ReturnCode.E_DATA_TYPE_CONFLICT, data
        if feature is TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE:
            if value[0] > 1:
                return ReturnCode.E_DATA_VOID, value
            connection.feature_info_enabled = bool(value[0])
            return ReturnCode.E_SUCCESS, value
        address = IndividualAddress.from_knx(value)
        if address == connection.individual_address:
            return ReturnCode.E_SUCCESS, value
        if (
            not address.raw
            or address in self.individual_addresses
            or address == self._own_address()
            or address in self._used_addresses()
        ):
            return ReturnCode.E_DATA_VOID, value
        connection.individual_address = address
        return ReturnCode.E_SUCCESS, value

    def _send_feature_info(
        self, connection: ServerConnection, feature: TunnellingFeatureType
    ) -> None:
        """Send a TUNNELLING_FEATURE_INFO if the tunnel enabled them - KNX v01.07.01 - Tunnelling 03.08.04 - §3.4."""
        if not connection.feature_info_enabled:
            return
        value = self._feature_value(connection, feature)
        channel = connection.communication_channel
        connection.send_request(
            lambda sequence_counter: TunnellingFeatureInfo(
                communication_channel_id=channel,
                sequence_counter=sequence_counter,
                feature_type=feature,
                data=value,
            )
        )

    def _connection_state_changed(self, state: XknxConnectionState) -> None:
        """Inform the clients about a changed bus connection. Callback."""
        connected = state is XknxConnectionState.CONNECTED
        if connected == self._bus_connected:
            return
        self._bus_connected = connected
        for connection in list(self._connections.values()):
            if connection.is_tunnel:
                self._send_feature_info(
                    connection, TunnellingFeatureType.BUS_CONNECTION_STATUS
                )
            else:
                # PID_KNXNETIP_DEVICE_STATE is evented - KNX v01.07.03 - Device
                # Management 03.08.03 - §2.5.20
                self._send_cemi(
                    connection,
                    property_info_indication(
                        ResourceObjectType.OBJECT_KNXNETIP_PARAMETER.value,
                        ResourceKNXNETIPPropertyId.PID_KNXNETIP_DEVICE_STATE.value,
                        self._device_state(),
                    ),
                )

    ####################
    #
    # DEVICE MANAGEMENT
    #
    ####################

    def _device_configuration_request_received(
        self, request: DeviceConfigurationRequest, source: Peer
    ) -> None:
        """
        Acknowledge and answer a DEVICE_CONFIGURATION_REQUEST - KNX v01.07.03 - Device Management 03.08.03 - §4.2.6.

        M_PropRead.req and M_PropWrite.req are answered; M_Reset.req and the
        function property services are acknowledged only.
        """
        connection = self._connection(request.communication_channel_id, source)
        if connection is None or connection.is_tunnel:
            return
        if not self._sequenced(
            connection,
            request.sequence_counter,
            lambda: DeviceConfigurationAck(
                communication_channel_id=connection.communication_channel,
                sequence_counter=request.sequence_counter,
            ),
        ):
            return
        response = property_service_response(
            request.raw_cemi, self._property_elements(connection)
        )
        if response is None:
            logger.debug(
                "KNXnet/IP server ignores device management cEMI frame: %s",
                request.raw_cemi.hex(),
            )
            return
        self._send_cemi(connection, response)

    def _property_elements(self, connection: ServerConnection) -> PropertyElements:
        """Return the Properties of the server's Device Object and KNXnet/IP Parameter Object."""

        def elements(object_type: int, property_id: int) -> list[bytes] | None:
            if object_type == ResourceObjectType.OBJECT_DEVICE.value:
                device_properties: dict[int, list[bytes]] = {
                    ResourceGenericPropertyId.PID_OBJECT_TYPE.value: [
                        object_type.to_bytes(2, "big")
                    ],
                    ResourceGenericPropertyId.PID_SERIAL_NUMBER.value: [
                        self._serial_number
                    ],
                    ResourceGenericPropertyId.PID_MANUFACTURER_ID.value: [
                        self.manufacturer_code.to_bytes(2, "big")
                    ],
                    ResourceDevicePropertyId.PID_MAX_APDU_LENGTH.value: [
                        self._max_apdu_length().to_bytes(2, "big")
                    ],
                    ResourceDevicePropertyId.PID_DEVICE_DESCRIPTOR.value: [
                        self.device_descriptor.to_bytes(2, "big")
                    ],
                }
                return device_properties.get(property_id)
            if object_type == ResourceObjectType.OBJECT_KNXNETIP_PARAMETER.value:
                knxnetip_properties: dict[int, list[bytes]] = {
                    ResourceGenericPropertyId.PID_OBJECT_TYPE.value: [
                        object_type.to_bytes(2, "big")
                    ],
                    ResourceKNXNETIPPropertyId.PID_PROJECT_INSTALLATION_ID.value: [
                        bytes(2)
                    ],
                    ResourceKNXNETIPPropertyId.PID_KNX_INDIVIDUAL_ADDRESS.value: [
                        self._own_address().to_knx()
                    ],
                    ResourceKNXNETIPPropertyId.PID_ADDITIONAL_INDIVIDUAL_ADDRESSES.value: [
                        address.to_knx() for address in self.individual_addresses
                    ],
                    ResourceKNXNETIPPropertyId.PID_CURRENT_IP_ADDRESS.value: [
                        socket.inet_aton(connection.local_ip)
                    ],
                    ResourceKNXNETIPPropertyId.PID_MAC_ADDRESS.value: [
                        self._mac_address
                    ],
                    ResourceKNXNETIPPropertyId.PID_SYSTEM_SETUP_MULTICAST_ADDRESS.value: [
                        socket.inet_aton(DEFAULT_MCAST_GRP)
                    ],
                    ResourceKNXNETIPPropertyId.PID_KNXNETIP_DEVICE_CAPABILITIES.value: [
                        _DEVICE_CAPABILITIES.to_bytes(2, "big")
                    ],
                    ResourceKNXNETIPPropertyId.PID_KNXNETIP_DEVICE_STATE.value: [
                        self._device_state()
                    ],
                    ResourceKNXNETIPPropertyId.PID_FRIENDLY_NAME.value: [
                        bytes((char,))
                        for char in self.name.encode("latin_1", errors="replace")[
                            :30
                        ].ljust(30, b"\0")
                    ],
                    # identifiers of the tunnelling addresses: index 1..n of
                    # PID_ADDITIONAL_INDIVIDUAL_ADDRESSES - KNX v01.07.03 - Device
                    # Management 03.08.03 - §2.5.29.3
                    ResourceKNXNETIPPropertyId.PID_TUNNELLING_ADDRESSES.value: [
                        bytes((index,))
                        for index in range(1, len(self.individual_addresses) + 1)
                    ],
                }
                return knxnetip_properties.get(property_id)
            return None

        return elements

    def _device_state(self) -> bytes:
        """Return PID_KNXNETIP_DEVICE_STATE."""
        return bytes((0 if self._bus_is_connected() else _DEVICE_STATE_KNX_FAULT,))

    ####################
    #
    # STATE
    #
    ####################

    def _bus_is_connected(self) -> bool:
        """Return whether the interface of `xknx` is connected to the bus."""
        return self.xknx.connection_manager.state is XknxConnectionState.CONNECTED

    def _own_address(self) -> IndividualAddress:
        """Return the server's own individual address."""
        return self.individual_address or self.xknx.current_address

    def _medium(self) -> KNXMedium:
        """Return the KNX medium - configured, reported by a KNX USB interface, or TP1."""
        if self.medium is not None:
            return self.medium
        if (info := self.xknx.knxip_interface.usb_interface_info()) is not None:
            return info.medium
        return KNXMedium.TP1

    def _max_apdu_length(self) -> int:
        """Return the maximum APDU length - configured, reported by a KNX USB interface, or 15."""
        if self.max_apdu_length is not None:
            return self.max_apdu_length
        if (info := self.xknx.knxip_interface.usb_interface_info()) is not None:
            return info.max_apdu_length
        return DEFAULT_MAX_APDU_LENGTH

    def _refuse_unparsable_connect_request(
        self, data: bytes, address: tuple[str, int]
    ) -> None:
        """
        Refuse a CONNECT_REQUEST of a connection type or tunnelling layer xknx doesn't know.

        Such a request can't be parsed, so its control endpoint and CRI are read
        from the raw octets: an unknown tunnelling layer is E_TUNNELLING_LAYER,
        any other unknown connection type E_CONNECTION_TYPE.
        """
        header_end = KNXIPHeader.HEADERLENGTH
        cri = header_end + 2 * HPAI.LENGTH
        if len(data) < cri + 2 or data[
            2:4
        ] != KNXIPServiceType.CONNECT_REQUEST.value.to_bytes(2, "big"):
            return
        control_endpoint = HPAI()
        try:
            control_endpoint.from_knx(data[header_end : header_end + HPAI.LENGTH])
        except CouldNotParseKNXIP:
            return
        if (peer := self._resolve(control_endpoint, _UDPPeer(self, address))) is None:
            return
        status_code = (
            ErrorCode.E_TUNNELLING_LAYER
            if data[cri + 1] == ConnectRequestType.TUNNEL_CONNECTION.value
            else ErrorCode.E_CONNECTION_TYPE
        )
        peer.send(_refusal(status_code, ConnectRequestType.TUNNEL_CONNECTION))
