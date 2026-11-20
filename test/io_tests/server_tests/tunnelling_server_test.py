"""Tests for the KNXnet/IP tunnelling server - frame by frame with raw clients."""

from __future__ import annotations

import asyncio
import socket
from unittest.mock import Mock, patch

import pytest

from xknx.cemi import CEMIMessageCode
from xknx.core.connection_state import XknxConnectionState, XknxConnectionType
from xknx.exceptions import ConversionError
from xknx.io.server import KNXIPTunnellingServer
from xknx.io.server.raw_cemi import LDataFrame
from xknx.knxip import (
    HPAI,
    SRP,
    ConnectionStateRequest,
    ConnectionStateResponse,
    ConnectRequest,
    ConnectRequestType,
    ConnectResponse,
    DescriptionRequest,
    DescriptionResponse,
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
from xknx.management.management import Management
from xknx.telegram import GroupAddress, IndividualAddress, TelegramDirection
from xknx.telegram.apci import GroupValueWrite, ReturnCode

from .conftest import (
    MAC_ADDRESS,
    OWN_ADDRESS,
    POOL,
    SERVER_IP,
    Backing,
    RawClient,
    RawTCPClient,
    l_data,
)

GROUP = GroupAddress("1/2/3")
PARTNER = IndividualAddress("1.1.9")
# TPDUs of T_Connect, T_Disconnect and T_ACK 0 - KNX v01.02.03 - Transport Layer 03.03.04 - §2
T_CONNECT = b"\x80"
T_DISCONNECT = b"\x81"
T_ACK_0 = b"\xc2"


async def _connected(client: RawClient) -> ConnectResponse:
    """Open a tunnel and return the CONNECT_RESPONSE."""
    response = await client.connect()
    assert response.status_code is ErrorCode.E_NO_ERROR
    return response


def _raw(body: KNXIPBody) -> bytes:
    """Serialize a KNX/IP frame."""
    return KNXIPFrame.init_from_body(body).to_knx()


def _tunnelling_request(
    channel: int, sequence_counter: int, raw: bytes
) -> TunnellingRequest:
    """Return a TUNNELLING_REQUEST of a client."""
    return TunnellingRequest(
        communication_channel_id=channel,
        sequence_counter=sequence_counter,
        raw_cemi=raw,
    )


class TestConstruction:
    """Test the arguments of the server."""

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"individual_addresses": []}, "needs individual addresses"),
            ({"individual_addresses": ["1.1.1", "1.1.1"]}, "must be unique"),
            ({"mac_address": b"\x00"}, "MAC address"),
            ({"serial_number": b"\x00"}, "serial number"),
        ],
    )
    def test_invalid_arguments(
        self, backing: Backing, kwargs: dict[str, object], message: str
    ) -> None:
        """Test that invalid arguments are refused."""
        arguments: dict[str, object] = {"individual_addresses": POOL} | kwargs
        with pytest.raises(ConversionError, match=message):
            KNXIPTunnellingServer(backing.xknx, **arguments)  # type: ignore[arg-type]

    def test_serial_number_derived_from_mac_address(self, backing: Backing) -> None:
        """Test the default serial number."""
        server = KNXIPTunnellingServer(
            backing.xknx, individual_addresses=POOL, mac_address=MAC_ADDRESS
        )
        assert server._device_information().serial_number == "00:00:6d:01:02:03"
        assert server.port == 3671


class TestDiscovery:
    """Test search and description."""

    async def test_search_request(
        self, server: KNXIPTunnellingServer, client: RawClient
    ) -> None:
        """Test that a SEARCH_REQUEST is answered with the device information and service families."""
        client.send(SearchRequest(discovery_endpoint=client.hpai))
        response = await client.receive(SearchResponse)
        assert response.control_endpoint == HPAI(SERVER_IP, server.port)
        device_info, families = response.dibs
        assert isinstance(device_info, DIBDeviceInformation)
        assert device_info.name == "xknx bridge"
        assert device_info.individual_address == OWN_ADDRESS
        assert device_info.knx_medium is KNXMedium.TP1
        assert device_info.mac_address == MAC_ADDRESS.hex(":")
        assert device_info.multicast_address == "0.0.0.0"
        assert not device_info.programming_mode
        assert isinstance(families, DIBSuppSVCFamilies)
        assert families.version(DIBServiceFamily.CORE) == 2
        assert families.version(DIBServiceFamily.DEVICE_MANAGEMENT) == 1
        assert families.version(DIBServiceFamily.TUNNELING) == 2

    async def test_search_request_route_back(self, client: RawClient) -> None:
        """Test that a route back HPAI is answered to the source of the request."""
        client.send(SearchRequest(discovery_endpoint=HPAI()))
        await client.receive(SearchResponse)

    @pytest.mark.parametrize(
        "hpai",
        [
            HPAI(protocol=HostProtocol.IPV4_TCP),
            HPAI("0.0.0.0", 1234),
            HPAI("127.0.0.1", 0),
        ],
    )
    async def test_search_request_invalid_hpai(
        self, client: RawClient, hpai: HPAI
    ) -> None:
        """Test that a SEARCH_REQUEST with a TCP or half route back HPAI is discarded."""
        client.send(SearchRequest(discovery_endpoint=hpai))
        await client.silence()

    async def test_search_request_extended(
        self, server: KNXIPTunnellingServer, client: RawClient
    ) -> None:
        """Test the DIBs of a SEARCH_RESPONSE_EXTENDED, tunnelling slots included."""
        await _connected(client)
        client.send(
            SearchRequestExtended(
                discovery_endpoint=client.hpai,
                srps=[SRP.request_device_description([DIBTypeCode.TUNNELING_INFO])],
            )
        )
        response = await client.receive(SearchResponseExtended)
        assert response.control_endpoint == HPAI(SERVER_IP, server.port)
        device_info, extended, families, tunnelling = response.dibs
        assert isinstance(device_info, DIBDeviceInformation)
        assert isinstance(extended, DIBGeneric)
        assert extended.dtc is DIBTypeCode.ADDITIONAL_DEVICE_INFO
        # medium status ok, max APDU 15, device descriptor 091Ah
        assert extended.data == bytes.fromhex("0000 000f 091a")
        assert isinstance(families, DIBSuppSVCFamilies)
        assert isinstance(tunnelling, DIBTunnelingInfo)
        assert tunnelling.max_apdu_length == 15
        slots = tunnelling.slots
        assert list(slots) == [IndividualAddress(address) for address in POOL]
        assert not slots[IndividualAddress("1.1.240")].free
        assert slots[IndividualAddress("1.1.241")].free
        assert all(slot.usable and slot.authorized for slot in slots.values())

    @pytest.mark.parametrize(
        ("srp", "answered"),
        [
            (SRP.with_programming_mode(), False),
            (SRP.with_mac_address(MAC_ADDRESS), True),
            (SRP.with_mac_address(bytes(6)), False),
            (SRP.with_service(DIBServiceFamily.TUNNELING, 2), True),
            (SRP.with_service(DIBServiceFamily.TUNNELING, 3), False),
            (SRP.with_service(DIBServiceFamily.ROUTING, 1), False),
            (SRP(SearchRequestParameterType.INVALID, mandatory=True), False),
            (SRP(SearchRequestParameterType.INVALID, mandatory=False), True),
        ],
    )
    async def test_search_request_extended_srp(
        self, client: RawClient, srp: SRP, answered: bool
    ) -> None:
        """Test that the server answers only the searches it matches."""
        client.send(SearchRequestExtended(discovery_endpoint=client.hpai, srps=[srp]))
        if answered:
            await client.receive(SearchResponseExtended)
        else:
            await client.silence()

    async def test_search_request_extended_unknown_service_family(
        self, client: RawClient
    ) -> None:
        """Test that a Select By Service SRP of an unknown service family isn't answered."""
        request = SearchRequestExtended(
            discovery_endpoint=client.hpai,
            srps=[SRP.with_service(DIBServiceFamily.CORE, 1)],
        )
        raw = bytearray(_raw(request))
        raw[-2] = 0x7F
        client.send_raw(bytes(raw))
        await client.silence()

    async def test_description_request(self, client: RawClient) -> None:
        """Test that a DESCRIPTION_REQUEST is answered without Tunnelling Information DIB."""
        client.send(DescriptionRequest(control_endpoint=client.hpai))
        response = await client.receive(DescriptionResponse)
        assert [type(dib) for dib in response.dibs] == [
            DIBDeviceInformation,
            DIBSuppSVCFamilies,
        ]

    async def test_without_tcp_core_and_tunnelling_v1(self, backing: Backing) -> None:
        """Test that a server without TCP announces Core v1 and Tunnelling v1."""
        server = KNXIPTunnellingServer(
            backing.xknx,
            individual_addresses=POOL,
            local_ip=SERVER_IP,
            port=0,
            discovery=False,
            tcp=False,
            name="name",
            medium=KNXMedium.RF,
            max_apdu_length=200,
        )
        await server.start()
        client = await RawClient.open(server)
        try:
            client.send(DescriptionRequest(control_endpoint=client.hpai))
            response = await client.receive(DescriptionResponse)
            device_info, families = response.dibs
            assert isinstance(device_info, DIBDeviceInformation)
            assert device_info.knx_medium is KNXMedium.RF
            assert isinstance(families, DIBSuppSVCFamilies)
            assert families.version(DIBServiceFamily.CORE) == 1
            assert families.version(DIBServiceFamily.TUNNELING) == 1
            assert server._tcp_server is None
        finally:
            client.close()
            await server.stop()

    @pytest.mark.parametrize("same_port", [True, False])
    async def test_discovery_sockets(self, backing: Backing, same_port: bool) -> None:
        """Test that a server with discovery still answers unicast searches."""
        server = KNXIPTunnellingServer(
            backing.xknx,
            individual_addresses=POOL,
            local_ip=SERVER_IP,
            port=0,
            # port 0 joins the multicast group on the server's socket
            multicast_port=0 if same_port else _free_udp_port(),
            tcp=False,
        )
        await server.start()
        client = await RawClient.open(server)
        try:
            client.send(SearchRequest(discovery_endpoint=client.hpai))
            await client.receive(SearchResponse)
        finally:
            client.close()
            await server.stop()


