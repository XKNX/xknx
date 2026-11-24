"""Fixtures for the KNXnet/IP tunnelling server: a fake bus connection and raw KNXnet/IP clients."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TypeVar, cast

import pytest

from xknx import XKNX
from xknx.cemi import CEMIFrame, CEMIMessageCode
from xknx.core.connection_state import XknxConnectionState
from xknx.exceptions import CommunicationError, IncompleteKNXIPFrame
from xknx.io.interface import Interface
from xknx.io.server import KNXIPTunnellingServer
from xknx.knxip import (
    HPAI,
    ConnectRequest,
    ConnectRequestInformation,
    ConnectRequestType,
    ConnectResponse,
    HostProtocol,
    KNXIPBody,
    KNXIPFrame,
    TunnellingAck,
    TunnellingLayer,
    TunnellingRequest,
)
from xknx.telegram import GroupAddress, IndividualAddress

SERVER_IP = "127.0.0.1"
POOL = ["1.1.240", "1.1.241"]
OWN_ADDRESS = IndividualAddress("1.1.0")
MAC_ADDRESS = bytes.fromhex("00 24 6d 01 02 03")
GROUP_WRITE_ON = bytes.fromhex("0081")

_BodyT = TypeVar("_BodyT", bound=KNXIPBody)


def l_data(
    code: CEMIMessageCode,
    source: str,
    destination: GroupAddress | IndividualAddress,
    apdu: bytes = GROUP_WRITE_ON,
) -> bytes:
    """Return a raw cEMI L_Data frame - a standard frame without additional information."""
    control_2 = 0xE0 if isinstance(destination, GroupAddress) else 0x60
    return (
        bytes((code.value, 0x00, 0xBC, control_2))
        + IndividualAddress(source).to_knx()
        + destination.to_knx()
        + bytes((len(apdu) - 1,))
        + apdu
    )


class FakeInterface(Interface):
    """A bus connection recording the frames sent and confirming them."""

    def __init__(self, xknx: XKNX) -> None:
        """Initialize FakeInterface."""
        self.xknx = xknx
        self.sent: list[bytes] = []
        self.confirm = True
        self.fail = False
        self._sent_event = asyncio.Event()

    async def connect(self) -> None:
        """Connect to the fake bus."""
        self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )

    async def disconnect(self) -> None:
        """Disconnect from the fake bus."""
        self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )

    async def send_cemi(self, cemi: CEMIFrame) -> None:
        """Record a frame and confirm it like an interface does."""
        if self.fail:
            raise CommunicationError("No bus")
        raw = cemi.to_knx()
        self.sent.append(raw)
        self._sent_event.set()
        if self.confirm:
            confirmation = bytes((CEMIMessageCode.L_DATA_CON.value,)) + raw[1:]
            asyncio.get_running_loop().call_soon(self.receive, confirmation)

    def receive(self, raw: bytes) -> None:
        """Pass a frame from the bus on, as the interface does."""
        self.xknx.knxip_interface.cemi_received(raw)

    async def wait_sent(self, count: int = 1) -> list[bytes]:
        """Wait until `count` frames were sent and return them."""
        async with asyncio.timeout(3):
            while len(self.sent) < count:
                self._sent_event.clear()
                await self._sent_event.wait()
        return self.sent


@dataclass
class Backing:
    """The XKNX instance the server forwards to, and its fake interface."""

    xknx: XKNX
    interface: FakeInterface


@pytest.fixture(autouse=True)
def _short_disconnect_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    """Don't wait long for the DISCONNECT_RESPONSEs of raw clients on stop."""
    monkeypatch.setattr(
        "xknx.io.server.tunnelling_server.DISCONNECT_RESPONSE_TIMEOUT", 0.05
    )


@pytest.fixture(name="backing")
async def fixture_backing() -> Backing:
    """Return an XKNX instance connected to a fake bus."""
    xknx = XKNX()
    interface = FakeInterface(xknx)
    xknx.knxip_interface._interface = interface
    xknx.current_address = OWN_ADDRESS
    await interface.connect()
    return Backing(xknx=xknx, interface=interface)


@pytest.fixture(name="server")
async def fixture_server(backing: Backing) -> AsyncIterator[KNXIPTunnellingServer]:
    """Return a started server on an ephemeral port of 127.0.0.1."""
    server = KNXIPTunnellingServer(
        backing.xknx,
        individual_addresses=POOL,
        local_ip=SERVER_IP,
        port=0,
        discovery=False,
        mac_address=MAC_ADDRESS,
    )
    await server.start()
    yield server
    await server.stop()


class _FrameQueue:
    """Received KNX/IP frames."""

    def __init__(self) -> None:
        """Initialize _FrameQueue."""
        self.frames: asyncio.Queue[KNXIPBody] = asyncio.Queue()

    async def receive(self, body_type: type[_BodyT], timeout: float = 3) -> _BodyT:
        """Return the next frame, which has to be of `body_type`."""
        async with asyncio.timeout(timeout):
            body = await self.frames.get()
        assert isinstance(body, body_type), body
        return body

    async def silence(self, timeout: float = 0.2) -> None:
        """Assert that no frame arrives within `timeout`."""
        await asyncio.sleep(timeout)
        assert self.frames.empty(), self.frames.get_nowait()


