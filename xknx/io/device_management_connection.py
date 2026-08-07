"""Abstraction for a KNXnet/IP device management connection."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging

from xknx.cemi import (
    CEMIFrame,
    CEMIMessageCode,
    CEMIMPropInfo,
    CEMIMPropReadRequest,
    CEMIMPropReadResponse,
    CEMIMPropWriteRequest,
    CEMIMPropWriteResponse,
)
from xknx.exceptions import CommunicationError, UnsupportedCEMIMessage
from xknx.knxip import HPAI, ConnectRequestInformation, DeviceConfigurationRequest
from xknx.knxip.knxip_enum import ConnectRequestType
from xknx.profile.const import ResourceObjectType, ResourcePropertyId
from xknx.util import asyncio_timeout

from .const import (
    DEVICE_CONFIGURATION_REQUEST_REPETITIONS,
    DEVICE_CONFIGURATION_REQUEST_TIMEOUT,
    HEARTBEAT_RATE,
)
from .device_management import DeviceManagement
from .request_response import Connect, ConnectionState, DeviceConfiguration, Disconnect
from .transport import UDPTransport

logger = logging.getLogger("xknx.log")


class DeviceManagementConnection:
    """
    A KNXnet/IP device management connection to one server.

    Reads and writes the Properties of the server's own Interface Objects -
    its KNXnet/IP Parameter Object and Device Object - over a device
    management connection, which is a separate connection type from
    tunnelling and unrelated to the KNX bus behind the server. It is
    therefore not an `Interface`: it carries no telegrams, has no individual
    address and does not touch `xknx.current_address` or the connection
    manager.

    Requests are answered by the server with a cEMI frame of its own, so the
    connection tracks which request is outstanding and returns the matching
    answer. Frames the server sends unprompted - `M_PropInfo.ind` for the
    evented device state, and the cEMI Transport Layer indications - go to
    `indication_callback` instead.

    UDP only, as device management over TCP is not acknowledged.
    """

    __slots__ = (
        "_device_management",
        "_heartbeat_task",
        "_pending",
        "_request_lock",
        "communication_channel",
        "gateway_ip",
        "gateway_port",
        "indication_callback",
        "local_hpai",
        "local_ip",
        "local_port",
        "route_back",
        "sequence_number",
        "transport",
    )

    def __init__(
        self,
        gateway_ip: str,
        gateway_port: int,
        local_ip: str,
        local_port: int = 0,
        route_back: bool = False,
        indication_callback: Callable[[CEMIFrame], None] | None = None,
    ) -> None:
        """Initialize DeviceManagementConnection class."""
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.local_ip = local_ip
        self.local_port = local_port
        self.route_back = route_back
        self.indication_callback = indication_callback

        self.transport = UDPTransport(
            local_addr=(local_ip, local_port),
            remote_addr=(gateway_ip, gateway_port),
            multicast=False,
        )
        self.local_hpai = HPAI()
        self.communication_channel: int | None = None
        self.sequence_number = 0
        self._device_management: DeviceManagement | None = None
        self._pending: asyncio.Future[CEMIFrame] | None = None
        self._request_lock = asyncio.Lock()
        self._heartbeat_task: asyncio.Task[None] | None = None

    async def __aenter__(self) -> DeviceManagementConnection:
        """Connect on entering a context."""
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        """Disconnect on leaving a context."""
        await self.disconnect()

    ####################
    #
    # CONNECT DISCONNECT
    #
    ####################

    async def connect(self) -> None:
        """Open the device management connection. Raise CommunicationError if it fails."""
        try:
            await self.transport.connect()
            if self.route_back:
                self.local_hpai = HPAI()
            else:
                local_addr, local_port = self.transport.getsockname()
                self.local_hpai = HPAI(ip_addr=local_addr, port=local_port)
            await self._connect_request()
        except (OSError, CommunicationError) as ex:
            self.transport.stop()
            raise CommunicationError(
                f"Device management connection could not be established: {ex}"
            ) from ex

        self._heartbeat_task = asyncio.create_task(self._heartbeat())

    async def _connect_request(self) -> None:
        """Send a ConnectRequest and set up the connection from its response."""
        connect = Connect(
            transport=self.transport,
            local_hpai=self.local_hpai,
            cri=ConnectRequestInformation(
                connection_type=ConnectRequestType.DEVICE_MGMT_CONNECTION,
            ),
        )
        await connect.start()
        if not connect.success:
            raise CommunicationError(
                f"ConnectRequest failed. Status code: {connect.response_status_code}"
            )

        self.communication_channel = connect.communication_channel
        self.sequence_number = 0
        data_endpoint = (
            None
            if connect.data_endpoint.route_back
            else connect.data_endpoint.addr_tuple
        )
        self._device_management = DeviceManagement(
            transport=self.transport,
            communication_channel=self.communication_channel,
            cemi_received_callback=self._cemi_received,
            data_endpoint=data_endpoint,
        )
        self._device_management.start()
        logger.debug(
            "Device management connection established. communication_channel=%s",
            self.communication_channel,
        )

    async def disconnect(self) -> None:
        """Close the device management connection."""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        if self._device_management is not None:
            self._device_management.stop()
            self._device_management = None
        if self.communication_channel is not None:
            disconnect = Disconnect(
                transport=self.transport,
                communication_channel_id=self.communication_channel,
                local_hpai=self.local_hpai,
            )
            await disconnect.start()
            self.communication_channel = None
        self.transport.stop()

    async def _heartbeat(self) -> None:
        """Keep the connection alive, as the server drops a silent one."""
        while True:
            await asyncio.sleep(HEARTBEAT_RATE)
            if self.communication_channel is None:
                return
            conn_state = ConnectionState(
                transport=self.transport,
                communication_channel_id=self.communication_channel,
                local_hpai=self.local_hpai,
            )
            await conn_state.start()
            if not conn_state.success:
                logger.warning(
                    "Device management connection heartbeat failed with status: %s",
                    conn_state.response_status_code,
                )

    ####################
    #
    # REQUESTS
    #
    ####################

    async def request(self, cemi: CEMIFrame) -> CEMIFrame:
        """
        Send one cEMI frame and return the one the server answers with.

        Raise CommunicationError when the request is not acknowledged or the
        server does not answer it.
        """
        if self.communication_channel is None or self._device_management is None:
            raise CommunicationError("No active device management connection.")

        # A device management connection carries one request at a time, and
        # the sequence counter and the pending answer are shared state.
        async with self._request_lock:
            self._pending = asyncio.get_running_loop().create_future()
            try:
                await self._send_request(cemi)
                async with asyncio_timeout(DEVICE_CONFIGURATION_REQUEST_TIMEOUT):
                    return await self._pending
            except asyncio.TimeoutError:
                raise CommunicationError(
                    f"No answer to {cemi.code} within "
                    f"{DEVICE_CONFIGURATION_REQUEST_TIMEOUT} seconds."
                ) from None
            finally:
                self._pending = None

    async def _send_request(self, cemi: CEMIFrame) -> None:
        """Send a request, repeating it while it stays unacknowledged."""
        assert self.communication_channel is not None
        assert self._device_management is not None

        raw_cemi = cemi.to_knx()
        # A repetition keeps the sequence counter of the frame it repeats.
        for attempt in range(DEVICE_CONFIGURATION_REQUEST_REPETITIONS + 1):
            device_configuration = DeviceConfiguration(
                transport=self.transport,
                data_endpoint=self._device_management.data_endpoint_addr,
                device_configuration_request=DeviceConfigurationRequest(
                    communication_channel_id=self.communication_channel,
                    sequence_counter=self.sequence_number,
                    raw_cemi=raw_cemi,
                ),
                timeout_in_seconds=DEVICE_CONFIGURATION_REQUEST_TIMEOUT,
            )
            await device_configuration.start()
            if device_configuration.success:
                self.sequence_number = self.sequence_number + 1 & 0xFF
                return
            logger.debug(
                "DeviceConfigurationRequest was not acknowledged (attempt %s of %s).",
                attempt + 1,
                DEVICE_CONFIGURATION_REQUEST_REPETITIONS + 1,
            )

        # Repeated to no avail, so the connection is terminated as required.
        await self.disconnect()
        raise CommunicationError(
            "DeviceConfigurationRequest was not acknowledged after "
            f"{DEVICE_CONFIGURATION_REQUEST_REPETITIONS} repetitions. Disconnected."
        )

    def _cemi_received(self, raw_cemi: bytes) -> None:
        """Handle a cEMI frame the server sent. Callback of DeviceManagement."""
        try:
            cemi = CEMIFrame.from_knx(raw_cemi)
        except (UnsupportedCEMIMessage, ValueError) as err:
            logger.warning("Could not parse received cEMI frame: %s", err)
            return

        # Of what a server sends, M_PropInfo.ind is the only message that is
        # not an answer to a request. The cEMI Transport Layer indications
        # would be the others, but xknx does not know those message codes.
        if cemi.code is CEMIMessageCode.M_PROP_INFO_IND:
            if self.indication_callback is not None:
                self.indication_callback(cemi)
            return
        if self._pending is not None and not self._pending.done():
            self._pending.set_result(cemi)
            return
        logger.debug("Received an unexpected cEMI frame: %s", cemi)

    ####################
    #
    # PROPERTIES
    #
    ####################

    async def read_property(
        self,
        object_type: ResourceObjectType,
        property_id: ResourcePropertyId | int,
        object_instance: int = 1,
        number_of_elements: int = 1,
        start_index: int = 1,
    ) -> bytes:
        """
        Read a Property of one of the server's own Interface Objects.

        Raise CommunicationError when the server reports an error instead.
        """
        answer = await self.request(
            CEMIFrame(
                code=CEMIMessageCode.M_PROP_READ_REQ,
                data=CEMIMPropReadRequest(
                    property_info=CEMIMPropInfo(
                        object_type=object_type,
                        object_instance=object_instance,
                        property_id=property_id,
                        number_of_elements=number_of_elements,
                        start_index=start_index,
                    )
                ),
            )
        )
        if not isinstance(answer.data, CEMIMPropReadResponse):
            raise CommunicationError(f"Unexpected answer to a property read: {answer}")
        if (error_code := answer.data.error_code) is not None:
            raise CommunicationError(f"Reading the property failed: {error_code}")
        return answer.data.data

    async def write_property(
        self,
        object_type: ResourceObjectType,
        property_id: ResourcePropertyId | int,
        data: bytes,
        object_instance: int = 1,
        number_of_elements: int = 1,
        start_index: int = 1,
    ) -> None:
        """
        Write a Property of one of the server's own Interface Objects.

        Raise CommunicationError when the server reports an error.
        """
        answer = await self.request(
            CEMIFrame(
                code=CEMIMessageCode.M_PROP_WRITE_REQ,
                data=CEMIMPropWriteRequest(
                    property_info=CEMIMPropInfo(
                        object_type=object_type,
                        object_instance=object_instance,
                        property_id=property_id,
                        number_of_elements=number_of_elements,
                        start_index=start_index,
                    ),
                    data=data,
                ),
            )
        )
        if not isinstance(answer.data, CEMIMPropWriteResponse):
            raise CommunicationError(f"Unexpected answer to a property write: {answer}")
        if (error_code := answer.data.error_code) is not None:
            raise CommunicationError(f"Writing the property failed: {error_code}")