def _free_udp_port() -> int:
    """Return a UDP port that is free right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((SERVER_IP, 0))
        return int(sock.getsockname()[1])


class TestConnect:
    """Test opening and closing connections."""

    async def test_address_pool(
        self, server: KNXIPTunnellingServer, client: RawClient
    ) -> None:
        """Test that each tunnel gets the next free address and the pool runs out."""
        first = await _connected(client)
        second = await _connected(client)
        assert first.crd.individual_address == IndividualAddress("1.1.240")
        assert second.crd.individual_address == IndividualAddress("1.1.241")
        assert first.communication_channel != second.communication_channel
        assert first.data_endpoint == HPAI(SERVER_IP, server.port)
        assert [tunnel.individual_address for tunnel in server.tunnels] == [
            IndividualAddress(address) for address in POOL
        ]
        assert server.tunnels[0].client == client.hpai.addr_tuple
        assert server.tunnels[0].protocol is HostProtocol.IPV4_UDP
        assert server.tunnels[0].layer is TunnellingLayer.DATA_LINK_LAYER

        client.send_raw(b"")  # an empty datagram is ignored
        refused = await client.connect()
        assert refused.status_code is ErrorCode.E_NO_MORE_CONNECTIONS
        assert refused.communication_channel == 0

        client.send(
            DisconnectRequest(
                communication_channel_id=first.communication_channel,
                control_endpoint=client.hpai,
            )
        )
        response = await client.receive(DisconnectResponse)
        assert response.status_code is ErrorCode.E_NO_ERROR
        again = await _connected(client)
        assert again.crd.individual_address == IndividualAddress("1.1.240")
        # channel ids are handed out in turn, not reused right away
        assert again.communication_channel not in (
            first.communication_channel,
            second.communication_channel,
        )

    async def test_refused_response(self, backing: Backing) -> None:
        """Test the octets of a refused CONNECT_RESPONSE: channel 0, empty HPAI, CRD with 0.0.0."""
        server = KNXIPTunnellingServer(
            backing.xknx,
            individual_addresses=["1.1.240"],
            local_ip=SERVER_IP,
            port=0,
            discovery=False,
            tcp=False,
        )
        await server.start()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((SERVER_IP, 0))
            sock.settimeout(3)
            hpai = HPAI(*sock.getsockname())
            request = _raw(ConnectRequest(control_endpoint=hpai, data_endpoint=hpai))
            for _ in range(2):
                await asyncio.to_thread(sock.sendto, request, (SERVER_IP, server.port))
                answer = await asyncio.to_thread(sock.recv, 100)
        await server.stop()
        assert answer == bytes.fromhex(
            "0610 0206 0014 00 24 0801 00000000 0000 0404 0000"
        )

    async def test_extended_cri(self, client: RawClient) -> None:
        """Test that an Extended CRI requests a tunnelling address."""
        response = await client.connect(individual_address=IndividualAddress("1.1.241"))
        assert response.crd.individual_address == IndividualAddress("1.1.241")
        in_use = await client.connect(individual_address=IndividualAddress("1.1.241"))
        assert in_use.status_code is ErrorCode.E_CONNECTION_IN_USE
        unknown = await client.connect(individual_address=IndividualAddress("1.1.99"))
        assert unknown.status_code is ErrorCode.E_NO_TUNNELLING_ADDRESS

    @pytest.mark.parametrize(
        ("connection_type", "layer", "status_code"),
        [
            (
                ConnectRequestType.TUNNEL_CONNECTION,
                TunnellingLayer.BUSMONITOR_LAYER,
                ErrorCode.E_TUNNELLING_LAYER,
            ),
            (
                ConnectRequestType.TUNNEL_CONNECTION,
                TunnellingLayer.RAW_LAYER,
                ErrorCode.E_TUNNELLING_LAYER,
            ),
            (
                ConnectRequestType.REMLOG_CONNECTION,
                TunnellingLayer.DATA_LINK_LAYER,
                ErrorCode.E_CONNECTION_TYPE,
            ),
        ],
    )
    async def test_refused(
        self,
        client: RawClient,
        connection_type: ConnectRequestType,
        layer: TunnellingLayer,
        status_code: ErrorCode,
    ) -> None:
        """Test that unsupported connection types and layers are refused."""
        response = await client.connect(
            knx_layer=layer, connection_type=connection_type
        )
        assert response.status_code is status_code

    @pytest.mark.parametrize(
        ("cri", "status_code"),
        [
            # an unknown connection type
            (bytes.fromhex("0277"), ErrorCode.E_CONNECTION_TYPE),
            # a tunnel with an unknown layer
            (bytes.fromhex("04040100"), ErrorCode.E_TUNNELLING_LAYER),
        ],
    )
    async def test_refused_unknown_cri(
        self, client: RawClient, cri: bytes, status_code: ErrorCode
    ) -> None:
        """Test that a CONNECT_REQUEST xknx can't parse is refused."""
        body = client.hpai.to_knx() + client.hpai.to_knx() + cri
        client.send_raw(
            bytes.fromhex("0610 0205") + (6 + len(body)).to_bytes(2, "big") + body
        )
        response = await client.receive(ConnectResponse)
        assert response.status_code is status_code

    async def test_unparsable_frames_ignored(self, client: RawClient) -> None:
        """Test that unparsable frames other than CONNECT_REQUESTs are ignored."""
        client.send_raw(
            bytes.fromhex("0610 0205 0008 0000")
        )  # truncated CONNECT_REQUEST
        client.send_raw(
            bytes.fromhex("0610 0201 0008 0000")
        )  # truncated SEARCH_REQUEST
        # a CONNECT_REQUEST with an invalid control endpoint
        client.send_raw(
            bytes.fromhex("0610 0205 001a") + bytes(16) + bytes.fromhex("0277")
        )
        await client.silence()

    async def test_without_bus_connection(
        self, backing: Backing, client: RawClient
    ) -> None:
        """Test that a tunnel needs the bus connection of the interface."""
        response = await _connected(client)
        await backing.interface.disconnect()
        refused = await client.connect()
        assert refused.status_code is ErrorCode.E_KNX_CONNECTION
        client.send(
            ConnectionStateRequest(
                communication_channel_id=response.communication_channel,
                control_endpoint=client.hpai,
            )
        )
        state = await client.receive(ConnectionStateResponse)
        assert state.status_code is ErrorCode.E_KNX_CONNECTION

    async def test_connectionstate(self, client: RawClient) -> None:
        """Test CONNECTIONSTATE_REQUESTs of open and unknown channels."""
        response = await _connected(client)
        for channel, status_code in (
            (response.communication_channel, ErrorCode.E_NO_ERROR),
            (99, ErrorCode.E_CONNECTION_ID),
        ):
            client.send(
                ConnectionStateRequest(
                    communication_channel_id=channel, control_endpoint=client.hpai
                )
            )
            state = await client.receive(ConnectionStateResponse)
            assert state.communication_channel_id == channel
            assert state.status_code is status_code
        # an invalid HPAI is discarded
        client.send(
            ConnectionStateRequest(
                communication_channel_id=response.communication_channel,
                control_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
            )
        )
        await client.silence()

    async def test_disconnect_unknown_channel(
        self, server: KNXIPTunnellingServer, client: RawClient
    ) -> None:
        """Test that a DISCONNECT_REQUEST of an unknown channel is answered with E_CONNECTION_ID."""
        response = await _connected(client)
        client.send(
            DisconnectRequest(communication_channel_id=99, control_endpoint=client.hpai)
        )
        answer = await client.receive(DisconnectResponse)
        assert answer.status_code is ErrorCode.E_CONNECTION_ID
        assert len(server.tunnels) == 1
        # an invalid HPAI: answered to the control endpoint of the connection
        client.send(
            DisconnectRequest(
                communication_channel_id=response.communication_channel,
                control_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
            )
        )
        answer = await client.receive(DisconnectResponse)
        assert answer.status_code is ErrorCode.E_NO_ERROR
        assert server.tunnels == []
        client.send(
            DisconnectRequest(
                communication_channel_id=99,
                control_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
            )
        )
        await client.silence()

    async def test_heartbeat_timeout(self, backing: Backing) -> None:
        """Test that a connection without heartbeat is terminated."""
        server = KNXIPTunnellingServer(
            backing.xknx,
            individual_addresses=POOL,
            local_ip=SERVER_IP,
            port=0,
            discovery=False,
            tcp=False,
            heartbeat_timeout=0.3,
        )
        await server.start()
        client = await RawClient.open(server)
        try:
            response = await _connected(client)
            for _ in range(3):
                await asyncio.sleep(0.15)
                client.send(
                    ConnectionStateRequest(
                        communication_channel_id=response.communication_channel,
                        control_endpoint=client.hpai,
                    )
                )
                await client.receive(ConnectionStateResponse)
            assert len(server.tunnels) == 1
            request = await client.receive(DisconnectRequest)
            assert request.communication_channel_id == response.communication_channel
            assert request.control_endpoint == HPAI(SERVER_IP, server.port)
            assert server.tunnels == []
        finally:
            client.close()
            await server.stop()

    async def test_stop_disconnects_clients(
        self,
        monkeypatch: pytest.MonkeyPatch,
        server: KNXIPTunnellingServer,
        client: RawClient,
    ) -> None:
        """Test that stopping the server sends a DISCONNECT_REQUEST to every client and waits for the responses."""
        monkeypatch.setattr(
            "xknx.io.server.tunnelling_server.DISCONNECT_RESPONSE_TIMEOUT", 5
        )
        first = await _connected(client)
        second = await _connected(client)
        stopping = asyncio.create_task(server.stop())
        channels = set()
        for _ in range(2):
            request = await client.receive(DisconnectRequest)
            channels.add(request.communication_channel_id)
            client.send(
                DisconnectResponse(
                    communication_channel_id=request.communication_channel_id
                )
            )
        async with asyncio.timeout(0.5):
            await stopping
        assert channels == {first.communication_channel, second.communication_channel}
        assert server.tunnels == []