class RawClient(asyncio.DatagramProtocol, _FrameQueue):
    """A KNXnet/IP client sending and receiving raw frames over UDP."""

    def __init__(self, server_address: tuple[str, int]) -> None:
        """Initialize RawClient."""
        _FrameQueue.__init__(self)
        self.server_address = server_address
        self.transport: asyncio.DatagramTransport | None = None

    @classmethod
    async def open(cls, server: KNXIPTunnellingServer) -> RawClient:
        """Return a client of a server, bound to an ephemeral port."""
        client = cls((SERVER_IP, server.port))
        await asyncio.get_running_loop().create_datagram_endpoint(
            lambda: client, local_addr=(SERVER_IP, 0)
        )
        return client

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Keep the transport. Callback."""
        # Not isinstance: before Python 3.12 the selector event loop's datagram
        # transport is no asyncio.DatagramTransport.
        self.transport = cast(asyncio.DatagramTransport, transport)

    def datagram_received(self, data: bytes, addr: tuple[str | int, int]) -> None:
        """Queue a received frame. Callback."""
        self.frames.put_nowait(KNXIPFrame.from_knx(data)[0].body)

    @property
    def hpai(self) -> HPAI:
        """Return the HPAI of the client's endpoint."""
        assert self.transport is not None
        return HPAI(*self.transport.get_extra_info("sockname"))

    def send(self, body: KNXIPBody, address: tuple[str, int] | None = None) -> None:
        """Send a frame to the server."""
        self.send_raw(KNXIPFrame.init_from_body(body).to_knx(), address)

    def send_raw(self, raw: bytes, address: tuple[str, int] | None = None) -> None:
        """Send raw octets to the server."""
        assert self.transport is not None
        self.transport.sendto(raw, address or self.server_address)

    async def connect(
        self,
        knx_layer: TunnellingLayer = TunnellingLayer.DATA_LINK_LAYER,
        individual_address: IndividualAddress | None = None,
        connection_type: ConnectRequestType = ConnectRequestType.TUNNEL_CONNECTION,
    ) -> ConnectResponse:
        """Send a CONNECT_REQUEST and return the CONNECT_RESPONSE."""
        self.send(
            ConnectRequest(
                control_endpoint=self.hpai,
                data_endpoint=self.hpai,
                cri=ConnectRequestInformation(
                    connection_type=connection_type,
                    knx_layer=knx_layer,
                    individual_address=individual_address,
                ),
            )
        )
        return await self.receive(ConnectResponse)

    async def receive_cemi(self, ack: bool = True) -> TunnellingRequest:
        """Return the next TUNNELLING_REQUEST, acknowledged."""
        request = await self.receive(TunnellingRequest)
        if ack:
            self.send(
                TunnellingAck(
                    communication_channel_id=request.communication_channel_id,
                    sequence_counter=request.sequence_counter,
                )
            )
        return request

    def close(self) -> None:
        """Close the socket."""
        if self.transport is not None:
            self.transport.close()


class RawTCPClient(asyncio.Protocol, _FrameQueue):
    """A KNXnet/IP client sending and receiving raw frames over TCP."""

    def __init__(self) -> None:
        """Initialize RawTCPClient."""
        _FrameQueue.__init__(self)
        self.transport: asyncio.Transport | None = None
        self.closed = asyncio.Event()
        self._buffer = b""

    @classmethod
    async def open(cls, server: KNXIPTunnellingServer) -> RawTCPClient:
        """Return a client connected to a server."""
        client = cls()
        await asyncio.get_running_loop().create_connection(
            lambda: client, SERVER_IP, server.port
        )
        return client

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Keep the transport. Callback."""
        assert isinstance(transport, asyncio.Transport)
        self.transport = transport

    def data_received(self, data: bytes) -> None:
        """Queue the received frames. Callback."""
        self._buffer += bytes(data)
        while self._buffer:
            try:
                frame, self._buffer = KNXIPFrame.from_knx(self._buffer)
            except IncompleteKNXIPFrame:
                return
            self.frames.put_nowait(frame.body)

    def connection_lost(self, exc: Exception | None) -> None:
        """Note the closed connection. Callback."""
        self.closed.set()

    hpai = HPAI(protocol=HostProtocol.IPV4_TCP)

    def send(self, body: KNXIPBody) -> None:
        """Send a frame to the server."""
        self.send_raw(KNXIPFrame.init_from_body(body).to_knx())

    def send_raw(self, raw: bytes) -> None:
        """Send raw octets to the server."""
        assert self.transport is not None
        self.transport.write(raw)

    async def connect(self) -> ConnectResponse:
        """Send a CONNECT_REQUEST for a tunnel and return the CONNECT_RESPONSE."""
        self.send(ConnectRequest(control_endpoint=self.hpai, data_endpoint=self.hpai))
        return await self.receive(ConnectResponse)

    def close(self) -> None:
        """Close the connection."""
        if self.transport is not None:
            self.transport.close()


@pytest.fixture(name="client")
async def fixture_client(server: KNXIPTunnellingServer) -> AsyncIterator[RawClient]:
    """Return a raw UDP client of the server."""
    client = await RawClient.open(server)
    yield client
    client.close()
