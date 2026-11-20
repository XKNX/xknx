"""End-to-end tests of the KNXnet/IP tunnelling server with the xknx clients."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from xknx import XKNX
from xknx.cemi import CEMIFrame, CEMIMessageCode
from xknx.core.connection_state import XknxConnectionState
from xknx.dpt import DPTBinary
from xknx.exceptions import CommunicationError
from xknx.io import (
    ConnectionConfig,
    ConnectionType,
    UDPDeviceManagementConnection,
)
from xknx.io.self_description import request_description
from xknx.io.server import KNXIPTunnellingServer
from xknx.io.server.raw_cemi import LDataFrame
from xknx.knxip import HostProtocol
from xknx.profile.const import (
    ResourceDevicePropertyId,
    ResourceGenericPropertyId,
    ResourceKNXNETIPPropertyId,
    ResourceObjectType,
)
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDirection,
)
from xknx.telegram.apci import GroupValueWrite

from .conftest import MAC_ADDRESS, OWN_ADDRESS, POOL, SERVER_IP, Backing, l_data

GROUP = GroupAddress("1/2/3")


class _Client:
    """An XKNX instance connected to the server as tunnelling client."""

    def __init__(
        self, server: KNXIPTunnellingServer, connection_type: ConnectionType
    ) -> None:
        """Initialize _Client."""
        self.received: asyncio.Queue[Telegram] = asyncio.Queue()
        self.xknx = XKNX(
            connection_config=ConnectionConfig(
                connection_type=connection_type,
                gateway_ip=SERVER_IP,
                gateway_port=server.port,
                local_ip=SERVER_IP,
                auto_reconnect=False,
            ),
            telegram_received_cb=self._telegram_received,
        )

    def _telegram_received(self, telegram: Telegram) -> None:
        """Queue an incoming telegram."""
        if telegram.direction is TelegramDirection.INCOMING:
            self.received.put_nowait(telegram)

    async def receive(self) -> Telegram:
        """Return the next incoming telegram."""
        async with asyncio.timeout(3):
            return await self.received.get()


@pytest.fixture(
    name="tunnel_client",
    params=[ConnectionType.TUNNELING, ConnectionType.TUNNELING_TCP],
)
async def fixture_tunnel_client(
    request: pytest.FixtureRequest, server: KNXIPTunnellingServer
) -> AsyncIterator[_Client]:
    """Return a started xknx tunnelling client of the server - UDP or TCP."""
    client = _Client(server, request.param)
    await client.xknx.start()
    yield client
    await client.xknx.stop()


async def test_tunnel(
    backing: Backing, server: KNXIPTunnellingServer, tunnel_client: _Client
) -> None:
    """Test that an xknx client sends and receives telegrams through the server."""
    assert tunnel_client.xknx.current_address == IndividualAddress("1.1.240")
    (tunnel,) = server.tunnels
    assert tunnel.individual_address == IndividualAddress("1.1.240")

    await tunnel_client.xknx.telegrams.put(
        Telegram(GROUP, payload=GroupValueWrite(DPTBinary(1)))
    )
    sent = LDataFrame((await backing.interface.wait_sent())[0])
    assert sent.code is CEMIMessageCode.L_DATA_REQ
    assert sent.source == IndividualAddress("1.1.240")
    assert sent.destination == GROUP
    await tunnel_client.xknx.telegrams.join()
    assert tunnel_client.xknx.connection_manager.cemi_count_outgoing == 1

    backing.interface.receive(l_data(CEMIMessageCode.L_DATA_IND, "1.1.5", GROUP))
    telegram = await tunnel_client.receive()
    assert telegram.source_address == IndividualAddress("1.1.5")
    assert telegram.destination_address == GROUP
    assert telegram.payload == GroupValueWrite(DPTBinary(1))

    await tunnel_client.xknx.stop()
    await asyncio.sleep(0.05)
    assert server.tunnels == []


async def test_two_clients_see_each_other(
    backing: Backing, server: KNXIPTunnellingServer
) -> None:
    """Test that a telegram of one client reaches the other client and the XKNX instance of the server."""
    first = _Client(server, ConnectionType.TUNNELING)
    second = _Client(server, ConnectionType.TUNNELING_TCP)
    await first.xknx.start()
    await second.xknx.start()
    try:
        assert {tunnel.protocol for tunnel in server.tunnels} == {
            HostProtocol.IPV4_UDP,
            HostProtocol.IPV4_TCP,
        }
        assert second.xknx.current_address == IndividualAddress("1.1.241")
        await first.xknx.telegrams.put(
            Telegram(GROUP, payload=GroupValueWrite(DPTBinary(0)))
        )
        telegram = await second.receive()
        assert telegram.source_address == IndividualAddress("1.1.240")
        assert telegram.payload == GroupValueWrite(DPTBinary(0))
        local = backing.xknx.telegrams.get_nowait()
        assert local is not None
        assert local.source_address == IndividualAddress("1.1.240")

        # and a telegram of the server's own XKNX instance reaches both
        await backing.xknx.cemi_handler.send_telegram(
            Telegram(GROUP, payload=GroupValueWrite(DPTBinary(1)))
        )
        for client in (first, second):
            telegram = await client.receive()
            assert telegram.source_address == OWN_ADDRESS
    finally:
        await first.xknx.stop()
        await second.xknx.stop()


async def test_stop_disconnects_xknx_client(server: KNXIPTunnellingServer) -> None:
    """Test that stopping the server disconnects an xknx client."""
    client = _Client(server, ConnectionType.TUNNELING)
    await client.xknx.start()
    try:
        assert client.xknx.connection_manager.connected.is_set()
        disconnected = asyncio.Event()
        client.xknx.connection_manager.register_connection_state_changed_cb(
            lambda state: (
                disconnected.set()
                if state is XknxConnectionState.DISCONNECTED
                else None
            )
        )
        await server.stop()
        async with asyncio.timeout(1):
            await disconnected.wait()
    finally:
        await client.xknx.stop()


async def test_request_description(server: KNXIPTunnellingServer) -> None:
    """Test that xknx reads the description and the tunnelling slots of the server."""
    gateway = await request_description(
        gateway_ip=SERVER_IP, gateway_port=server.port, local_ip=SERVER_IP
    )
    assert gateway.name == "xknx bridge"
    assert gateway.individual_address == OWN_ADDRESS
    assert gateway.mac_address == MAC_ADDRESS.hex(":")
    assert gateway.core_version == 2
    assert gateway.supports_tunnelling
    assert gateway.supports_tunnelling_tcp
    assert not gateway.supports_routing
    assert not gateway.tunnelling_requires_secure
    assert [str(address) for address in gateway.tunnelling_slots] == POOL
    assert all(slot.free for slot in gateway.tunnelling_slots.values())


async def test_device_management(
    backing: Backing, server: KNXIPTunnellingServer
) -> None:
    """Test that a device management connection reads the server's own Properties."""
    indications: asyncio.Queue[CEMIFrame] = asyncio.Queue()
    connection = UDPDeviceManagementConnection(
        gateway_ip=SERVER_IP,
        gateway_port=server.port,
        local_ip=SERVER_IP,
        indication_callback=indications.put_nowait,
    )
    async with connection:
        knxnetip = ResourceObjectType.OBJECT_KNXNETIP_PARAMETER
        device = ResourceObjectType.OBJECT_DEVICE
        assert (
            await connection.read_property(
                knxnetip, ResourceKNXNETIPPropertyId.PID_KNX_INDIVIDUAL_ADDRESS
            )
            == OWN_ADDRESS.to_knx()
        )
        additional = ResourceKNXNETIPPropertyId.PID_ADDITIONAL_INDIVIDUAL_ADDRESSES
        assert await connection.read_property(knxnetip, additional, start_index=0) == (
            2
        ).to_bytes(2, "big")
        assert await connection.read_property(
            knxnetip, additional, number_of_elements=2
        ) == b"".join(IndividualAddress(address).to_knx() for address in POOL)
        assert (
            await connection.read_property(
                knxnetip,
                ResourceKNXNETIPPropertyId.PID_FRIENDLY_NAME,
                number_of_elements=11,
            )
            == b"xknx bridge"
        )
        assert (
            await connection.read_property(
                knxnetip, ResourceKNXNETIPPropertyId.PID_MAC_ADDRESS
            )
            == MAC_ADDRESS
        )
        assert await connection.read_property(
            knxnetip, ResourceKNXNETIPPropertyId.PID_CURRENT_IP_ADDRESS
        ) == bytes((127, 0, 0, 1))
        assert await connection.read_property(
            knxnetip,
            ResourceKNXNETIPPropertyId.PID_TUNNELLING_ADDRESSES,
            number_of_elements=2,
        ) == bytes((1, 2))
        assert await connection.read_property(
            device, ResourceDevicePropertyId.PID_DEVICE_DESCRIPTOR
        ) == bytes.fromhex("091a")
        assert (
            await connection.read_property(
                device, ResourceGenericPropertyId.PID_SERIAL_NUMBER
            )
            == bytes.fromhex("0000") + MAC_ADDRESS[2:]
        )
        with pytest.raises(CommunicationError, match="CEMI_ERROR_VOID_DP"):
            await connection.read_property(
                ResourceObjectType.OBJECT_ROUTER,
                ResourceGenericPropertyId.PID_OBJECT_TYPE,
            )
        with pytest.raises(CommunicationError, match="CEMI_ERROR_PROP_INDEX_RANGE"):
            await connection.read_property(knxnetip, additional, number_of_elements=3)
        with pytest.raises(CommunicationError, match="CEMI_ERROR_READ_ONLY"):
            await connection.write_property(
                knxnetip,
                ResourceKNXNETIPPropertyId.PID_FRIENDLY_NAME,
                data=b"x",
            )

        # the device state is evented
        await backing.interface.disconnect()
        async with asyncio.timeout(3):
            indication = await indications.get()
        assert indication.code is CEMIMessageCode.M_PROP_INFO_IND
        assert indication.data is not None
        assert indication.data.to_knx()[-1:] == b"\x01"
        assert server.tunnels == []