class TestTunnelling:
    """Test the telegrams of the tunnels."""

    async def test_sequence_counter(self, backing: Backing, client: RawClient) -> None:
        """Test that requests are acknowledged, repetitions not forwarded and others discarded."""
        channel = (await _connected(client)).communication_channel
        frame = l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", GROUP)

        client.send(_tunnelling_request(channel, 0, frame))
        ack = await client.receive(TunnellingAck)
        assert (ack.communication_channel_id, ack.sequence_counter) == (channel, 0)
        sent = await backing.interface.wait_sent()
        # the source 0.0.0 is replaced by the tunnel's address
        assert LDataFrame(sent[0]).source == IndividualAddress("1.1.240")
        confirmation = await client.receive_cemi()
        assert confirmation.sequence_counter == 0
        assert (
            confirmation.raw_cemi
            == bytes((CEMIMessageCode.L_DATA_CON.value,)) + sent[0][1:]
        )

        # a repetition is acknowledged again but not sent
        client.send(_tunnelling_request(channel, 0, frame))
        assert (await client.receive(TunnellingAck)).sequence_counter == 0
        # out of sequence: neither acknowledged nor sent
        client.send(_tunnelling_request(channel, 5, frame))
        await client.silence()
        assert len(backing.interface.sent) == 1

        client.send(_tunnelling_request(channel, 1, frame))
        assert (await client.receive(TunnellingAck)).sequence_counter == 1
        await backing.interface.wait_sent(2)
        assert (await client.receive_cemi()).sequence_counter == 1

    async def test_source_address_kept(
        self, backing: Backing, client: RawClient
    ) -> None:
        """Test that a source address other than 0.0.0 is sent unchanged."""
        channel = (await _connected(client)).communication_channel
        frame = l_data(CEMIMessageCode.L_DATA_REQ, "1.1.77", GROUP)
        client.send(_tunnelling_request(channel, 0, frame))
        await client.receive(TunnellingAck)
        assert (await backing.interface.wait_sent())[0] == frame

    async def test_requests_of_unknown_channels_ignored(
        self, backing: Backing, client: RawClient
    ) -> None:
        """Test that requests of unknown channels and invalid frames aren't acknowledged or sent."""
        channel = (await _connected(client)).communication_channel
        client.send(
            _tunnelling_request(
                99, 0, l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", GROUP)
            )
        )
        client.send(TunnellingAck(communication_channel_id=99))
        await client.silence()
        # acknowledged, but not sent: an invalid L_Data.req, an M_Reset.req, an L_Data.ind
        for sequence_counter, raw in enumerate(
            (
                bytes.fromhex("1100bc"),
                bytes.fromhex("f1"),
                l_data(CEMIMessageCode.L_DATA_IND, "1.1.1", GROUP),
                b"",
            )
        ):
            client.send(_tunnelling_request(channel, sequence_counter, raw))
            await client.receive(TunnellingAck)
        await client.silence()
        assert backing.interface.sent == []

    async def test_confirmation_and_indications(
        self, backing: Backing, server: KNXIPTunnellingServer, client: RawClient
    ) -> None:
        """Test that the sender gets the L_Data.con, the other tunnels and xknx an L_Data.ind."""
        first = await _connected(client)
        other = await RawClient.open(server)
        try:
            await _connected(other)
            client.send(
                _tunnelling_request(
                    first.communication_channel,
                    0,
                    l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", GROUP),
                )
            )
            await client.receive(TunnellingAck)
            confirmation = LDataFrame((await client.receive_cemi()).raw_cemi)
            assert confirmation.code is CEMIMessageCode.L_DATA_CON
            indication = LDataFrame((await other.receive_cemi()).raw_cemi)
            assert indication.code is CEMIMessageCode.L_DATA_IND
            assert indication.source == IndividualAddress("1.1.240")
            assert indication.destination == GROUP
            await client.silence(0.1)
            # xknx receives the telegram as from the bus
            telegram = backing.xknx.telegrams.get_nowait()
            assert telegram is not None
            assert telegram.direction is TelegramDirection.INCOMING
            assert telegram.source_address == IndividualAddress("1.1.240")
            assert isinstance(telegram.payload, GroupValueWrite)
        finally:
            other.close()

    async def test_negative_confirmation(
        self, backing: Backing, server: KNXIPTunnellingServer, client: RawClient
    ) -> None:
        """Test that a frame the interface can't send gets a negative L_Data.con and no indication."""
        channel = (await _connected(client)).communication_channel
        other = await RawClient.open(server)
        try:
            await _connected(other)
            backing.interface.fail = True
            client.send(
                _tunnelling_request(
                    channel, 0, l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", GROUP)
                )
            )
            await client.receive(TunnellingAck)
            confirmation = LDataFrame((await client.receive_cemi()).raw_cemi)
            assert confirmation.code is CEMIMessageCode.L_DATA_CON
            assert confirmation.confirm_error
            assert confirmation.source == IndividualAddress("1.1.240")
            await other.silence()
            assert backing.xknx.telegrams.empty()
        finally:
            other.close()

    async def test_bus_indications(
        self, backing: Backing, server: KNXIPTunnellingServer, client: RawClient
    ) -> None:
        """Test that group frames go to every tunnel, point-to-point frames to the addressed one."""
        await _connected(client)
        other = await RawClient.open(server)
        try:
            await _connected(other)
            group = l_data(CEMIMessageCode.L_DATA_IND, "1.1.5", GROUP)
            backing.interface.receive(group)
            assert (await client.receive_cemi()).raw_cemi == group
            assert (await other.receive_cemi()).raw_cemi == group
            to_other = l_data(
                CEMIMessageCode.L_DATA_IND,
                "1.1.5",
                IndividualAddress("1.1.241"),
                b"\x80",
            )
            backing.interface.receive(to_other)
            assert (await other.receive_cemi()).raw_cemi == to_other
            backing.interface.receive(
                l_data(
                    CEMIMessageCode.L_DATA_IND,
                    "1.1.5",
                    IndividualAddress("1.1.9"),
                    b"\x80",
                )
            )
            # invalid frames and other services are not passed on
            backing.interface.receive(bytes.fromhex("2900"))
            backing.interface.receive(bytes.fromhex("2e00"))
            backing.interface.receive(bytes.fromhex("f0"))
            await client.silence()
            await other.silence(0)
            # xknx receives as before
            telegram = backing.xknx.telegrams.get_nowait()
            assert telegram is not None
            assert telegram.destination_address == GROUP
        finally:
            other.close()

    async def test_telegrams_of_xknx_reach_tunnels(
        self, backing: Backing, client: RawClient
    ) -> None:
        """Test that a telegram xknx itself sends goes to the tunnels as L_Data.ind."""
        from xknx.dpt import DPTBinary  # pylint: disable=import-outside-toplevel
        from xknx.telegram import Telegram  # pylint: disable=import-outside-toplevel

        await _connected(client)
        await backing.xknx.cemi_handler.send_telegram(
            Telegram(GROUP, payload=GroupValueWrite(DPTBinary(1)))
        )
        indication = LDataFrame((await client.receive_cemi()).raw_cemi)
        assert indication.code is CEMIMessageCode.L_DATA_IND
        assert indication.source == OWN_ADDRESS
        # a negative L_Data.con is no telegram on the bus
        backing.interface.receive(bytes.fromhex("2e00bd e0 1100 0a03 01 0081"))
        await client.silence()

    async def test_unacknowledged_request_terminates(
        self,
        monkeypatch: pytest.MonkeyPatch,
        backing: Backing,
        server: KNXIPTunnellingServer,
        client: RawClient,
    ) -> None:
        """Test that a TUNNELLING_REQUEST is repeated once, then the connection terminated."""
        monkeypatch.setattr(
            "xknx.io.server.connection.TUNNELLING_REQUEST_TIMEOUT", 0.05
        )
        channel = (await _connected(client)).communication_channel
        backing.interface.receive(l_data(CEMIMessageCode.L_DATA_IND, "1.1.5", GROUP))
        first = await client.receive_cemi(ack=False)
        repeated = await client.receive_cemi(ack=False)
        assert first.sequence_counter == repeated.sequence_counter == 0
        request = await client.receive(DisconnectRequest)
        assert request.communication_channel_id == channel
        assert server.tunnels == []

    async def test_ack_with_error_repeats(
        self, monkeypatch: pytest.MonkeyPatch, backing: Backing, client: RawClient
    ) -> None:
        """Test that a TUNNELLING_ACK with an error status has the request repeated."""
        monkeypatch.setattr("xknx.io.server.connection.TUNNELLING_REQUEST_TIMEOUT", 0.5)
        channel = (await _connected(client)).communication_channel
        backing.interface.receive(l_data(CEMIMessageCode.L_DATA_IND, "1.1.5", GROUP))
        first = await client.receive_cemi(ack=False)
        client.send(
            TunnellingAck(
                communication_channel_id=channel,
                sequence_counter=first.sequence_counter,
                status_code=ErrorCode.E_DATA_CONNECTION,
            )
        )
        repeated = await client.receive_cemi()
        assert repeated.sequence_counter == 0
        backing.interface.receive(l_data(CEMIMessageCode.L_DATA_IND, "1.1.5", GROUP))
        assert (await client.receive_cemi()).sequence_counter == 1


