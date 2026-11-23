"""
KNX tunnelling over a KNX USB interface.

On connect the bus access server is set up in the order of KNX v01.03.04 - Basic and
System Components - Couplers 09.03 - §3.5.3: the supported EMI types are read, the one
used is activated (cEMI where supported), the bus connection status, the manufacturer
code and the mask version (Device Descriptor Type 0) are read. Then the EMI server is
switched to the data link layer - a cEMI server through PID_COMM_MODE, read back to
verify (KNX v01.04.02 - External Message Interface 03.06.03 - §4.2.2.4.2), an EMI1/EMI2
server through its "system status" or PEI_Switch (§3.1.3, §3.1.4) - and its own
individual address is read.

On disconnect a cEMI interface is closed as it is: whoever connects next sets the
communication mode again, as the cEMI server may be in any mode until then
(KNX v01.04.02 - External Message Interface 03.06.03 - §4.2.2.4.2). An EMI1/EMI2
interface is switched back to its normal mode.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
import logging
from typing import TYPE_CHECKING, Generic, TypeVar

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
from xknx.core import XknxConnectionState, XknxConnectionType
from xknx.exceptions import (
    CommunicationError,
    ConversionError,
    CouldNotParseCEMI,
    CouldNotParseUSBFrame,
    UnsupportedCEMIMessage,
)
from xknx.profile.const import (
    ResourceCEMIServerPropertyId,
    ResourceDevicePropertyId,
    ResourceObjectType,
    ResourcePropertyId,
)
from xknx.secure.data_secure import is_data_secure
from xknx.secure.keyring import InterfaceType, Keyring
from xknx.telegram import IndividualAddress

from ..interface import CEMIBytesCallbackType, Interface
from . import emi
from .const import (
    BCU_ADDRESS_MASKS,
    CEMI_SERVER_ADDRESS_MASKS,
    DEVICE_FEATURE_GET_TIMEOUT,
    EMIID,
    CommunicationMode,
    DeviceFeature,
    DeviceFeatureService,
    ProtocolID,
    SupportedEMIType,
)
from .emi import EMILayer
from .frame import ReportAssembler, USBTransferFrame, device_feature_frame
from .hid_device import (
    HIDDevice,
    USBDeviceInfo,
    find_usb_interfaces,
)

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
# the EMI types in the order they are preferred
_EMI_PREFERENCE = (
    (EMIID.CEMI, SupportedEMIType.CEMI),
    (EMIID.EMI2, SupportedEMIType.EMI2),
    (EMIID.EMI1, SupportedEMIType.EMI1),
)

_MANAGEMENT_RESPONSES = {
    CEMIMessageCode.M_PROP_READ_REQ: CEMIMessageCode.M_PROP_READ_CON,
    CEMIMessageCode.M_PROP_WRITE_REQ: CEMIMessageCode.M_PROP_WRITE_CON,
}
_CONNECTION_CLOSED = "USB connection closed"

# (message code, object type, object instance, property id)
_PropertyKey = tuple[CEMIMessageCode, int, int, int]
_K = TypeVar("_K")
_V = TypeVar("_V")


class _PendingRequests(Generic[_K, _V]):
    """Requests to the interface waiting for their answer, matched by a key."""

    __slots__ = ("_futures",)

    def __init__(self) -> None:
        """Initialize _PendingRequests."""
        self._futures: dict[_K, asyncio.Future[_V]] = {}

    async def request(
        self,
        key: _K,
        send: Callable[[], Awaitable[None]],
        timeout: float,
        timeout_message: str,
    ) -> _V:
        """Send a request and wait for its answer. Raise CommunicationError on timeout."""
        future: asyncio.Future[_V] = asyncio.get_running_loop().create_future()
        self._futures[key] = future
        try:
            await send()
            async with asyncio.timeout(timeout):
                return await future
        except TimeoutError:
            raise CommunicationError(timeout_message) from None
        finally:
            if self._futures.get(key) is future:
                del self._futures[key]

    def resolve(self, key: _K, answer: _V) -> bool:
        """Pass an answer to the request waiting for it. Return whether one did."""
        future = self._futures.get(key)
        if future is None or future.done():
            return False
        future.set_result(answer)
        return True

    def fail_all(self, message: str) -> None:
        """Fail every waiting request."""
        for future in self._futures.values():
            if not future.done():
                future.set_exception(CommunicationError(message))
        self._futures.clear()


@dataclass(frozen=True, slots=True)
class USBInterfaceInfo:
    """
    What a connected KNX USB interface reported about itself.

    `individual_address` is None when it could not be read. `max_apdu_length` is
    informational: xknx doesn't limit the telegrams it sends by it.
    """

    device: USBDeviceInfo
    individual_address: IndividualAddress | None
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

    While the interface reports no bus connection, the connection state is
    DISCONNECTED and nothing can be sent; it is CONNECTED again as soon as the
    interface reports the bus back.
    """

    __slots__ = (
        "_assembler",
        "_bus_connected",
        "_device",
        "_emi",
        "_established",
        "_features",
        "_identify",
        "_info",
        "_last_request_source",
        "_memory",
        "_original_system_status",
        "_properties",
        "_reconnect_on_loss",
        "_reconnect_task",
        "_send_lock",
        "_setup_task",
        "_source_mismatch_logged",
        "auto_reconnect",
        "auto_reconnect_wait",
        "busmonitor",
        "cemi_received_callback",
        "device_info",
        "keyring",
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
        keyring: Keyring | None = None,
    ) -> None:
        """
        Initialize USBTunnel.

        Without any of `vendor_id`, `product_id`, `serial_number` and `path` the
        first known KNX USB interface found is used. `path` alone selects the
        interface at that hidapi device path, also one missing from the known KNX
        USB interfaces. After it was unplugged the interface is looked up again by
        vendor and product id and serial number, so it is found on another USB
        port as well; of several identical interfaces without a serial number the
        one at the old path is preferred, else the first one found is used.

        With `busmonitor` the EMI server is switched to the bus monitor mode
        instead: every frame on the bus is passed on as L_Busmon.ind, and nothing
        can be sent. `CEMIFrame.from_knx()` doesn't parse L_Busmon.ind, so
        `cemi_received_callback` has to handle these frames itself -
        `KNXIPInterface.cemi_received` drops them as unsupported.

        `keyring` is only used to warn, with Data Secure, when the interface's
        individual address is none of the keyring's interfaces.
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
        self.keyring = keyring
        self.device_info: USBDeviceInfo | None = None

        self._assembler = ReportAssembler()
        self._bus_connected = False
        self._device: HIDDevice | None = None
        self._emi = EMIID.CEMI
        self._established = False
        self._features: _PendingRequests[DeviceFeature, bytes] = _PendingRequests()
        # EMI2 PEI_Identify: a single request at a time, key None
        self._identify: _PendingRequests[None, int] = _PendingRequests()
        self._info: USBInterfaceInfo | None = None
        self._last_request_source: IndividualAddress | None = None
        self._memory: _PendingRequests[int, bytes] = _PendingRequests()
        self._original_system_status: int | None = None
        self._properties: _PendingRequests[_PropertyKey, CEMIFrame] = _PendingRequests()
        self._reconnect_on_loss = False
        self._reconnect_task: asyncio.Task[None] | None = None
        self._send_lock = asyncio.Lock()
        self._setup_task: asyncio.Task[None] | None = None
        self._source_mismatch_logged = False

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
        """Find the interface to connect to. Blocks: enumerates the USB devices."""
        if self.device_info is not None:
            # reconnect to the same interface, possibly on another port
            devices = find_usb_interfaces(
                self.device_info.vendor_id,
                self.device_info.product_id,
                self.device_info.serial_number or None,
            )
            for device in devices:
                if device.path == self.device_info.path:
                    return device
        elif self.path is not None:
            devices = find_usb_interfaces(
                self.vendor_id, self.product_id, self.serial_number, path=self.path
            )
            if not devices:
                raise CommunicationError(f"No KNX USB interface at {self.path!r}")
        else:
            devices = find_usb_interfaces(
                self.vendor_id, self.product_id, self.serial_number
            )
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
        self._source_mismatch_logged = False
        try:
            await self._open()
            await self._setup()
        except CommunicationError as ex:
            logger.debug("Could not connect to KNX USB interface: %s", ex)
            await self._connect_failed()
            raise CommunicationError(
                f"USB connection could not be established: {ex}"
            ) from ex
        except BaseException:
            await self._connect_failed()
            raise

        self._established = True
        self._reconnect_on_loss = True
        logger.debug("Connected to KNX USB interface %s", self._info)
        self._announce_connection_state()

    async def _open(self) -> None:
        """Find and open the interface."""
        loop = asyncio.get_running_loop()
        device_info = await loop.run_in_executor(None, self._find_device)
        self._device = HIDDevice(
            device_info,
            report_received=self._report_received,
            connection_lost=self._device_lost,
        )
        await self._device.open()
        # another backend's path when the interface was opened through that one
        self.device_info = self._device.info

    async def _connect_failed(self) -> None:
        """Clean up after a failed connect."""
        self._prepare_disconnect()
        await self._close_device()

    def _announce_connection_state(self) -> None:
        """Set the connection state from the interface's bus connection."""
        if self._bus_connected:
            self.xknx.connection_manager.connection_state_changed(
                XknxConnectionState.CONNECTED, self.connection_type
            )
            return
        logger.warning(
            "KNX USB interface %s is not connected to the bus", self.device_info
        )
        self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )

    async def _setup(self) -> None:
        """Set up the bus access server and the EMI server, in the order of the specification."""
        assert self.device_info is not None
        # KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.3.2
        supported = await self._get_supported_emi_types()
        self._emi = _preferred_emi_type(supported)
        # §3.5.3.4.2
        await self._activate_emi_type(supported)
        # §3.5.3.4
        self._bus_connected = await self._get_bus_connection_status()
        # §3.5.3.4.1
        manufacturer_code = await self._get_optional_feature(
            DeviceFeature.MANUFACTURER_CODE
        )
        # §3.5.3.3.3: before any local device management
        mask_version = await self._get_mask_version()

        if self._emi is EMIID.CEMI:
            await self._set_communication_mode()
            individual_address = await self._read_cemi_individual_address(mask_version)
            max_apdu_length = await self._read_max_apdu_length()
        else:
            self._warn_emi_data_secure()
            await self._switch_emi_layer(
                EMILayer.BUSMONITOR if self.busmonitor else EMILayer.DATA_LINK_LAYER
            )
            individual_address = await self._read_emi_individual_address(mask_version)
            max_apdu_length = emi.MAX_APDU_LENGTH
        self._check_individual_address(individual_address)
        self.xknx.current_address = individual_address or IndividualAddress(0)

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

    async def _get_supported_emi_types(self) -> SupportedEMIType:
        """Get the EMI types the interface supports."""
        data = await self._feature_get(DeviceFeature.SUPPORTED_EMI_TYPE)
        return SupportedEMIType(
            int.from_bytes(data, "big")
            & (SupportedEMIType.EMI1 | SupportedEMIType.EMI2 | SupportedEMIType.CEMI)
        )

    async def _activate_emi_type(self, supported: SupportedEMIType) -> None:
        """
        Activate the EMI type used.

        An interface with a single EMI type needn't support the Set service and
        ignores it then; but the SpaceLogic KNX USB Interface DIN Rail (cEMI only)
        reports no active EMI type (00h) after power-up until it is set - so it is
        always set. With several EMI types the active one is read back.
        """
        await self._feature_set(DeviceFeature.ACTIVE_EMI_TYPE, bytes((self._emi,)))
        if len([flag for flag in SupportedEMIType if flag in supported]) > 1:
            active = await self._feature_get(DeviceFeature.ACTIVE_EMI_TYPE)
            if active[:1] != bytes((self._emi,)):
                raise CommunicationError(
                    f"KNX USB interface did not activate {_EMI_NAMES[self._emi]} "
                    f"(active EMI type {active.hex()})"
                )

    async def _get_bus_connection_status(self) -> bool:
        """Get whether the interface is connected to the bus."""
        data = await self._feature_get(DeviceFeature.BUS_CONNECTION_STATUS)
        logger.debug(
            "KNX USB interface reports the bus connection status %s", data.hex()
        )
        return data[:1] == b"\x01"

    async def _get_optional_feature(self, feature: DeviceFeature) -> int | None:
        """Get an optional 2 octet device feature; None when it isn't answered."""
        try:
            data = await self._feature_get(feature)
        except CommunicationError:
            return None
        return int.from_bytes(data[:2], "big") if len(data) >= 2 else None

    async def _get_mask_version(self) -> int | None:
        """
        Get the Device Descriptor Type 0 of the interface - KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.3.3.

        An EMI1/EMI2 interface that doesn't answer the device feature is asked for
        the memory mapped one at 004Eh.
        """
        mask_version = await self._get_optional_feature(
            DeviceFeature.DEVICE_DESCRIPTOR_TYPE_0
        )
        if mask_version is not None or self._emi is EMIID.CEMI:
            return mask_version
        try:
            data = await self._memory_read(emi.DEVICE_DESCRIPTOR_ADDRESS, 2)
        except CommunicationError:
            return None
        return int.from_bytes(data[:2], "big") if len(data) >= 2 else None

    async def _set_communication_mode(self) -> None:
        """Switch the cEMI server to the data link layer or the bus monitor mode and verify it."""
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

    async def _read_cemi_individual_address(
        self, mask_version: int | None
    ) -> IndividualAddress | None:
        """
        Read the individual address of a cEMI interface; None when it can't be read.

        A stand-alone USB interface (mask 0310h, 2311h) has its own in the cEMI Server
        Object - KNX v02.01.01 - Configuration Procedures 03.05.03 - §3.13.3.2 - where
        the Device Object holds the one of an end device combined with it
        (§3.13.4.2); when the cEMI Server Object isn't answered, the Device Object
        is read. Every other interface has it in the Device Object - KNX v01.04.02 -
        External Message Interface 03.06.03 - §4.2.2.2.
        """
        if mask_version in CEMI_SERVER_ADDRESS_MASKS:
            try:
                return await self._read_address_properties(
                    ResourceObjectType.OBJECT_CEMI_SERVER,
                    ResourceCEMIServerPropertyId.PID_CEMI_SERVER_SNA,
                    ResourceCEMIServerPropertyId.PID_CEMI_SERVER_DEVICE_ADDRESS,
                )
            except CommunicationError as ex:
                logger.debug(
                    "Could not read the individual address from the cEMI Server "
                    "Object, reading the Device Object: %s",
                    ex,
                )
        try:
            return await self._read_address_properties(
                ResourceObjectType.OBJECT_DEVICE,
                ResourceDevicePropertyId.PID_SUBNET_ADDR,
                ResourceDevicePropertyId.PID_DEVICE_ADDR,
            )
        except CommunicationError as ex:
            logger.warning(
                "Could not read the individual address of the KNX USB interface: %s", ex
            )
            return None

    async def _read_address_properties(
        self,
        object_type: ResourceObjectType,
        subnet_property: ResourcePropertyId,
        device_property: ResourcePropertyId,
    ) -> IndividualAddress:
        """Read an individual address from its subnet and device address properties."""
        subnet = await self._property_read(object_type, subnet_property)
        device = await self._property_read(object_type, device_property)
        # a confirmation without data can't be parsed - it is no answer
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

    def _warn_emi_data_secure(self) -> None:
        """Warn that an EMI1/EMI2 interface can't carry most Data Secure telegrams."""
        if self.xknx.cemi_handler.data_secure is not None:
            logger.warning(
                "KNX USB interface %s supports %s only: it can't send or receive "
                "extended frames, which most Data Secure telegrams need. "
                "Use a cEMI interface for Data Secure.",
                self.device_info,
                _EMI_NAMES[self._emi],
            )

    async def _switch_emi_layer(self, layer: EMILayer) -> None:
        """
        Give access to a layer of an EMI1/EMI2 interface.

        EMI2: PEI_Switch.req; EMI1: the "system status" is written and read back -
        KNX v01.04.02 - External Message Interface 03.06.03 - §3.1.3, §3.1.4. Where
        the "system status" is changed, the one before is kept for switching back.
        """
        if self._emi is EMIID.EMI1 or layer is EMILayer.BUSMONITOR:
            self._original_system_status = await self._read_system_status()
        if self._emi is EMIID.EMI2:
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

    async def _read_system_status(self) -> int | None:
        """Read the "system status" of an EMI1/EMI2 interface; None when it isn't answered."""
        try:
            data = await self._memory_read(emi.SYSTEM_STATUS_ADDRESS, 1)
        except CommunicationError as ex:
            logger.debug("Could not read the system status: %s", ex)
            return None
        return data[0] if data else None

    async def _read_emi_individual_address(
        self, mask_version: int | None
    ) -> IndividualAddress | None:
        """
        Read the individual address of an EMI1/EMI2 interface; None when it isn't read.

        EMI2: PEI_Identify, whatever the mask version - KNX v01.04.02 - External
        Message Interface 03.06.03 - §3.3.9.5, §3.3.9.6. Else, and when that isn't
        answered, from the memory - only for a mask version with the address at
        0117h (BCU 1, BCU 2): local device management follows the Device Descriptor
        Type 0 and isn't done for any other - KNX v01.03.04 - Basic and System
        Components - Couplers 09.03 - §3.5.3.3.3.
        """
        if self._emi is EMIID.EMI2:
            try:
                return IndividualAddress(
                    await self._identify.request(
                        None,
                        lambda: self._send_tunnel_frame(bytes((emi.PEI_IDENTIFY_REQ,))),
                        LOCAL_MANAGEMENT_TIMEOUT,
                        "KNX USB interface did not answer PEI_Identify",
                    )
                )
            except CommunicationError as ex:
                logger.debug("%s", ex)
        if mask_version not in BCU_ADDRESS_MASKS:
            logger.warning(
                "KNX USB interface %s has mask version %s: its individual address "
                "is not read",
                self.device_info,
                "unknown" if mask_version is None else f"{mask_version:04X}h",
            )
            return None
        try:
            data = await self._memory_read(emi.INDIVIDUAL_ADDRESS_ADDRESS, 2)
        except CommunicationError as ex:
            logger.warning(
                "Could not read the individual address of the KNX USB interface: %s", ex
            )
            return None
        if len(data) < 2:
            return None
        return IndividualAddress(int.from_bytes(data[:2], "big"))

    def _check_individual_address(
        self, individual_address: IndividualAddress | None
    ) -> None:
        """
        Check the interface's individual address for Data Secure.

        A Data Secure receiver ignores a sender that isn't in its Security Individual
        Address Table, and the source address is part of the MAC - KNX v02.01.01 -
        Application Layer 03.03.07 - §5.1.3.2, §5.2.1.1. While the address is
        unknown, Data Secure telegrams aren't sent (see `send_cemi()`); an address
        that is none of the keyring's interfaces is warned about.
        """
        data_secure = self.xknx.cemi_handler.data_secure is not None
        if individual_address is None:
            logger.warning(
                "Individual address of KNX USB interface %s unknown - %s",
                self.device_info,
                "Data Secure telegrams are not sent until it is known"
                if data_secure
                else "using 0.0.0",
            )
            return
        if data_secure:
            self._check_keyring_address(individual_address)

    def _check_keyring_address(self, individual_address: IndividualAddress) -> None:
        """Warn when the interface's address is none of the keyring's interfaces."""
        if self.keyring is None or self.keyring.get_interface_by_individual_address(
            individual_address
        ):
            return
        usb_interfaces = [
            str(interface.individual_address)
            for interface in self.keyring.interfaces
            if interface.type is InterfaceType.USB
        ]
        logger.warning(
            "KNX USB interface %s has the individual address %s, which is no "
            "interface of the keyring: its Data Secure telegrams may be dropped "
            "unless the devices know this address as a sender. "
            "USB interfaces of the keyring: %s",
            self.device_info,
            individual_address,
            ", ".join(usb_interfaces) or "none",
        )

    def _individual_address_unknown(self) -> bool:
        """Return whether the interface's individual address is unknown."""
        return self._info is not None and self._info.individual_address is None

    def _device_lost(self) -> None:
        """Handle an interface that stopped answering, e.g. because it was unplugged. Callback."""
        logger.warning("Lost connection to KNX USB interface %s", self.device_info)
        self._reconnect_after_loss()

    def _reconnect_after_loss(self) -> None:
        """
        Fail pending requests and start reconnecting.

        Only once connected: a lost interface during the first connect fails that
        connect.
        """
        self._prepare_disconnect()
        if self._reconnect_on_loss and self._reconnect_task is None:

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

    def _server_reset(self) -> None:
        """
        Set the interface up again after its reset or power-up (M_Reset.ind).

        The cEMI server may be back in the communication mode "no layer": the client
        sets PID_COMM_MODE again - KNX v01.04.02 - External Message Interface
        03.06.03 - §4.1.7.5.2, §4.2.2.4.2 Table 17 note c). When that fails, the
        interface is reconnected.
        """
        if not self._established or self._setup_task is not None:
            logger.debug("KNX USB interface was reset")
            return
        logger.info(
            "KNX USB interface %s was reset - setting it up again", self.device_info
        )
        self._established = False
        self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTING, self.connection_type
        )

        def _setup_task_cleanup(_: asyncio.Task[None]) -> None:
            self._setup_task = None

        self._setup_task = asyncio.create_task(self._setup_again())
        self._setup_task.add_done_callback(_setup_task_cleanup)

    async def _setup_again(self) -> None:
        """Run the setup again; reconnect when it fails."""
        try:
            await self._setup()
        except Exception as ex:  # pylint: disable=broad-except
            logger.warning(
                "Could not set up KNX USB interface %s again after its reset: %s",
                self.device_info,
                ex,
            )
            self._reconnect_after_loss()
            return
        self._established = True
        self._announce_connection_state()

    def _prepare_disconnect(self) -> None:
        """Set the connection state and fail pending requests."""
        self._established = False
        self._features.fail_all(_CONNECTION_CLOSED)
        self._identify.fail_all(_CONNECTION_CLOSED)
        self._properties.fail_all(_CONNECTION_CLOSED)
        self._memory.fail_all(_CONNECTION_CLOSED)
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
        self._reconnect_on_loss = False
        self._prepare_disconnect()
        for task in (self._reconnect_task, self._setup_task):
            if task is not None:
                task.cancel()
        if was_established and self._emi is not EMIID.CEMI and self._device is not None:
            try:
                await self._send_tunnel_frame(self._normal_mode_request())
            except CommunicationError as ex:
                logger.debug("Could not switch KNX USB interface back: %s", ex)
        await self._close_device()

    def _normal_mode_request(self) -> bytes:
        """
        Return the EMI message switching an EMI1/EMI2 interface back to normal mode.

        EMI2: the PEI_Switch.req of Figure 2 - with the "system status" before the
        bus monitor mode, which it changed. EMI1: the "system status" before.
        KNX v01.04.02 - External Message Interface 03.06.03 - §3.1.3, §3.1.4. When
        the "system status" before is unknown or left an external layer on, the
        interface is restarted instead (`emi.restart_request()`).
        """
        if self._emi is EMIID.EMI2 and not self.busmonitor:
            return emi.pei_switch(EMILayer.NORMAL)
        status = emi.restorable_system_status(self._original_system_status)
        if status is None:
            logger.debug(
                "Restarting KNX USB interface %s: system status before %s",
                self.device_info,
                "unknown"
                if self._original_system_status is None
                else f"{self._original_system_status:02x}h",
            )
            return emi.restart_request(self._emi)
        if self._emi is EMIID.EMI2:
            return emi.pei_switch(EMILayer.NORMAL, status)
        return emi.pc_set_value(self._emi, emi.SYSTEM_STATUS_ADDRESS, bytes((status,)))

    ####################
    #
    # REQUESTS
    #
    ####################

    async def _write_frame(self, frame: USBTransferFrame) -> None:
        """Write a KNX USB transfer frame."""
        async with self._send_lock:
            device = self._device
            if device is None:
                raise CommunicationError("KNX USB interface not connected")
            for report in frame.to_reports():
                await device.write(report)

    async def _send_tunnel_frame(self, raw: bytes) -> None:
        """Send a message in the EMI type in use."""
        await self._write_frame(
            USBTransferFrame(
                protocol=ProtocolID.KNX_TUNNEL, service=self._emi, body=raw
            )
        )

    async def _memory_read(self, address: int, length: int) -> bytes:
        """Read the memory of an EMI1/EMI2 interface (PC_Get_Value)."""
        return await self._memory.request(
            address,
            lambda: self._send_tunnel_frame(
                emi.pc_get_value(self._emi, address, length)
            ),
            LOCAL_MANAGEMENT_TIMEOUT,
            f"KNX USB interface did not answer PC_Get_Value of {address:04x}h",
        )

    async def _feature_get(self, feature: DeviceFeature) -> bytes:
        """Get a device feature of the bus access server - KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.2.2."""
        return await self._features.request(
            feature,
            lambda: self._write_frame(
                device_feature_frame(DeviceFeatureService.GET, feature)
            ),
            DEVICE_FEATURE_GET_TIMEOUT,
            f"KNX USB interface did not answer Device Feature Get {feature.name}",
        )

    async def _feature_set(self, feature: DeviceFeature, data: bytes) -> None:
        """Set a device feature of the bus access server. It is not answered."""
        await self._write_frame(
            device_feature_frame(DeviceFeatureService.SET, feature, data)
        )

    async def _management_request(self, request: CEMIFrame) -> CEMIFrame:
        """Send a local device management request and wait for its confirmation."""
        assert isinstance(request.data, CEMIMPropReadRequest | CEMIMPropWriteRequest)
        info = request.data.property_info
        return await self._properties.request(
            (
                _MANAGEMENT_RESPONSES[request.code],
                info.object_type.value,
                info.object_instance,
                info.property_id,
            ),
            lambda: self._send_tunnel_frame(request.to_knx()),
            LOCAL_MANAGEMENT_TIMEOUT,
            f"KNX USB interface did not confirm {request.code.name} of property {info.property_id}",
        )

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
        if cemi.code is CEMIMessageCode.L_DATA_REQ and not self._bus_connected:
            raise CommunicationError("KNX USB interface is not connected to the bus")
        if (
            isinstance(cemi.data, CEMILData)
            and is_data_secure(cemi.data)
            and self._individual_address_unknown()
        ):
            # its MAC would cover another source address than the one on the bus
            raise CommunicationError(
                "The individual address of the KNX USB interface is unknown: "
                "Data Secure telegrams can't be sent"
            )
        raw_cemi = cemi.to_knx()
        if self._emi is EMIID.CEMI:
            self._last_request_source = _l_data_source(raw_cemi)
            await self._send_tunnel_frame(raw_cemi)
            return
        try:
            raw = emi.l_data_req_from_cemi(self._emi, raw_cemi)
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
            if self._emi is EMIID.CEMI:
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
            self._features.resolve(feature, frame.feature_data)
        elif (
            frame.service == DeviceFeatureService.INFO
            and feature == DeviceFeature.BUS_CONNECTION_STATUS
        ):
            logger.debug(
                "KNX USB interface informs about the bus connection status %s",
                frame.feature_data.hex(),
            )
            self._bus_connection_changed(frame.feature_data[:1] == b"\x01")

    def _bus_connection_changed(self, connected: bool) -> None:
        """
        Map the bus connection status to the connection state.

        KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.4
        """
        if connected == self._bus_connected:
            return
        self._bus_connected = connected
        if self._info is not None:
            self._info = replace(self._info, bus_connected=connected)
        if not self._established:
            # announced when the setup is done
            return
        if connected:
            logger.info("KNX USB interface is connected to the bus again")
            self._announce_connection_state()
        else:
            logger.warning("KNX USB interface lost its bus connection")
            self.xknx.connection_manager.connection_state_changed(
                XknxConnectionState.DISCONNECTED
            )

    def _cemi_received(self, raw_cemi: bytes) -> None:
        """Pass a cEMI frame on, unless it answers a request of this connection."""
        code = raw_cemi[0] if raw_cemi else None
        if code in (
            CEMIMessageCode.M_PROP_READ_CON.value,
            CEMIMessageCode.M_PROP_WRITE_CON.value,
        ):
            try:
                cemi = CEMIFrame.from_knx(raw_cemi)
            except (CouldNotParseCEMI, UnsupportedCEMIMessage) as ex:
                logger.debug("Ignoring invalid cEMI management frame: %s", ex)
                return
            if isinstance(cemi.data, CEMIMPropReadResponse | CEMIMPropWriteResponse):
                info = cemi.data.property_info
                if self._properties.resolve(
                    (
                        cemi.code,
                        info.object_type.value,
                        info.object_instance,
                        info.property_id,
                    ),
                    cemi,
                ):
                    return
        elif code == CEMIMessageCode.M_RESET_IND.value:
            self._server_reset()
            return
        elif code == CEMIMessageCode.L_DATA_CON.value:
            self._check_confirmation_source(raw_cemi)
        self.cemi_received_callback(raw_cemi)

    def _check_confirmation_source(self, raw_cemi: bytes) -> None:
        """
        Take over or check the source address the interface sent with.

        The L_Data.con carries the source address used - KNX v01.04.02 - External
        Message Interface 03.06.03 - §4.1.5.3.4; with source 0.0.0 requested, the
        interface puts in its own (§4.1.5.3.3). So an individual address that
        couldn't be read is taken from there. Else a source other than requested
        is warned about: Data Secure computes the MAC with the requested one, so
        receivers can't verify such a telegram.
        """
        source = _l_data_source(raw_cemi)
        if source is None:
            return
        requested = self._last_request_source
        if self._individual_address_unknown():
            if requested is not None and not requested.raw and source.raw:
                self._adopt_individual_address(source)
            return
        expected = (
            requested
            if requested is not None and requested.raw
            else self.xknx.current_address
        )
        if source == expected or self._source_mismatch_logged:
            return
        self._source_mismatch_logged = True
        logger.warning(
            "KNX USB interface %s sent with the individual address %s instead of %s%s",
            self.device_info,
            source,
            expected,
            " - receivers can't verify its Data Secure telegrams"
            if self.xknx.cemi_handler.data_secure is not None
            else "",
        )

    def _adopt_individual_address(self, individual_address: IndividualAddress) -> None:
        """Take over the individual address the interface sent with."""
        assert self._info is not None
        self._info = replace(self._info, individual_address=individual_address)
        self.xknx.current_address = individual_address
        logger.info(
            "KNX USB interface %s sends with the individual address %s",
            self.device_info,
            individual_address,
        )
        if self.xknx.cemi_handler.data_secure is not None:
            self._check_keyring_address(individual_address)

    def _emi_received(self, raw: bytes) -> None:
        """Answer a memory read or PEI_Identify, or pass an EMI1/EMI2 message on as cEMI."""
        if (memory := emi.parse_pc_get_value_con(self._emi, raw)) is not None:
            address, data = memory
            self._memory.resolve(address, data)
            return
        if (
            self._emi is EMIID.EMI2
            and (individual_address := emi.parse_pei_identify_con(raw)) is not None
        ):
            self._identify.resolve(None, individual_address)
            return
        raw_cemi = emi.to_cemi(
            self._emi,
            raw,
            busmonitor=self.busmonitor,
            own_address=self.xknx.current_address.raw,
        )
        if raw_cemi is None:
            logger.debug("Ignoring %s message: %s", _EMI_NAMES[self._emi], raw.hex())
            return
        self.cemi_received_callback(raw_cemi)


def _preferred_emi_type(supported: SupportedEMIType) -> EMIID:
    """
    Return the EMI type to use: cEMI, else EMI2, else EMI1.

    Tunnelling frames are only sent in an EMI type the interface supports -
    KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.3.2.
    """
    for emi_id, flag in _EMI_PREFERENCE:
        if flag in supported:
            return emi_id
    raise CommunicationError("KNX USB interface supports no EMI type")


def _l_data_source(raw_cemi: bytes) -> IndividualAddress | None:
    """Return the source address of a cEMI L_Data message; None when it is too short."""
    if len(raw_cemi) < 2:
        return None
    offset = 2 + raw_cemi[1] + 2
    if len(raw_cemi) < offset + 2:
        return None
    return IndividualAddress(int.from_bytes(raw_cemi[offset : offset + 2], "big"))
