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
from xknx.exceptions import (
    CommunicationError,
    CouldNotParseCEMI,
    UnsupportedCEMIMessage,
)
from xknx.knxip import (
    HPAI,
    ConnectRequestInformation,
    DeviceConfigurationRequest,
    DisconnectRequest,
    DisconnectResponse,
    KNXIPFrame,
    KNXIPServiceType,
)
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
from .transport import KNXIPTransport, UDPTransport

logger = logging.getLogger("xknx.log")


def _same_property(one: CEMIMPropInfo, other: CEMIMPropInfo) -> bool:
    """Tell whether two property infos address the same Property."""
    return (
        one.object_type is other.object_type
        and one.object_instance == other.object_instance
        and one.property_id == other.property_id
    )


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

    The connection is supervised: a heartbeat keeps it alive and closes it
    when the server stops answering, and a DisconnectRequest of the server
    is answered and ends it as well.

    UDP only, as device management over TCP is not acknowledged.
    """

    __slots__ = (
        "_data_endpoint_addr",
        "_device_management",
        "_disconnect_callback",
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
        self._data_endpoint_addr: tuple[str, int] | None = None
        self._device_management: DeviceManagement | None = None
        self._disconnect_callback: KNXIPTransport.Callback | None = None
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
        if self.communication_channel is not None:
            raise CommunicationError(
                "Device management connection is already open. "
                f"communication_channel={self.communication_channel}"
            )
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
        self._data_endpoint_addr = (
            None
            if connect.data_endpoint.route_back
            else connect.data_endpoint.addr_tuple
        )
        self._device_management = DeviceManagement(
            transport=self.transport,
            communication_channel=self.communication_channel,
            cemi_received_callback=self._cemi_received,
            data_endpoint=self._data_endpoint_addr,
        )
        self._device_management.start()
        self._disconnect_callback = self.transport.register_callback(
            self._disconnect_request_received,
            [KNXIPServiceType.DISCONNECT_REQUEST],
        )
        logger.debug(
            "Device management connection established. communication_channel=%s",
            self.communication_channel,
        )

    async def disconnect(self) -> None:
        """Close the device management connection."""
        self._stop()
        try:
            if self.communication_channel is not None:
                disconnect = Disconnect(
                    transport=self.transport,
                    communication_channel_id=self.communication_channel,
                    local_hpai=self.local_hpai,
                )
                await disconnect.start()
                if not disconnect.success:
                    logger.debug(
                        "DisconnectRequest was not answered by the server (%s).",
                        "timeout"
                        if disconnect.response_status_code is None
                        else disconnect.response_status_code,
                    )
        finally:
            self.communication_channel = None
            self.transport.stop()

    def _stop(self) -> None:
        """Stop answering and expecting frames of the current connection."""
        if self._heartbeat_task is not None:
            # The heartbeat task disconnects itself after repeated failures.
            if self._heartbeat_task is not asyncio.current_task():
                self._heartbeat_task.cancel()
            self._heartbeat_task = None
        if self._device_management is not None:
            self._device_management.stop()
            self._device_management = None
        if self._disconnect_callback is not None:
            self.transport.unregister_callback(self._disconnect_callback)
            self._disconnect_callback = None
        if self._pending is not None and not self._pending.done():
            # Fail a request waiting for an answer instead of timing it out.
            self._pending.cancel()

    def _disconnect_request_received(
        self, knxipframe: KNXIPFrame, source: HPAI, _transport: KNXIPTransport
    ) -> None:
        """Handle a DisconnectRequest sent by the server."""
        if not isinstance(knxipframe.body, DisconnectRequest):
            return
        if knxipframe.body.communication_channel_id != self.communication_channel:
            logger.debug(
                "Received DisconnectRequest for another communication channel "
                "than %s. Discarding frame: %s",
                self.communication_channel,
                knxipframe.body,
            )
            return
        logger.info("Device management connection was closed by the server.")
        self.transport.send(
            KNXIPFrame.init_from_body(
                DisconnectResponse(communication_channel_id=self.communication_channel)
            )
        )
        self.communication_channel = None
        self._stop()
        self.transport.stop()

    async def _heartbeat(self) -> None:
        """Keep the connection alive, as the server drops a silent one."""
        while True:
            await asyncio.sleep(HEARTBEAT_RATE)
            if (channel := self.communication_channel) is None:
                return
            success, status = await self._connectionstate_request(channel)
            if not success:
                # Repeat the ConnectionStateRequest three times, then
                # terminate the connection - KNXnet/IP Core 03.08.02 §5.4.
                for _retry in range(3):
                    success, status = await self._connectionstate_request(channel)
                    if success:
                        break
            if success:
                continue
            logger.warning(
                "Device management connection heartbeat failed %s. Disconnecting.",
                "- no response from the server"
                if status is None
                else f"with status: {status}",
            )
            await self.disconnect()
            return

    async def _connectionstate_request(
        self, communication_channel: int
    ) -> tuple[bool, str | None]:
        """Send a ConnectionStateRequest and return its outcome."""
        conn_state = ConnectionState(
            transport=self.transport,
            communication_channel_id=communication_channel,
            local_hpai=self.local_hpai,
        )
        await conn_state.start()
        status_code: str | None = None
        if error_code := conn_state.response_status_code:
            status_code = error_code.name
        return conn_state.success, status_code

    ####################
    #
    # REQUESTS
    #
    ####################

    async def request(
        self,
        cemi: CEMIFrame,
        matches: Callable[[CEMIFrame], bool] | None = None,
    ) -> CEMIFrame:
        """
        Send one cEMI frame and return the one the server answers with.

        `matches` tells whether a received frame is the awaited answer;
        frames it rejects - e.g. the late answer to an earlier, timed out
        request - are discarded. Without it, the first frame that is not an
        indication is returned. Note that xknx only parses the Property
        service message codes, so e.g. a M_FuncProp request cannot see its
        answer - and M_Reset.req has none at all.

        Raise CommunicationError when the request is not acknowledged or the
        server does not answer it.
        """
        # A device management connection carries one request at a time, and
        # the sequence counter and the pending answer are shared state.
        async with self._request_lock:
            if self.communication_channel is None or self._device_management is None:
                raise CommunicationError("No active device management connection.")
            pending: asyncio.Future[CEMIFrame] = (
                asyncio.get_running_loop().create_future()
            )
            self._pending = pending
            try:
                await self._send_request(cemi)
                async with asyncio_timeout(DEVICE_CONFIGURATION_REQUEST_TIMEOUT):
                    while True:
                        answer = await pending
                        if matches is None or matches(answer):
                            return answer
                        logger.debug(
                            "Discarding cEMI frame not answering the request: %s",
                            answer,
                        )
                        pending = asyncio.get_running_loop().create_future()
                        self._pending = pending
            except asyncio.TimeoutError:
                raise CommunicationError(
                    f"No answer to {cemi.code} within "
                    f"{DEVICE_CONFIGURATION_REQUEST_TIMEOUT} seconds."
                ) from None
            except asyncio.CancelledError:
                if pending.cancelled():
                    # disconnect() failed the request
                    raise CommunicationError(
                        "Device management connection was closed."
                    ) from None
                raise
            finally:
                self._pending = None

    async def _send_request(self, cemi: CEMIFrame) -> None:
        """Send a request, repeating it while it stays unacknowledged."""
        if (channel := self.communication_channel) is None:
            raise CommunicationError("No active device management connection.")

        raw_cemi = cemi.to_knx()
        # A repetition keeps the sequence counter of the frame it repeats.
        for attempt in range(DEVICE_CONFIGURATION_REQUEST_REPETITIONS + 1):
            device_configuration = DeviceConfiguration(
                transport=self.transport,
                data_endpoint=self._data_endpoint_addr,
                device_configuration_request=DeviceConfigurationRequest(
                    communication_channel_id=channel,
                    sequence_counter=self.sequence_number,
                    raw_cemi=raw_cemi,
                ),
                timeout_in_seconds=DEVICE_CONFIGURATION_REQUEST_TIMEOUT,
            )
            await device_configuration.start()
            answered = (
                # The acknowledgement went missing, but the answer arrived -
                # so the server did accept the request.
                self._pending is not None
                and self._pending.done()
                and not self._pending.cancelled()
            )
            if device_configuration.success or answered:
                self.sequence_number = self.sequence_number + 1 & 0xFF
                return
            logger.debug(
                "DeviceConfigurationRequest was not acknowledged (attempt %s of %s%s).",
                attempt + 1,
                DEVICE_CONFIGURATION_REQUEST_REPETITIONS + 1,
                ""
                if device_configuration.response_status_code is None
                else f"; error status {device_configuration.response_status_code.name}",
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
        except (CouldNotParseCEMI, UnsupportedCEMIMessage, ValueError) as err:
            logger.warning("Could not parse received cEMI frame: %s", err)
            return
        except Exception:  # pylint: disable=broad-exception-caught
            # Last-resort guard: this runs in the transport's datagram
            # callback, where an unforeseen parsing bug must not escape.
            logger.exception("Unexpected error parsing cEMI frame: %s", raw_cemi.hex())
            return

        # Of what a server sends, M_PropInfo.ind is the only message that is
        # not an answer to a request. The cEMI Transport Layer indications
        # would be the others, but xknx does not know those message codes.
        if cemi.code is CEMIMessageCode.M_PROP_INFO_IND:
            if self.indication_callback is not None:
                try:
                    self.indication_callback(cemi)
                except Exception:  # pylint: disable=broad-exception-caught
                    logger.exception("Unexpected error in indication_callback")
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
        property_info = CEMIMPropInfo(
            object_type=object_type,
            object_instance=object_instance,
            property_id=property_id,
            number_of_elements=number_of_elements,
            start_index=start_index,
        )
        answer = await self.request(
            CEMIFrame(
                code=CEMIMessageCode.M_PROP_READ_REQ,
                data=CEMIMPropReadRequest(property_info=property_info),
            ),
            matches=lambda frame: (
                isinstance(frame.data, CEMIMPropReadResponse)
                and _same_property(frame.data.property_info, property_info)
            ),
        )
        if not isinstance(answer.data, CEMIMPropReadResponse):
            raise CommunicationError(f"Unexpected answer to a property read: {answer}")
        try:
            error_code = answer.data.error_code
        except ValueError:
            # resolving the error octet to a CEMIErrorCode is lazy and only
            # covers the codes the specification defines
            raise CommunicationError(
                "Reading the property failed with an unknown error code: "
                f"0x{answer.data.data.hex()}"
            ) from None
        if error_code is not None:
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
        property_info = CEMIMPropInfo(
            object_type=object_type,
            object_instance=object_instance,
            property_id=property_id,
            number_of_elements=number_of_elements,
            start_index=start_index,
        )
        answer = await self.request(
            CEMIFrame(
                code=CEMIMessageCode.M_PROP_WRITE_REQ,
                data=CEMIMPropWriteRequest(property_info=property_info, data=data),
            ),
            matches=lambda frame: (
                isinstance(frame.data, CEMIMPropWriteResponse)
                and _same_property(frame.data.property_info, property_info)
            ),
        )
        if not isinstance(answer.data, CEMIMPropWriteResponse):
            raise CommunicationError(f"Unexpected answer to a property write: {answer}")
        if (error_code := answer.data.error_code) is not None:
            raise CommunicationError(f"Writing the property failed: {error_code}")