class TestPointToPointMapping:
    """Test point-to-point frames of the tunnels going out with the interface's address."""

    async def _send(
        self, client: RawClient, channel: int, sequence_counter: int, raw: bytes
    ) -> LDataFrame:
        """Send an L_Data.req of a tunnel and return its L_Data.con."""
        client.send(_tunnelling_request(channel, sequence_counter, raw))
        await client.receive(TunnellingAck)
        return LDataFrame((await client.receive_cemi()).raw_cemi)

    async def test_mapped(
        self,
        monkeypatch: pytest.MonkeyPatch,
        backing: Backing,
        client: RawClient,
    ) -> None:
        """Test the interface's address goes out, and the partner's frames go back to the tunnel only."""
        process = Mock()
        # Management has __slots__: patched on the class
        monkeypatch.setattr(Management, "process", process)
        channel = (await _connected(client)).communication_channel
        confirmation = await self._send(
            client,
            channel,
            0,
            l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", PARTNER, T_CONNECT),
        )
        sent = LDataFrame((await backing.interface.wait_sent())[0])
        assert sent.source == OWN_ADDRESS
        assert sent.destination == PARTNER
        # the tunnel sees its own address in its confirmation
        assert confirmation.code is CEMIMessageCode.L_DATA_CON
        assert confirmation.source == IndividualAddress("1.1.240")
        # the partner's answer to the interface's address goes to the tunnel
        backing.interface.receive(
            l_data(CEMIMessageCode.L_DATA_IND, "1.1.9", OWN_ADDRESS, T_ACK_0)
        )
        answer = LDataFrame((await client.receive_cemi()).raw_cemi)
        assert answer.source == PARTNER
        assert answer.destination == IndividualAddress("1.1.240")
        # and not to xknx, which would refuse the unknown connection
        await client.silence(0.1)
        process.assert_not_called()
        # other partners of the interface's address still reach xknx
        backing.interface.receive(
            l_data(CEMIMessageCode.L_DATA_IND, "1.1.8", OWN_ADDRESS, T_ACK_0)
        )
        await client.silence(0.1)
        process.assert_called_once()

    async def test_partner_of_one_tunnel(
        self,
        monkeypatch: pytest.MonkeyPatch,
        backing: Backing,
        server: KNXIPTunnellingServer,
        client: RawClient,
    ) -> None:
        """Test another tunnel can't reach a partner until the first one disconnected or the time ran out."""
        first = (await _connected(client)).communication_channel
        other = await RawClient.open(server)
        try:
            second = (await _connected(other)).communication_channel
            to_partner = l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", PARTNER, T_CONNECT)
            assert not (await self._send(client, first, 0, to_partner)).confirm_error
            await other.silence(0.1)
            assert (await self._send(other, second, 0, to_partner)).confirm_error
            assert len(backing.interface.sent) == 1
            # the partner disconnects: free for the other tunnel
            backing.interface.receive(
                l_data(CEMIMessageCode.L_DATA_IND, "1.1.9", OWN_ADDRESS, T_DISCONNECT)
            )
            assert LDataFrame((await client.receive_cemi()).raw_cemi).source == PARTNER
            assert not (await self._send(other, second, 1, to_partner)).confirm_error
            # the first tunnel disconnects itself: free again
            disconnect = l_data(
                CEMIMessageCode.L_DATA_REQ, "0.0.0", PARTNER, T_DISCONNECT
            )
            assert not (await self._send(other, second, 2, disconnect)).confirm_error
            await client.silence(0.1)
            assert not (await self._send(client, first, 1, to_partner)).confirm_error
            # after the transport layer's connection timeout another tunnel takes over
            monkeypatch.setattr(
                "xknx.io.server.tunnelling_server.POINT_TO_POINT_TIMEOUT", 0
            )
            assert not (await self._send(other, second, 3, to_partner)).confirm_error
        finally:
            other.close()

    async def test_closed_tunnel_frees_its_partners(
        self, backing: Backing, server: KNXIPTunnellingServer
    ) -> None:
        """Test the partners of a closed tunnel reach xknx again."""
        client = await RawClient.open(server)
        channel = (await _connected(client)).communication_channel
        await self._send(
            client,
            channel,
            0,
            l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", PARTNER, T_CONNECT),
        )
        client.send(
            DisconnectRequest(
                communication_channel_id=channel, control_endpoint=client.hpai
            )
        )
        await client.receive(DisconnectResponse)
        client.close()
        with patch.object(Management, "process") as process:
            backing.interface.receive(
                l_data(CEMIMessageCode.L_DATA_IND, "1.1.9", OWN_ADDRESS, T_ACK_0)
            )
            await asyncio.sleep(0.05)
        process.assert_called_once()

    @pytest.mark.parametrize(
        ("map_point_to_point", "connection_type", "mapped"),
        [
            (None, XknxConnectionType.USB, True),
            (None, XknxConnectionType.TUNNEL_UDP, True),
            (None, XknxConnectionType.ROUTING, False),
            (None, XknxConnectionType.ROUTING_SECURE, False),
            (False, XknxConnectionType.USB, False),
            (True, XknxConnectionType.ROUTING, True),
        ],
    )
    async def test_when_mapped(
        self,
        backing: Backing,
        map_point_to_point: bool | None,
        connection_type: XknxConnectionType,
        mapped: bool,
    ) -> None:
        """Test point-to-point frames are mapped but for a routing connection, which receives every frame."""
        backing.xknx.connection_manager.connection_type = connection_type
        server = KNXIPTunnellingServer(
            backing.xknx,
            individual_addresses=POOL,
            local_ip=SERVER_IP,
            port=0,
            discovery=False,
            tcp=False,
            mac_address=MAC_ADDRESS,
            map_point_to_point=map_point_to_point,
        )
        await server.start()
        client = await RawClient.open(server)
        try:
            channel = (await _connected(client)).communication_channel
            await self._send(
                client,
                channel,
                0,
                l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", PARTNER, T_CONNECT),
            )
            sent = LDataFrame((await backing.interface.wait_sent())[0])
            assert sent.source == (
                OWN_ADDRESS if mapped else IndividualAddress("1.1.240")
            )
        finally:
            client.close()
            await server.stop()

    async def test_not_mapped(self, backing: Backing, client: RawClient) -> None:
        """Test group frames, other sources and the interface's own address keep their source."""
        channel = (await _connected(client)).communication_channel
        frames = [
            l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", GROUP),
            l_data(CEMIMessageCode.L_DATA_REQ, "1.1.77", PARTNER, T_CONNECT),
            l_data(CEMIMessageCode.L_DATA_REQ, "1.1.0", PARTNER, T_CONNECT),
        ]
        for sequence_counter, frame in enumerate(frames):
            await self._send(client, channel, sequence_counter, frame)
        sent = await backing.interface.wait_sent(3)
        assert [LDataFrame(raw).source for raw in sent] == [
            IndividualAddress("1.1.240"),
            IndividualAddress("1.1.77"),
            OWN_ADDRESS,
        ]


