"""
KNX tunnelling over a KNX USB interface.

On connect the bus access server is checked and set up - KNX v01.03.04 - Basic and
System Components - Couplers 09.03 - §3.5.3.3.2: the supported EMI types are read,
the one used is activated (cEMI where supported), and the cEMI server is switched
to the data link layer (PID_COMM_MODE, read back to verify) - KNX v01.04.02 - External Message Interface
03.06.03 - §4.2.2.4.2. The interface's own individual address and maximum APDU
length are read from its device object. On disconnect the interface is closed as
it is: whoever connects next sets the communication mode again, as the cEMI server
may be in any mode until then (KNX v01.04.02 - External Message Interface 03.06.03 -
§4.2.2.4.2).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
import logging
from typing import TYPE_CHECKING

from xknx.cemi import (
    CEMIFrame,
    CEMIMessageCode,
    CEMIMPropInfo,
    CEMIMPropReadRequest,
    CEMIMPropReadResponse,
    CEMIMPropWriteRequest,
    CEMIMPropWriteResponse,
)
from xknx.core import XknxConnectionState, XknxConnectionType
from xknx.exceptions import (
    CommunicationError,
    ConversionError,
    CouldNotParseCEMI,
    UnsupportedCEMIMessage,
)
from xknx.profile.const import (
    ResourceCEMIServerPropertyId,
    ResourceDevicePropertyId,
    ResourceObjectType,
    ResourcePropertyId,
)
from xknx.telegram import IndividualAddress

from ..interface import CEMIBytesCallbackType, Interface
from . import emi
from .const import (
    DEVICE_FEATURE_GET_TIMEOUT,
    EMIID,
    CommunicationMode,
    DeviceFeature,
    DeviceFeatureService,
    ProtocolID,
    SupportedEMIType,
)
from .emi import EMILayer
from .frame import (
    CouldNotParseUSBFrame,
    ReportAssembler,
    USBTransferFrame,
    device_feature_frame,
)
from .hid_device import HIDDevice, USBDeviceInfo, find_usb_interfaces

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")

# timeout for local device management requests (M_PropRead/M_PropWrite) - the
# recommended request-to-confirmation timeout of a cEMI client is 3 s,
# KNX v01.04.02 - External Message Interface 03.06.03 - §4.1.5.1
LOCAL_MANAGEMENT_TIMEOUT = 3.0
# APDU length of a short frame - used when the interface doesn't report its own
DEFAULT_MAX_APDU_LENGTH = 15

_EMI_NAMES = {EMIID.CEMI: "cEMI", EMIID.EMI1: "EMI1", EMIID.EMI2: "EMI2"}

_MANAGEMENT_RESPONSES = {
    CEMIMessageCode.M_PROP_READ_REQ: CEMIMessageCode.M_PROP_READ_CON,
    CEMIMessageCode.M_PROP_WRITE_REQ: CEMIMessageCode.M_PROP_WRITE_CON,
}


@dataclass(frozen=True, slots=True)
class USBInterfaceInfo:
    """What a connected KNX USB interface reported about itself."""

    device: USBDeviceInfo
    individual_address: IndividualAddress
    max_apdu_length: int
    supported_emi_types: SupportedEMIType
    bus_connected: bool
    manufacturer_code: int | None = None
    mask_version: int | None = None
    # the EMI format used with the interface
    emi_type: EMIID = EMIID.CEMI


class USBTunnel(Interface):
    """
    Interface to the KNX bus through a KNX USB interface.

    cEMI is used when the interface supports it, else EMI2, else EMI1; frames are
    passed on as cEMI either way.
    """

    __slots__ = (
        "_assembler",
        "_bus_connected",
        "_device",
        "_emi",
        "_established",
        "_feature_requests",
        "_info",
        "_memory_requests",
        "_property_requests",
        "_reconnect_task",
        "_send_lock",
        "auto_reconnect",
        "auto_reconnect_wait",
        "busmonitor",
        "cemi_received_callback",
        "device_info",
        "path",
        "product_id",
        "serial_number",
        "vendor_id",
        "xknx",
    )

    connection_type = XknxConnectionType.USB

    def __init__(
        self,
        xknx: XKNX,
        cemi_received_callback: CEMIBytesCallbackType,
        *,
        vendor_id: int | None = None,
        product_id: int | None = None,
        serial_number: str | None = None,
        path: bytes | None = None,
        auto_reconnect: bool = True,
        auto_reconnect_wait: int = 3,
        busmonitor: bool = False,
    ) -> None:
        """
        Initialize USBTunnel.

        Without any of `vendor_id`, `product_id`, `serial_number` and `path` the
        first known KNX USB interface found is used. After it was unplugged it is
        looked up again by vendor and product id and serial number, so it is found
        on another USB port as well.

        With `busmonitor` the cEMI server is switched to the bus monitor mode
        instead: every frame on the bus is passed on as L_Busmon.ind, and nothing
        can be sent.
        """
        self.xknx = xknx
        self.busmonitor = busmonitor
        self.cemi_received_callback = cemi_received_callback
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.serial_number = serial_number
        self.path = path
        self.auto_reconnect = auto_reconnect
        self.auto_reconnect_wait = auto_reconnect_wait
        self.device_info: USBDeviceInfo | None = None

        self._assembler = ReportAssembler()
        self._bus_connected = False
        self._device: HIDDevice | None = None
        self._emi = EMIID.CEMI
        self._established = False
        self._feature_requests: dict[DeviceFeature, asyncio.Future[bytes]] = {}
        self._info: USBInterfaceInfo | None = None
        self._memory_requests: dict[int, asyncio.Future[bytes]] = {}
        self._property_requests: dict[
            tuple[CEMIMessageCode, int, int, int], asyncio.Future[CEMIFrame]
        ] = {}
        self._reconnect_task: asyncio.Task[None] | None = None
        self._send_lock = asyncio.Lock()

    @property
    def info(self) -> USBInterfaceInfo | None:
        """Return what the connected interface reported about itself."""
        return self._info

    ####################
    #
    # CONNECT DISCONNECT
    #
    ####################

    def _find_device(self) -> USBDeviceInfo:
        """Find the interface to connect to."""
        if self.path is not None and self.device_info is None:
            for device in find_usb_interfaces(self.vendor_id, self.product_id):
                if device.path == self.path:
                    return device
            raise CommunicationError(f"No KNX USB interface at {self.path!r}")
        vendor_id = self.vendor_id
        product_id = self.product_id
        serial_number = self.serial_number
        if self.device_info is not None:
            # reconnect to the same interface, possibly on another port
            vendor_id = self.device_info.vendor_id
            product_id = self.device_info.product_id
            serial_number = self.device_info.serial_number or None
        devices = find_usb_interfaces(vendor_id, product_id, serial_number)
        if not devices:
            raise CommunicationError("No KNX USB interface found")
        if len(devices) > 1:
            logger.debug(
                "Found %s KNX USB interfaces - using %s", len(devices), devices[0]
            )
        return devices[0]

    async def connect(self) -> None:
        """Connect to the KNX USB interface. Raise CommunicationError when not successful."""
        self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTING, self.connection_type
        )
        try:
            device_info = self._find_device()
            self._device = HIDDevice(
                device_info,
                report_received=self._report_received,
                connection_lost=self._device_lost,
            )
            await self._device.open()
            self.device_info = device_info
            await self._setup()
        except CommunicationError as ex:
            logger.debug("Could not connect to KNX USB interface: %s", ex)
            self.xknx.connection_manager.connection_state_changed(
                XknxConnectionState.DISCONNECTED
            )
            await self._close_device()
            raise CommunicationError(
                f"USB connection could not be established: {ex}"
            ) from ex

        self._established = True
        logger.debug("Connected to KNX USB interface %s", self._info)
        self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED, self.connection_type
        )

    async def _setup(self) -> None:
        """Set up the bus access server and the EMI server for tunnelling."""
        assert self.device_info is not None
        supported = SupportedEMIType(
            int.from_bytes(
                await self._feature_get(DeviceFeature.SUPPORTED_EMI_TYPE), "big"
            )
            & (SupportedEMIType.EMI1 | SupportedEMIType.EMI2 | SupportedEMIType.CEMI)
        )
        # KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.3.2:
        # tunnelling frames only in an EMI type the interface supports
        for emi_id, flag in (
            (EMIID.CEMI, SupportedEMIType.CEMI),
            (EMIID.EMI2, SupportedEMIType.EMI2),
            (EMIID.EMI1, SupportedEMIType.EMI1),
        ):
            if flag in supported:
                self._emi = emi_id
                break
        else:
            raise CommunicationError("KNX USB interface supports no EMI type")
        # an interface with a single EMI type needn't support the Set service; it
        # ignores it then. Some report no active EMI type after power-up until it is set.
        await self._feature_set(DeviceFeature.ACTIVE_EMI_TYPE, bytes((self._emi,)))
        if len([flag for flag in SupportedEMIType if flag in supported]) > 1:
            active = await self._feature_get(DeviceFeature.ACTIVE_EMI_TYPE)
            if active[:1] != bytes((self._emi,)):
                raise CommunicationError(
                    f"KNX USB interface did not activate {_EMI_NAMES[self._emi]} "
                    f"(active EMI type {active.hex()})"
                )
        self._bus_connected = bool(
            (await self._feature_get(DeviceFeature.BUS_CONNECTION_STATUS))[:1]
            == b"\x01"
        )
        manufacturer_code = await self._optional_feature(
            DeviceFeature.MANUFACTURER_CODE
        )
        mask_version = await self._optional_feature(
            DeviceFeature.DEVICE_DESCRIPTOR_TYPE_0
        )

        if self._emi == EMIID.CEMI:
            await self._setup_cemi()
            individual_address = await self._read_individual_address()
            max_apdu_length = await self._read_max_apdu_length()
        else:
            await self._switch_emi_layer(
                EMILayer.BUSMONITOR if self.busmonitor else EMILayer.DATA_LINK_LAYER
            )
            individual_address = await self._read_emi_individual_address()
            max_apdu_length = emi.MAX_APDU_LENGTH
        self.xknx.current_address = individual_address

        self._info = USBInterfaceInfo(
            device=self.device_info,
            individual_address=individual_address,
            max_apdu_length=max_apdu_length,
            supported_emi_types=supported,
            bus_connected=self._bus_connected,
            manufacturer_code=manufacturer_code,
            mask_version=mask_version,
            emi_type=self._emi,
        )
        if not self._bus_connected:
            logger.warning(
                "KNX USB interface %s is not connected to the bus", self._info.device
            )

    async def _setup_cemi(self) -> None:
        """Switch the cEMI server to the data link layer or the bus monitor mode."""
        communication_mode = bytes(
            (
                CommunicationMode.DATA_LINK_LAYER_BUSMONITOR
                if self.busmonitor
                else CommunicationMode.DATA_LINK_LAYER,
            )
        )
        await self._property_write(
            ResourceObjectType.OBJECT_CEMI_SERVER,
            ResourceCEMIServerPropertyId.PID_COMM_MODE,
            communication_mode,
        )
        active_mode = await self._property_read(
            ResourceObjectType.OBJECT_CEMI_SERVER,
            ResourceCEMIServerPropertyId.PID_COMM_MODE,
        )
        if active_mode[:1] != communication_mode:
            raise CommunicationError(
                f"KNX USB interface did not switch to communication mode "
                f"{communication_mode.hex()} (it is in {active_mode.hex()})"
            )

    async def _switch_emi_layer(self, layer: EMILayer) -> None:
        """
        Give access to a layer of an EMI1/EMI2 interface.

        EMI2: PEI_Switch.req; EMI1: the "system status" is written and read back -
        KNX v01.04.02 - External Message Interface 03.06.03 - §3.1.3, §3.1.4.
        """
        if self._emi == EMIID.EMI2:
            await self._send_tunnel_frame(emi.pei_switch(layer))
            return
        status = bytes((emi.SYSTEM_STATUS[layer],))
        await self._send_tunnel_frame(
            emi.pc_set_value(self._emi, emi.SYSTEM_STATUS_ADDRESS, status)
        )
        if (await self._memory_read(emi.SYSTEM_STATUS_ADDRESS, 1)) != status:
            raise CommunicationError(
                f"KNX USB interface did not switch to {layer.value}"
            )

    async def _read_emi_individual_address(self) -> IndividualAddress:
        """Read the individual address of an EMI1/EMI2 interface from its memory."""
        try:
            data = await self._memory_read(emi.INDIVIDUAL_ADDRESS_ADDRESS, 2)
        except CommunicationError as ex:
            logger.warning(
                "Could not read the individual address of the KNX USB interface: %s", ex
            )
            return IndividualAddress(0)
        return IndividualAddress(int.from_bytes(data[:2], "big"))

    async def _optional_feature(self, feature: DeviceFeature) -> int | None:
        """Get an optional 2 octet device feature; None when it isn't answered."""
        try:
            data = await self._feature_get(feature)
        except CommunicationError:
            return None
        return int.from_bytes(data[:2], "big") if len(data) >= 2 else None

    async def _read_individual_address(self) -> IndividualAddress:
        """Read the interface's individual address from its device object."""
        try:
            subnet = await self._property_read(
                ResourceObjectType.OBJECT_DEVICE,
                ResourceDevicePropertyId.PID_SUBNET_ADDR,
            )
            device = await self._property_read(
                ResourceObjectType.OBJECT_DEVICE,
                ResourceDevicePropertyId.PID_DEVICE_ADDR,
            )
        except CommunicationError as ex:
            logger.warning(
                "Could not read the individual address of the KNX USB interface: %s", ex
            )
            return IndividualAddress(0)
        return IndividualAddress((subnet[0] << 8) | device[0])

    async def _read_max_apdu_length(self) -> int:
        """Read the maximum APDU length of the interface, 15 when it isn't available."""
        try:
            data = await self._property_read(
                ResourceObjectType.OBJECT_DEVICE,
                ResourceDevicePropertyId.PID_MAX_APDU_LENGTH,
            )
        except CommunicationError:
            return DEFAULT_MAX_APDU_LENGTH
        return int.from_bytes(data[:2], "big") or DEFAULT_MAX_APDU_LENGTH

    def _device_lost(self) -> None:
        """Handle an interface that stopped answering, eg. because it was unplugged. Callback."""
        logger.warning("Lost connection to KNX USB interface %s", self.device_info)
        self._prepare_disconnect()
        if self._reconnect_task is None:

            def _reconnect_task_cleanup(_: asyncio.Task[None]) -> None:
                self._reconnect_task = None

            self._reconnect_task = asyncio.create_task(self._reconnect())
            self._reconnect_task.add_done_callback(_reconnect_task_cleanup)

    async def _reconnect(self) -> None:
        """Close the lost interface and reconnect until it is back."""
        await self._close_device()
        if not self.auto_reconnect:
            logger.warning("USB connection closed. auto_reconnect is disabled.")
            return
        attempt = 1
        while True:
            await asyncio.sleep(self.auto_reconnect_wait)
            try:
                logger.debug(
                    "Reconnecting to KNX USB interface... (attempt %s)", attempt
                )
                await self.connect()
            except CommunicationError:
                attempt += 1
            except Exception:  # pylint: disable=broad-except
                attempt += 1
                logger.exception(
                    "Unexpected error while reconnecting to KNX USB interface"
                )
            else:
                logger.info("Successfully reconnected to KNX USB interface.")
                return

    def _prepare_disconnect(self) -> None:
        """Set the connection state and fail pending requests."""
        self._established = False
        for feature_future in self._feature_requests.values():
            if not feature_future.done():
                feature_future.set_exception(
                    CommunicationError("USB connection closed")
                )
        for property_future in self._property_requests.values():
            if not property_future.done():
                property_future.set_exception(
                    CommunicationError("USB connection closed")
                )
        for memory_future in self._memory_requests.values():
            if not memory_future.done():
                memory_future.set_exception(CommunicationError("USB connection closed"))
        self._feature_requests.clear()
        self._property_requests.clear()
        self._memory_requests.clear()
        self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )

    async def _close_device(self) -> None:
        """Close the HID device."""
        if self._device is not None:
            device, self._device = self._device, None
            await device.close()

    async def stop_reconnect(self) -> None:
        """Stop reconnecting for good - the connection is about to be shut down."""
        self.auto_reconnect = False
        if self._reconnect_task is not None:
            self._reconnect_task.cancel()

    async def disconnect(self) -> None:
        """
        Close the interface.

        An EMI1/EMI2 interface is switched back to its normal mode first: while the
        external interface has access to the data link layer, the device's own
        application and object servers do not run (KNX v01.04.02 - External
        Message Interface 03.06.03 - §3.1.2). A cEMI interface is closed as it is.
        """
        was_established = self._established
        self._prepare_disconnect()
        if self._reconnect_task is not None:
            self._reconnect_task.cancel()
        if was_established and self._emi != EMIID.CEMI and self._device is not None:
            try:
                await self._send_tunnel_frame(self._normal_mode_request())
            except CommunicationError as ex:
                logger.debug("Could not switch KNX USB interface back: %s", ex)
        await self._close_device()

    def _normal_mode_request(self) -> bytes:
        """Return the EMI message switching an EMI1/EMI2 interface back to normal mode."""
        if self._emi == EMIID.EMI2:
            return emi.pei_switch(EMILayer.NORMAL)
        return emi.pc_set_value(
            self._emi,
            emi.SYSTEM_STATUS_ADDRESS,
            bytes((emi.SYSTEM_STATUS[EMILayer.NORMAL],)),
        )

    ####################
    #
    # REQUESTS
    #
    ####################

    async def _write_frame(self, frame: USBTransferFrame) -> None:
        """Write a KNX USB transfer frame."""
        if self._device is None:
            raise CommunicationError("KNX USB interface not connected")
        async with self._send_lock:
            for report in frame.to_reports():
                await self._device.write(report)

    async def _send_tunnel_frame(self, raw: bytes) -> None:
        """Send a message in the EMI type in use."""
        await self._write_frame(
            USBTransferFrame(
                protocol=ProtocolID.KNX_TUNNEL, service=self._emi, body=raw
            )
        )

    async def _memory_read(self, address: int, length: int) -> bytes:
        """Read the memory of an EMI1/EMI2 interface (PC_Get_Value)."""
        future: asyncio.Future[bytes] = asyncio.get_running_loop().create_future()
        self._memory_requests[address] = future
        try:
            await self._send_tunnel_frame(emi.pc_get_value(self._emi, address, length))
            async with asyncio.timeout(LOCAL_MANAGEMENT_TIMEOUT):
                return await future
        except TimeoutError:
            raise CommunicationError(
                f"KNX USB interface did not answer PC_Get_Value of {address:04x}h"
            ) from None
        finally:
            if self._memory_requests.get(address) is future:
                del self._memory_requests[address]

    async def _feature_get(self, feature: DeviceFeature) -> bytes:
        """Get a device feature of the bus access server - KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.2.2."""
        future: asyncio.Future[bytes] = asyncio.get_running_loop().create_future()
        self._feature_requests[feature] = future
        try:
            await self._write_frame(
                device_feature_frame(DeviceFeatureService.GET, feature)
            )
            async with asyncio.timeout(DEVICE_FEATURE_GET_TIMEOUT):
                return await future
        except TimeoutError:
            raise CommunicationError(
                f"KNX USB interface did not answer Device Feature Get {feature.name}"
            ) from None
        finally:
            if self._feature_requests.get(feature) is future:
                del self._feature_requests[feature]

    async def _feature_set(self, feature: DeviceFeature, data: bytes) -> None:
        """Set a device feature of the bus access server. It is not answered."""
        await self._write_frame(
            device_feature_frame(DeviceFeatureService.SET, feature, data)
        )

    async def _management_request(self, request: CEMIFrame) -> CEMIFrame:
        """Send a local device management request and wait for its confirmation."""
        assert isinstance(request.data, CEMIMPropReadRequest | CEMIMPropWriteRequest)
        info = request.data.property_info
        key = (
            _MANAGEMENT_RESPONSES[request.code],
            info.object_type.value,
            info.object_instance,
            info.property_id,
        )
        future: asyncio.Future[CEMIFrame] = asyncio.get_running_loop().create_future()
        self._property_requests[key] = future
        try:
            await self._send_tunnel_frame(request.to_knx())
            async with asyncio.timeout(LOCAL_MANAGEMENT_TIMEOUT):
                return await future
        except TimeoutError:
            raise CommunicationError(
                f"KNX USB interface did not confirm {request.code.name} of property {info.property_id}"
            ) from None
        finally:
            if self._property_requests.get(key) is future:
                del self._property_requests[key]

    async def _property_read(
        self,
        object_type: ResourceObjectType,
        property_id: ResourcePropertyId,
    ) -> bytes:
        """Read one element of a property of the interface (M_PropRead)."""
        response = await self._management_request(
            CEMIFrame(
                code=CEMIMessageCode.M_PROP_READ_REQ,
                data=CEMIMPropReadRequest(
                    property_info=CEMIMPropInfo(
                        object_type=object_type, property_id=property_id
                    )
                ),
            )
        )
        assert isinstance(response.data, CEMIMPropReadResponse)
        if response.data.error_code is not None:
            raise CommunicationError(
                f"Reading property {property_id.name} failed: {response.data.error_code!r}"
            )
        return response.data.data

    async def _property_write(
        self,
        object_type: ResourceObjectType,
        property_id: ResourcePropertyId,
        data: bytes,
    ) -> None:
        """Write one element of a property of the interface (M_PropWrite)."""
        response = await self._management_request(
            CEMIFrame(
                code=CEMIMessageCode.M_PROP_WRITE_REQ,
                data=CEMIMPropWriteRequest(
                    property_info=CEMIMPropInfo(
                        object_type=object_type, property_id=property_id
                    ),
                    data=data,
                ),
            )
        )
        assert isinstance(response.data, CEMIMPropWriteResponse)
        if response.data.error_code is not None:
            raise CommunicationError(
                f"Writing property {property_id.name} failed: {response.data.error_code!r}"
            )

    async def send_cemi(self, cemi: CEMIFrame) -> None:
        """Send a CEMIFrame to the KNX bus."""
        if not self._established:
            raise CommunicationError("KNX USB interface not connected")
        if self.busmonitor:
            raise CommunicationError("KNX USB interface is in bus monitor mode")
        if self._emi == EMIID.CEMI:
            await self._send_tunnel_frame(cemi.to_knx())
            return
        try:
            raw = emi.l_data_req_from_cemi(cemi.to_knx())
        except ConversionError as ex:
            raise CommunicationError(
                f"Can't send this through an {_EMI_NAMES[self._emi]} interface: {ex}"
            ) from ex
        await self._send_tunnel_frame(raw)

    ####################
    #
    # INCOMING
    #
    ####################

    def _report_received(self, report: bytes) -> None:
        """Handle an incoming HID report. Callback."""
        try:
            frame = self._assembler.feed(report)
        except CouldNotParseUSBFrame as ex:
            logger.debug("Ignoring invalid KNX USB frame: %s", ex)
            return
        if frame is None:
            return
        if frame.protocol == ProtocolID.BUS_ACCESS_SERVER_FEATURE:
            self._feature_frame_received(frame)
        elif frame.protocol == ProtocolID.KNX_TUNNEL:
            if frame.service != self._emi:
                logger.debug("Ignoring KNX USB frame in EMI type %s", frame.service)
                return
            if self._emi == EMIID.CEMI:
                self._cemi_received(frame.body)
            else:
                self._emi_received(frame.body)
        else:
            logger.debug("Ignoring KNX USB frame of protocol %s", frame.protocol)

    def _feature_frame_received(self, frame: USBTransferFrame) -> None:
        """Handle a Device Feature Response or Info."""
        feature = frame.feature
        if not isinstance(feature, DeviceFeature):
            logger.debug("Ignoring unknown device feature %s", feature)
            return
        if frame.service == DeviceFeatureService.RESPONSE:
            future = self._feature_requests.get(feature)
            if future is not None and not future.done():
                future.set_result(frame.feature_data)
        elif (
            frame.service == DeviceFeatureService.INFO
            and feature == DeviceFeature.BUS_CONNECTION_STATUS
        ):
            self._bus_connected = frame.feature_data[:1] == b"\x01"
            if self._info is not None:
                self._info = replace(self._info, bus_connected=self._bus_connected)
            if self._bus_connected:
                logger.info("KNX USB interface is connected to the bus again")
            else:
                logger.warning("KNX USB interface lost its bus connection")

    def _cemi_received(self, raw_cemi: bytes) -> None:
        """Pass a cEMI frame on, unless it answers a request of this connection."""
        if raw_cemi[:1] in (
            bytes((CEMIMessageCode.M_PROP_READ_CON.value,)),
            bytes((CEMIMessageCode.M_PROP_WRITE_CON.value,)),
        ):
            try:
                cemi = CEMIFrame.from_knx(raw_cemi)
            except (CouldNotParseCEMI, UnsupportedCEMIMessage) as ex:
                logger.debug("Ignoring invalid cEMI management frame: %s", ex)
                return
            if isinstance(cemi.data, CEMIMPropReadResponse | CEMIMPropWriteResponse):
                info = cemi.data.property_info
                key = (
                    cemi.code,
                    info.object_type.value,
                    info.object_instance,
                    info.property_id,
                )
                future = self._property_requests.get(key)
                if future is not None and not future.done():
                    future.set_result(cemi)
                    return
        elif raw_cemi[:1] == bytes((CEMIMessageCode.M_RESET_IND.value,)):
            logger.debug("KNX USB interface was reset")
            return
        self.cemi_received_callback(raw_cemi)

    def _emi_received(self, raw: bytes) -> None:
        """Answer a memory read, or pass an EMI1/EMI2 message on as cEMI."""
        if (memory := emi.parse_pc_get_value_con(self._emi, raw)) is not None:
            address, data = memory
            future = self._memory_requests.get(address)
            if future is not None and not future.done():
                future.set_result(data)
            return
        raw_cemi = emi.to_cemi(self._emi, raw, self.busmonitor)
        if raw_cemi is None:
            logger.debug("Ignoring %s message: %s", _EMI_NAMES[self._emi], raw.hex())
            return
        self.cemi_received_callback(raw_cemi)