class TestTunnellingFeatures:
    """Test the Tunnelling Feature services."""

    @staticmethod
    async def _feature(
        client: RawClient,
        request: TunnellingFeatureGet | TunnellingFeatureSet,
    ) -> TunnellingFeatureResponse:
        """Send a feature service and return the acknowledged response."""
        client.send(request)
        assert (await client.receive(TunnellingAck)).sequence_counter == (
            request.sequence_counter
        )
        response = await client.receive(TunnellingFeatureResponse)
        client.send(
            TunnellingAck(
                communication_channel_id=response.communication_channel_id,
                sequence_counter=response.sequence_counter,
            )
        )
        assert response.feature_type is request.feature_type
        return response

    @pytest.mark.parametrize(
        ("feature", "value"),
        [
            (TunnellingFeatureType.SUPPORTED_EMI_TYPE, "0004"),
            (TunnellingFeatureType.DEVICE_DESCRIPTOR_TYPE_0, "091a"),
            (TunnellingFeatureType.BUS_CONNECTION_STATUS, "0100"),
            (TunnellingFeatureType.MANUFACTURER_CODE, "0000"),
            (TunnellingFeatureType.ACTIVE_EMI_TYPE, "0300"),
            (TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS, "11f0"),
            (TunnellingFeatureType.MAX_APDU_LENGTH, "000f"),
            (TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE, "0000"),
        ],
    )
    async def test_get(
        self, client: RawClient, feature: TunnellingFeatureType, value: str
    ) -> None:
        """Test reading the Interface Features."""
        channel = (await _connected(client)).communication_channel
        response = await self._feature(
            client,
            TunnellingFeatureGet(
                communication_channel_id=channel, feature_type=feature
            ),
        )
        assert response.return_code is ReturnCode.E_SUCCESS
        assert response.data.hex() == value

    @pytest.mark.parametrize(
        ("feature", "data", "return_code"),
        [
            (
                TunnellingFeatureType.SUPPORTED_EMI_TYPE,
                "0004",
                ReturnCode.E_ACCESS_READ_ONLY,
            ),
            (
                TunnellingFeatureType.MAX_APDU_LENGTH,
                "00f0",
                ReturnCode.E_ACCESS_READ_ONLY,
            ),
            (
                TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE,
                "02",
                ReturnCode.E_DATA_VOID,
            ),
            (
                TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE,
                "0101",
                ReturnCode.E_DATA_TYPE_CONFLICT,
            ),
            (
                TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS,
                "11f0f0",
                ReturnCode.E_DATA_TYPE_CONFLICT,
            ),
            # another tunnel address, the server's own, 0.0.0
            (
                TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS,
                "11f1",
                ReturnCode.E_DATA_VOID,
            ),
            (
                TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS,
                "1100",
                ReturnCode.E_DATA_VOID,
            ),
            (
                TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS,
                "0000",
                ReturnCode.E_DATA_VOID,
            ),
            (
                TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS,
                "11f0",
                ReturnCode.E_SUCCESS,
            ),
        ],
    )
    async def test_set_refused(
        self,
        server: KNXIPTunnellingServer,
        client: RawClient,
        feature: TunnellingFeatureType,
        data: str,
        return_code: ReturnCode,
    ) -> None:
        """Test that read-only features and invalid values are refused."""
        channel = (await _connected(client)).communication_channel
        response = await self._feature(
            client,
            TunnellingFeatureSet(
                communication_channel_id=channel,
                feature_type=feature,
                data=bytes.fromhex(data),
            ),
        )
        assert response.return_code is return_code
        assert server.tunnels[0].individual_address == IndividualAddress("1.1.240")

    async def test_set_individual_address_and_infos(
        self, backing: Backing, server: KNXIPTunnellingServer, client: RawClient
    ) -> None:
        """Test changing the tunnel's address and the TUNNELLING_FEATURE_INFOs."""
        channel = (await _connected(client)).communication_channel
        enabled = await self._feature(
            client,
            TunnellingFeatureSet(
                communication_channel_id=channel,
                sequence_counter=0,
                feature_type=TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE,
                data=b"\x01",
            ),
        )
        assert enabled.return_code is ReturnCode.E_SUCCESS
        changed = await self._feature(
            client,
            TunnellingFeatureSet(
                communication_channel_id=channel,
                sequence_counter=1,
                feature_type=TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS,
                data=IndividualAddress("1.1.50").to_knx(),
            ),
        )
        assert changed.return_code is ReturnCode.E_SUCCESS
        info = await client.receive(TunnellingFeatureInfo)
        client.send(
            TunnellingAck(
                communication_channel_id=channel, sequence_counter=info.sequence_counter
            )
        )
        assert info.feature_type is TunnellingFeatureType.INTERFACE_INDIVIDUAL_ADDRESS
        assert info.data == IndividualAddress("1.1.50").to_knx()
        assert server.tunnels[0].individual_address == IndividualAddress("1.1.50")
        # the pool address is free again
        other = await RawClient.open(server)
        try:
            assert (await other.connect()).crd.individual_address == IndividualAddress(
                "1.1.240"
            )
        finally:
            other.close()

        await backing.interface.disconnect()
        info = await client.receive(TunnellingFeatureInfo)
        assert info.feature_type is TunnellingFeatureType.BUS_CONNECTION_STATUS
        assert info.data == b"\x00\x00"
        # an unchanged state isn't reported again
        backing.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTING
        )
        await client.silence()


class TestBusmonitor:
    """Test a server in front of an interface in bus monitor mode."""

    async def test_busmonitor_tunnel(self, backing: Backing) -> None:
        """Test that one bus monitor tunnel gets the L_Busmon.ind frames."""
        server = KNXIPTunnellingServer(
            backing.xknx,
            individual_addresses=POOL,
            local_ip=SERVER_IP,
            port=0,
            discovery=False,
            tcp=False,
            busmonitor=True,
        )
        await server.start()
        client = await RawClient.open(server)
        try:
            refused = await client.connect()
            assert refused.status_code is ErrorCode.E_TUNNELLING_LAYER
            response = await client.connect(knx_layer=TunnellingLayer.BUSMONITOR_LAYER)
            assert response.status_code is ErrorCode.E_NO_ERROR
            assert server.tunnels[0].layer is TunnellingLayer.BUSMONITOR_LAYER
            second = await client.connect(knx_layer=TunnellingLayer.BUSMONITOR_LAYER)
            assert second.status_code is ErrorCode.E_NO_MORE_CONNECTIONS

            busmonitor_frame = bytes.fromhex("2b0703010404020300bce0110a0a03010081cc")
            backing.interface.receive(busmonitor_frame)
            assert (await client.receive_cemi()).raw_cemi == busmonitor_frame
            # neither L_Data.ind is passed on nor L_Data.req sent
            backing.interface.receive(
                l_data(CEMIMessageCode.L_DATA_IND, "1.1.5", GROUP)
            )
            client.send(
                _tunnelling_request(
                    response.communication_channel,
                    0,
                    l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", GROUP),
                )
            )
            await client.receive(TunnellingAck)
            await client.silence()
            assert backing.interface.sent == []
        finally:
            client.close()
            await server.stop()


class TestTCP:
    """Test tunnels over TCP."""

    async def test_tunnel(
        self, backing: Backing, server: KNXIPTunnellingServer
    ) -> None:
        """Test that a TCP tunnel is neither acknowledged nor sequence checked."""
        client = await RawTCPClient.open(server)
        try:
            response = await client.connect()
            assert response.status_code is ErrorCode.E_NO_ERROR
            assert response.data_endpoint == HPAI(protocol=HostProtocol.IPV4_TCP)
            assert server.tunnels[0].protocol is HostProtocol.IPV4_TCP
            channel = response.communication_channel
            frame = l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", GROUP)
            # sequence counters aren't evaluated, frames are sent in one chunk of octets
            client.send_raw(
                _raw(_tunnelling_request(channel, 7, frame))
                + _raw(_tunnelling_request(channel, 7, frame))
            )
            await backing.interface.wait_sent(2)
            for _ in range(2):
                confirmation = await client.receive(TunnellingRequest)
                assert (
                    LDataFrame(confirmation.raw_cemi).code is CEMIMessageCode.L_DATA_CON
                )
            client.send(
                ConnectionStateRequest(
                    communication_channel_id=channel, control_endpoint=client.hpai
                )
            )
            state = await client.receive(ConnectionStateResponse)
            assert state.status_code is ErrorCode.E_NO_ERROR
            client.send(DescriptionRequest(control_endpoint=client.hpai))
            await client.receive(DescriptionResponse)
            # a channel is only valid through its own TCP connection
            udp = await RawClient.open(server)
            try:
                udp.send(
                    ConnectionStateRequest(
                        communication_channel_id=channel, control_endpoint=udp.hpai
                    )
                )
                state = await udp.receive(ConnectionStateResponse)
                assert state.status_code is ErrorCode.E_CONNECTION_ID
            finally:
                udp.close()
        finally:
            client.close()
        await asyncio.sleep(0.1)
        # closing the TCP connection closes its tunnels
        assert server.tunnels == []

    async def test_framing(self, server: KNXIPTunnellingServer) -> None:
        """Test that split frames are joined, unsupported ones skipped, an invalid header closes."""
        client = await RawTCPClient.open(server)
        try:
            raw = _raw(DescriptionRequest(control_endpoint=client.hpai))
            # a search over TCP isn't answered, an unknown service is skipped
            client.send_raw(
                _raw(SearchRequest(discovery_endpoint=client.hpai))
                + bytes.fromhex("0610 0999 0008 0000")
                + raw[:3]
            )
            await asyncio.sleep(0.05)
            client.send_raw(raw[3:])
            await client.receive(DescriptionResponse)
            # a TCP HPAI that isn't route back is discarded
            client.send(
                DescriptionRequest(
                    control_endpoint=HPAI("127.0.0.1", 1, HostProtocol.IPV4_TCP)
                )
            )
            await client.silence()
            client.send_raw(
                bytes.fromhex("0610 0999 0010 0000")
            )  # incomplete skipped frame
            client.send_raw(bytes(10))
            client.send_raw(bytes.fromhex("0510 0203 0008"))
            async with asyncio.timeout(1):
                await client.closed.wait()
        finally:
            client.close()

    async def test_idle_connection_closed(
        self, monkeypatch: pytest.MonkeyPatch, server: KNXIPTunnellingServer
    ) -> None:
        """Test that a TCP connection without KNXnet/IP connection is closed after the idle timeout."""
        monkeypatch.setattr("xknx.io.server.tunnelling_server.TCP_IDLE_TIMEOUT", 0.2)
        client = await RawTCPClient.open(server)
        try:
            response = await client.connect()
            await asyncio.sleep(0.3)
            assert not client.closed.is_set()
            client.send(
                DisconnectRequest(
                    communication_channel_id=response.communication_channel,
                    control_endpoint=client.hpai,
                )
            )
            await client.receive(DisconnectResponse)
            async with asyncio.timeout(1):
                await client.closed.wait()
        finally:
            client.close()

    async def test_heartbeat_timeout_closes_connection(self, backing: Backing) -> None:
        """Test that the TCP connection closes when its last tunnel times out."""
        server = KNXIPTunnellingServer(
            backing.xknx,
            individual_addresses=POOL,
            local_ip=SERVER_IP,
            port=0,
            discovery=False,
            heartbeat_timeout=0.1,
        )
        await server.start()
        client = await RawTCPClient.open(server)
        try:
            await client.connect()
            await client.receive(DisconnectRequest)
            async with asyncio.timeout(1):
                await client.closed.wait()
            assert server.tunnels == []
        finally:
            client.close()
            await server.stop()

    async def test_stop_closes_connections(self, server: KNXIPTunnellingServer) -> None:
        """Test that stopping the server disconnects and closes the TCP connections."""
        client = await RawTCPClient.open(server)
        try:
            response = await client.connect()
            stopping = asyncio.create_task(server.stop())
            request = await client.receive(DisconnectRequest)
            assert request.communication_channel_id == response.communication_channel
            assert request.control_endpoint == HPAI(protocol=HostProtocol.IPV4_TCP)
            client.send(
                DisconnectResponse(
                    communication_channel_id=request.communication_channel_id
                )
            )
            await stopping
            async with asyncio.timeout(1):
                await client.closed.wait()
        finally:
            client.close()


class TestMore:
    """Test the remaining paths of the server."""

    async def test_bound_to_all_interfaces(self, backing: Backing) -> None:
        """Test that a server on 0.0.0.0 announces the address the client reaches it at."""
        server = KNXIPTunnellingServer(
            backing.xknx,
            individual_addresses=POOL,
            port=0,
            discovery=False,
            tcp=False,
        )
        await server.start()
        await server.start()  # a second start does nothing
        client = await RawClient.open(server)
        try:
            client.send(SearchRequest(discovery_endpoint=client.hpai))
            response = await client.receive(SearchResponse)
            assert response.control_endpoint == HPAI(SERVER_IP, server.port)
        finally:
            client.close()
            await server.stop()

    async def test_values_of_usb_interface(
        self, monkeypatch: pytest.MonkeyPatch, backing: Backing, client: RawClient
    ) -> None:
        """Test that medium and maximum APDU length are taken from a KNX USB interface."""
        info = Mock(medium=KNXMedium.RF, max_apdu_length=55)
        monkeypatch.setattr(
            type(backing.xknx.knxip_interface), "usb_interface_info", lambda _: info
        )
        client.send(SearchRequestExtended(discovery_endpoint=client.hpai, srps=[]))
        response = await client.receive(SearchResponseExtended)
        device_info, _, _, tunnelling = response.dibs
        assert isinstance(device_info, DIBDeviceInformation)
        assert device_info.knx_medium is KNXMedium.RF
        assert isinstance(tunnelling, DIBTunnelingInfo)
        assert tunnelling.max_apdu_length == 55

    async def test_property_read_over_tunnel(self, client: RawClient) -> None:
        """Test that an M_PropRead.req of a tunnel is answered from the server's own Properties."""
        channel = (await _connected(client)).communication_channel
        # Device Object, instance 1, PID_DEVICE_DESCRIPTOR, 1 element from index 1
        client.send(
            _tunnelling_request(channel, 0, bytes.fromhex("fc 0000 01 53 1001"))
        )
        await client.receive(TunnellingAck)
        response = await client.receive_cemi()
        assert response.raw_cemi == bytes.fromhex("fb 0000 01 53 1001 091a")

    async def test_unparsable_telegram_passed_on(
        self, backing: Backing, server: KNXIPTunnellingServer, client: RawClient
    ) -> None:
        """Test that a frame xknx can't parse is sent and indicated unchanged, xknx doesn't get it."""
        channel = (await _connected(client)).communication_channel
        other = await RawClient.open(server)
        try:
            await _connected(other)
            frame = l_data(CEMIMessageCode.L_DATA_REQ, "1.1.240", GROUP, b"\x03\xfe")
            client.send(_tunnelling_request(channel, 0, frame))
            await client.receive(TunnellingAck)
            assert (await backing.interface.wait_sent())[0] == frame
            indication = await other.receive_cemi()
            assert (
                indication.raw_cemi
                == bytes((CEMIMessageCode.L_DATA_IND.value,)) + frame[1:]
            )
            assert backing.xknx.telegrams.empty()
        finally:
            other.close()

    async def test_forwarder_skips_closed_tunnel(
        self, backing: Backing, client: RawClient
    ) -> None:
        """Test that a frame of a tunnel closed before it was sent isn't sent."""
        channel = (await _connected(client)).communication_channel
        backing.interface.confirm = False
        frame = l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", GROUP)
        client.send(_tunnelling_request(channel, 0, frame))
        client.send(_tunnelling_request(channel, 1, frame))
        await client.receive(TunnellingAck)
        await client.receive(TunnellingAck)
        await backing.interface.wait_sent()
        client.send(
            DisconnectRequest(
                communication_channel_id=channel, control_endpoint=client.hpai
            )
        )
        await client.receive(DisconnectResponse)
        # the first frame is confirmed late, the second isn't sent any more
        backing.interface.receive(bytes.fromhex("2e00bce011f00a03010081"))
        await client.silence()
        assert len(backing.interface.sent) == 1

    async def test_device_management_connection(self, client: RawClient) -> None:
        """Test the sequence counter of a device management connection and the connection limit."""
        from xknx.knxip import (  # pylint: disable=import-outside-toplevel
            DeviceConfigurationAck,
            DeviceConfigurationRequest,
        )

        responses = [
            await client.connect(
                connection_type=ConnectRequestType.DEVICE_MGMT_CONNECTION
            )
            for _ in range(5)
        ]
        assert [response.status_code for response in responses] == [
            ErrorCode.E_NO_ERROR
        ] * 4 + [ErrorCode.E_NO_MORE_CONNECTIONS]
        assert responses[0].crd.individual_address is None
        channel = responses[0].communication_channel
        read = bytes.fromhex("fc 000b 01 34 1001")
        client.send(
            DeviceConfigurationRequest(
                communication_channel_id=channel, sequence_counter=0, raw_cemi=read
            )
        )
        assert (await client.receive(DeviceConfigurationAck)).sequence_counter == 0
        answer = await client.receive(DeviceConfigurationRequest)
        assert answer.raw_cemi == bytes.fromhex("fb 000b 01 34 1001 1100")
        client.send(
            DeviceConfigurationAck(
                communication_channel_id=channel,
                sequence_counter=answer.sequence_counter,
            )
        )
        # a repetition is acknowledged again but not answered, out of sequence is ignored
        for sequence_counter in (0, 3):
            client.send(
                DeviceConfigurationRequest(
                    communication_channel_id=channel,
                    sequence_counter=sequence_counter,
                    raw_cemi=read,
                )
            )
        assert (await client.receive(DeviceConfigurationAck)).sequence_counter == 0
        await client.silence()
        # M_Reset.req is acknowledged only; tunnelling services aren't answered on it
        client.send(
            DeviceConfigurationRequest(
                communication_channel_id=channel, sequence_counter=1, raw_cemi=b"\xf1"
            )
        )
        await client.receive(DeviceConfigurationAck)
        client.send(
            _tunnelling_request(
                channel, 2, l_data(CEMIMessageCode.L_DATA_REQ, "0.0.0", GROUP)
            )
        )
        client.send(
            TunnellingFeatureGet(
                communication_channel_id=channel,
                feature_type=TunnellingFeatureType.SUPPORTED_EMI_TYPE,
            )
        )
        client.send(DeviceConfigurationRequest(communication_channel_id=99))
        await client.silence()

    async def test_feature_services_sequenced(self, client: RawClient) -> None:
        """Test that Tunnelling Feature services of unknown channels or out of sequence are ignored."""
        channel = (await _connected(client)).communication_channel
        for channel_id, sequence_counter in ((99, 0), (channel, 4)):
            client.send(
                TunnellingFeatureGet(
                    communication_channel_id=channel_id,
                    sequence_counter=sequence_counter,
                    feature_type=TunnellingFeatureType.SUPPORTED_EMI_TYPE,
                )
            )
        await client.silence()

    async def test_handler_error_logged(
        self,
        monkeypatch: pytest.MonkeyPatch,
        server: KNXIPTunnellingServer,
        client: RawClient,
    ) -> None:
        """Test that an error handling a frame is logged and doesn't stop the server."""
        monkeypatch.setattr(
            KNXIPTunnellingServer,
            "_description_request_received",
            Mock(side_effect=RuntimeError),
        )
        with patch("logging.Logger.exception") as mock_exception:
            client.send(DescriptionRequest(control_endpoint=client.hpai))
            await client.silence(0.1)
        mock_exception.assert_called_once()
        client.send(SearchRequest(discovery_endpoint=client.hpai))
        await client.receive(SearchResponse)

    async def test_port_in_use(
        self, backing: Backing, server: KNXIPTunnellingServer
    ) -> None:
        """Test that start raises when the port is in use and leaves nothing open."""
        other = KNXIPTunnellingServer(
            backing.xknx,
            individual_addresses=POOL,
            local_ip=SERVER_IP,
            port=server.port,
            discovery=False,
        )
        with pytest.raises(OSError):
            await other.start()
        assert other._transport is None
