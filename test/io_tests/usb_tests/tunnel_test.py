"""Tests for tunnelling over KNX USB interfaces."""

import asyncio
from collections.abc import Callable
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

from xknx import XKNX
from xknx.cemi import CEMIFrame, CEMILData, CEMIMessageCode
from xknx.core import XknxConnectionState, XknxConnectionType
from xknx.dpt import DPTBinary
from xknx.exceptions import CommunicationError
from xknx.io import ConnectionConfig, ConnectionType, USBConfig
from xknx.io.knxip_interface import KNXIPInterface
from xknx.io.usb import (
    USBTunnel,
    find_usb_interfaces,
    hid_device,
    is_knx_usb_interface,
    tunnel as usb_tunnel,
)
from xknx.io.usb.const import (
    EMIID,
    DeviceFeature,
    DeviceFeatureService,
    ProtocolID,
    SupportedEMIType,
)
from xknx.io.usb.frame import USBTransferFrame, device_feature_frame
from xknx.io.usb.hid_device import HIDDevice, USBDeviceInfo
from xknx.profile.const import ResourceCEMIServerPropertyId, ResourceObjectType
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import GroupValueWrite

from .conftest import SPACELOGIC_ENUMERATION, FakeHIDModule


async def _until(condition: Callable[[], bool], timeout: float = 2.0) -> None:
    """Wait for something done by the reader thread - it can't set an asyncio.Event."""
    async with asyncio.timeout(timeout):
        while not condition():  # noqa: ASYNC110
            await asyncio.sleep(0.01)


@pytest.fixture(autouse=True)
def short_timeouts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Don't wait long for answers the fake interface doesn't give."""
    monkeypatch.setattr(usb_tunnel, "DEVICE_FEATURE_GET_TIMEOUT", 0.2)
    monkeypatch.setattr(usb_tunnel, "LOCAL_MANAGEMENT_TIMEOUT", 0.2)


class TestUSBTunnel:
    """Test USBTunnel against a simulated interface."""

    def setup_method(self) -> None:
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.xknx = XKNX()
        self.cemi_received = Mock()
        self.states: list[tuple[XknxConnectionState, XknxConnectionType]] = []
        self.xknx.connection_manager.register_connection_state_changed_cb(
            lambda state: self.states.append(
                (state, self.xknx.connection_manager.connection_type)
            )
        )

    def tunnel(self, **kwargs: object) -> USBTunnel:
        """Create a tunnel."""
        return USBTunnel(
            self.xknx,
            cemi_received_callback=self.cemi_received,
            auto_reconnect=False,
            **kwargs,  # type: ignore[arg-type]
        )

    async def test_connect(self, fake_hid: FakeHIDModule) -> None:
        """Test setting up the interface on connect."""
        tunnel = self.tunnel()
        await tunnel.connect()
        interface = fake_hid.interface

        feature_frames = [
            (frame.service, frame.body)
            for frame in interface.written
            if frame.protocol == ProtocolID.BUS_ACCESS_SERVER_FEATURE
        ]
        assert feature_frames == [
            (DeviceFeatureService.GET, b"\x01"),
            # set although cEMI is the only type - the interface reported none active
            (DeviceFeatureService.SET, b"\x05\x03"),
            (DeviceFeatureService.GET, b"\x03"),
            (DeviceFeatureService.GET, b"\x04"),
            (DeviceFeatureService.GET, b"\x02"),
        ]
        assert interface.written_cemi() == [
            bytes.fromhex("f6000801341001 00"),  # PID_COMM_MODE := data link layer
            bytes.fromhex("fc000801341001"),  # PID_COMM_MODE read back
            bytes.fromhex("fc000001391001"),  # PID_SUBNET_ADDR
            bytes.fromhex("fc0000013a1001"),  # PID_DEVICE_ADDR
            bytes.fromhex("fc000001381001"),  # PID_MAX_APDU_LENGTH
        ]
        assert interface.properties[(8, 52)] == b"\x00"
        assert self.xknx.current_address == IndividualAddress("1.0.2")
        info = tunnel.info
        assert info is not None
        assert info.individual_address == IndividualAddress("1.0.2")
        assert info.max_apdu_length == 55
        assert info.supported_emi_types == SupportedEMIType.CEMI
        assert info.bus_connected
        assert info.manufacturer_code == 0x00C5
        assert info.mask_version == 0x07B0
        assert info.device.serial_number == "00C501053FB2"
        assert self.states == [
            (XknxConnectionState.CONNECTING, XknxConnectionType.USB),
            (XknxConnectionState.CONNECTED, XknxConnectionType.USB),
        ]
        await tunnel.disconnect()

    async def test_disconnect(self, fake_hid: FakeHIDModule) -> None:
        """Test disconnect closes the device as it is."""
        tunnel = self.tunnel()
        await tunnel.connect()
        sent = len(fake_hid.interface.written)
        await tunnel.disconnect()
        interface = fake_hid.interface
        # nothing is sent on disconnect: the next connect sets the mode again
        assert len(interface.written) == sent
        assert interface.properties[(8, 52)] == b"\x00"
        assert fake_hid.closed == 1
        assert self.states[-1][0] is XknxConnectionState.DISCONNECTED
        # a reset indication (e.g. after another client reset it) isn't passed on
        tunnel.cemi_received_callback = self.cemi_received
        tunnel._cemi_received(b"\xf0")
        self.cemi_received.assert_not_called()
        with pytest.raises(CommunicationError):
            await tunnel.send_cemi(
                CEMIFrame(code=CEMIMessageCode.M_RESET_REQ, data=None)
            )

    async def test_send_and_receive(self, fake_hid: FakeHIDModule) -> None:
        """Test frames are sent in cEMI and confirmations and indications passed on."""
        tunnel = self.tunnel()
        await tunnel.connect()
        cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_REQ,
            data=CEMILData.init_from_telegram(
                Telegram(
                    destination_address=GroupAddress("1/2/3"),
                    payload=GroupValueWrite(DPTBinary(1)),
                ),
                src_addr=IndividualAddress("1.0.2"),
            ),
        )
        await tunnel.send_cemi(cemi)
        raw = cemi.to_knx()
        assert fake_hid.interface.written_cemi()[-1] == raw
        await _until(lambda: self.cemi_received.call_count == 1)
        assert self.cemi_received.call_args.args[0] == bytes((0x2E,)) + raw[1:]

        # an indication from the bus
        fake_hid.interface.send_cemi(bytes.fromhex("2900bce0102f0012030080346a"))
        await _until(lambda: self.cemi_received.call_count == 2)
        assert self.cemi_received.call_args.args[0] == bytes.fromhex(
            "2900bce0102f0012030080346a"
        )
        # property confirmations nobody of this connection waits for are passed on
        fake_hid.interface.send_cemi(bytes.fromhex("fb000001391001 10"))
        await _until(lambda: self.cemi_received.call_count == 3)
        # frames in another EMI type and other protocols are ignored
        fake_hid.interface.send_frame(
            device_feature_frame(
                DeviceFeatureService.INFO, DeviceFeature.MANUFACTURER_CODE
            )
        )
        await asyncio.sleep(0.2)
        assert self.cemi_received.call_count == 3
        await tunnel.disconnect()

    async def test_busmonitor(self, fake_hid: FakeHIDModule) -> None:
        """Test the bus monitor mode."""
        tunnel = self.tunnel(busmonitor=True)
        await tunnel.connect()
        interface = fake_hid.interface
        assert interface.written_cemi()[0] == bytes.fromhex("f60008013410 0101")
        assert interface.properties[(8, 52)] == b"\x01"
        busmon = bytes.fromhex("2b0703010304020300bce0102f0012030080346a")
        interface.send_cemi(busmon)
        await _until(lambda: self.cemi_received.call_count == 1)
        assert self.cemi_received.call_args.args[0] == busmon
        with pytest.raises(CommunicationError, match="bus monitor mode"):
            await tunnel.send_cemi(
                CEMIFrame(code=CEMIMessageCode.M_RESET_REQ, data=None)
            )
        await tunnel.disconnect()

    async def test_bus_connection_info(self, fake_hid: FakeHIDModule) -> None:
        """Test the interface informing about its bus connection."""
        tunnel = self.tunnel()
        await tunnel.connect()
        fake_hid.interface.send_frame(
            device_feature_frame(
                DeviceFeatureService.INFO, DeviceFeature.BUS_CONNECTION_STATUS, b"\x00"
            )
        )
        await _until(lambda: tunnel.info is not None and not tunnel.info.bus_connected)
        fake_hid.interface.send_frame(
            device_feature_frame(
                DeviceFeatureService.INFO, DeviceFeature.BUS_CONNECTION_STATUS, b"\x01"
            )
        )
        await _until(lambda: tunnel.info is not None and tunnel.info.bus_connected)
        await tunnel.disconnect()

    async def test_no_emi_type(self, fake_hid: FakeHIDModule) -> None:
        """Test an interface without any EMI type is refused."""
        fake_hid.interface.features[DeviceFeature.SUPPORTED_EMI_TYPE] = b"\x00\x08"
        tunnel = self.tunnel()
        with pytest.raises(CommunicationError, match="supports no EMI type"):
            await tunnel.connect()
        # nothing tunnelled to it
        assert fake_hid.interface.written_cemi() == []
        assert fake_hid.closed == 1
        assert self.states[-1][0] is XknxConnectionState.DISCONNECTED

    async def test_several_emi_types(self, fake_hid: FakeHIDModule) -> None:
        """Test the active EMI type is checked when there is a choice."""
        interface = fake_hid.interface
        interface.features[DeviceFeature.SUPPORTED_EMI_TYPE] = b"\x00\x06"
        interface.features[DeviceFeature.ACTIVE_EMI_TYPE] = b"\x02"
        tunnel = self.tunnel()
        await tunnel.connect()
        assert interface.features[DeviceFeature.ACTIVE_EMI_TYPE] == b"\x03"
        assert tunnel.info is not None
        assert tunnel.info.supported_emi_types == (
            SupportedEMIType.EMI2 | SupportedEMIType.CEMI
        )
        await tunnel.disconnect()

        # an interface that doesn't switch
        interface.features[DeviceFeature.ACTIVE_EMI_TYPE] = b"\x02"
        interface.accepts_emi_set = False
        with pytest.raises(CommunicationError, match="did not activate cEMI"):
            await self.tunnel().connect()

    async def test_no_answer(self, fake_hid: FakeHIDModule) -> None:
        """Test an interface not answering the mandatory feature."""
        fake_hid.interface.silent_features.add(DeviceFeature.SUPPORTED_EMI_TYPE)
        with pytest.raises(CommunicationError, match="did not answer"):
            await self.tunnel().connect()

    async def test_optional_values_missing(self, fake_hid: FakeHIDModule) -> None:
        """Test an interface without the optional features and properties."""
        interface = fake_hid.interface
        interface.silent_features |= {
            DeviceFeature.MANUFACTURER_CODE,
            DeviceFeature.DEVICE_DESCRIPTOR_TYPE_0,
        }
        del interface.properties[(0, 56)]
        del interface.properties[(0, 57)]
        tunnel = self.tunnel()
        await tunnel.connect()
        assert tunnel.info is not None
        assert tunnel.info.manufacturer_code is None
        assert tunnel.info.mask_version is None
        assert tunnel.info.max_apdu_length == 15
        assert tunnel.info.individual_address == IndividualAddress(0)
        await tunnel.disconnect()

    async def test_comm_mode_refused(self, fake_hid: FakeHIDModule) -> None:
        """Test an interface refusing the data link layer."""
        interface = fake_hid.interface

        def refuse(frame: object, original=interface._handle) -> None:  # noqa: ANN001
            body = getattr(frame, "body", b"")
            if body[:1] == b"\xf6":
                interface.send_cemi(
                    bytes((0xF5,)) + body[1:5] + bytes((0x00, 0x01, 0x05))
                )
                return
            original(frame)

        interface._handle = refuse  # type: ignore[method-assign]
        with pytest.raises(CommunicationError, match="PID_COMM_MODE"):
            await self.tunnel().connect()

    async def test_comm_mode_not_switched(self, fake_hid: FakeHIDModule) -> None:
        """Test an interface confirming the data link layer without switching to it."""
        interface = fake_hid.interface

        def ignore(frame: object, original=interface._handle) -> None:  # noqa: ANN001
            body = getattr(frame, "body", b"")
            if body[:1] == b"\xf6":
                interface.send_cemi(bytes((0xF5,)) + body[1:7])
                return
            original(frame)

        interface._handle = ignore  # type: ignore[method-assign]
        with pytest.raises(CommunicationError, match=r"did not switch.*it is in ff"):
            await self.tunnel().connect()

    async def test_not_found(self, fake_hid: FakeHIDModule) -> None:
        """Test no interface found."""
        fake_hid.enumeration.clear()
        with pytest.raises(CommunicationError, match="No KNX USB interface found"):
            await self.tunnel().connect()
        assert self.states[-1][0] is XknxConnectionState.DISCONNECTED

    async def test_by_path(self, fake_hid: FakeHIDModule) -> None:
        """Test selecting an interface by its path."""
        await (tunnel := self.tunnel(path=b"usb-path-1")).connect()
        await tunnel.disconnect()
        with pytest.raises(CommunicationError, match="No KNX USB interface at"):
            await self.tunnel(path=b"elsewhere").connect()

    async def test_open_fails(self, fake_hid: FakeHIDModule) -> None:
        """Test an interface that can't be opened."""
        fake_hid.interfaces.clear()
        with pytest.raises(CommunicationError, match="Could not open"):
            await self.tunnel().connect()

    async def test_unplugged_without_reconnect(self, fake_hid: FakeHIDModule) -> None:
        """Test unplugging the interface."""
        tunnel = self.tunnel()
        await tunnel.connect()
        fake_hid.interface.unplugged.set()
        await _until(lambda: self.states[-1][0] is XknxConnectionState.DISCONNECTED)
        await _until(lambda: fake_hid.closed == 1)
        with pytest.raises(CommunicationError):
            await tunnel.send_cemi(
                CEMIFrame(code=CEMIMessageCode.M_RESET_REQ, data=None)
            )
        await tunnel.disconnect()

    async def test_unplugged_and_reconnected(self, fake_hid: FakeHIDModule) -> None:
        """Test the interface is connected again when it's back."""
        tunnel = USBTunnel(
            self.xknx,
            cemi_received_callback=self.cemi_received,
            auto_reconnect=True,
            auto_reconnect_wait=0,
        )
        await tunnel.connect()
        interface = fake_hid.interface
        interface.unplugged.set()
        await _until(lambda: self.states[-1][0] is XknxConnectionState.DISCONNECTED)
        interface.unplugged.clear()
        await _until(lambda: self.states[-1][0] is XknxConnectionState.CONNECTED)
        assert interface.open_count == 2
        await tunnel.stop_reconnect()
        await tunnel.disconnect()

    async def test_stop_reconnect(self, fake_hid: FakeHIDModule) -> None:
        """Test a running reconnect is stopped."""
        tunnel = USBTunnel(
            self.xknx,
            cemi_received_callback=self.cemi_received,
            auto_reconnect=True,
            auto_reconnect_wait=0,
        )
        await tunnel.connect()
        fake_hid.interface.unplugged.set()
        await _until(lambda: self.states[-1][0] is XknxConnectionState.DISCONNECTED)
        await tunnel.stop_reconnect()
        await asyncio.sleep(0.1)
        await tunnel.disconnect()
        assert self.states[-1][0] is XknxConnectionState.DISCONNECTED

    async def test_ignored_frames(self, fake_hid: FakeHIDModule) -> None:
        """Test invalid and foreign frames are dropped."""
        tunnel = self.tunnel()
        await tunnel.connect()
        interface = fake_hid.interface
        # header length 7
        interface.send_report(bytes.fromhex("011309000700010f01000001"))
        interface.send_frame(
            USBTransferFrame(
                protocol=ProtocolID.KNX_TUNNEL, service=EMIID.EMI2, body=b"\x29\x00"
            )
        )
        interface.send_frame(
            USBTransferFrame(protocol=ProtocolID.M_BUS_TUNNEL, service=0, body=b"\x00")
        )
        interface.send_frame(
            USBTransferFrame(
                protocol=ProtocolID.BUS_ACCESS_SERVER_FEATURE,
                service=DeviceFeatureService.INFO,
                body=b"\x99",
            )
        )
        # a property confirmation too short to parse
        interface.send_cemi(bytes.fromhex("fb0000"))
        # and one frame that is passed on, after all others were handled
        interface.send_cemi(bytes.fromhex("2900bce0102f0012030080346a"))
        await _until(lambda: self.cemi_received.call_count == 1)
        assert self.cemi_received.call_args.args[0][0] == 0x29
        await tunnel.disconnect()

    async def test_requests_failed_by_unplugging(
        self, fake_hid: FakeHIDModule, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test requests waiting for an answer fail when the interface is gone."""
        monkeypatch.setattr(usb_tunnel, "DEVICE_FEATURE_GET_TIMEOUT", 5)
        monkeypatch.setattr(usb_tunnel, "LOCAL_MANAGEMENT_TIMEOUT", 5)
        tunnel = self.tunnel()
        await tunnel.connect()
        interface = fake_hid.interface
        interface.answers = False
        feature = asyncio.create_task(
            tunnel._feature_get(DeviceFeature.MANUFACTURER_CODE)
        )
        prop = asyncio.create_task(tunnel._read_max_apdu_length())
        await _until(lambda: len(interface.written) >= 11)
        interface.unplugged.set()
        with pytest.raises(CommunicationError, match="USB connection closed"):
            await feature
        # the APDU length falls back to the one of a short frame
        assert await prop == 15
        await tunnel.disconnect()

    async def test_management_timeout(self, fake_hid: FakeHIDModule) -> None:
        """Test a property request without confirmation."""
        tunnel = self.tunnel()
        await tunnel.connect()
        fake_hid.interface.answers = False
        with pytest.raises(CommunicationError, match="did not confirm"):
            await tunnel._property_write(
                ResourceObjectType.OBJECT_CEMI_SERVER,
                ResourceCEMIServerPropertyId.PID_COMM_MODE,
                b"\x01",
            )
        await tunnel.disconnect()

    async def test_disconnect_when_writing_fails(self, fake_hid: FakeHIDModule) -> None:
        """Test disconnecting an interface that no longer takes writes."""
        tunnel = self.tunnel()
        await tunnel.connect()
        fake_hid.interface.write_result = -1
        await tunnel.disconnect()
        assert fake_hid.closed == 1
        # nothing to write to any more
        with pytest.raises(CommunicationError, match="not connected"):
            await tunnel._send_tunnel_frame(b"\xf1")

    async def test_reconnect_survives_unexpected_errors(
        self, fake_hid: FakeHIDModule
    ) -> None:
        """Test reconnecting goes on after an unexpected error, until disconnected."""
        tunnel = USBTunnel(
            self.xknx,
            cemi_received_callback=self.cemi_received,
            auto_reconnect=True,
            auto_reconnect_wait=0,
        )
        await tunnel.connect()
        with patch.object(
            USBTunnel, "connect", AsyncMock(side_effect=RuntimeError("boom"))
        ) as connect:
            fake_hid.interface.unplugged.set()
            await _until(lambda: connect.await_count >= 2)
            # disconnecting ends the reconnect
            await tunnel.disconnect()
            count = connect.await_count
            await asyncio.sleep(0.05)
            assert connect.await_count == count


class TestHIDDevice:
    """Test the hidapi wrapper."""

    async def test_write_errors(self, fake_hid: FakeHIDModule) -> None:
        """Test failing writes and closing raise or log, as they should."""
        info = find_usb_interfaces()[0]
        device = HIDDevice(info, report_received=Mock(), connection_lost=Mock())
        with pytest.raises(CommunicationError, match="not open"):
            await device.write(bytes(64))
        await device.open()
        fake_hid.interface.write_result = -1
        with pytest.raises(CommunicationError, match="returned -1"):
            await device.write(bytes(64))
        fake_hid.close_error = True
        await device.close()
        assert fake_hid.closed == 0


class TestDiscovery:
    """Test finding KNX USB interfaces."""

    def test_known_interfaces(self, fake_hid: FakeHIDModule) -> None:
        """Test only KNX USB interfaces are listed."""
        fake_hid.enumeration += [
            # a keyboard of a KNX vendor
            {**SPACELOGIC_ENUMERATION, "path": b"kbd", "usage_page": 0x01},
            # an unknown vendor-defined HID device
            {**SPACELOGIC_ENUMERATION, "path": b"other", "vendor_id": 0x1234},
            # a vendor whose devices are all KNX interfaces
            {
                **SPACELOGIC_ENUMERATION,
                "path": b"weinzierl",
                "vendor_id": 0x0E77,
                "product_id": 0x9999,
                "usage_page": 0,
                "serial_number": None,
            },
            # the same device twice
            dict(SPACELOGIC_ENUMERATION),
        ]
        devices = find_usb_interfaces()
        assert [device.path for device in devices] == [b"usb-path-1", b"weinzierl"]
        assert devices[1].serial_number == ""
        assert str(devices[0]) == (
            "KNX Manufacturer KNX-USB Interface (16de:008e serial 00C501053FB2)"
        )
        # an explicit vendor finds unknown interfaces
        assert [device.path for device in find_usb_interfaces(0x1234)] == [b"other"]
        assert not find_usb_interfaces(serial_number="nope")
        assert is_knx_usb_interface(0x135E, 0x4711)
        assert not is_knx_usb_interface(0x16DE, 0x0001)

    async def test_without_hidapi(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test a clear error without hidapi installed."""
        monkeypatch.setitem(sys.modules, "hid", None)
        monkeypatch.setitem(sys.modules, "hidraw", None)
        with pytest.raises(CommunicationError, match="xknx\\[usb\\]"):
            find_usb_interfaces()
        device = HIDDevice(
            USBDeviceInfo(0x16DE, 0x008E, b"p"),
            report_received=Mock(),
            connection_lost=Mock(),
        )
        with pytest.raises(CommunicationError, match="xknx\\[usb\\]"):
            await device.open()

    async def test_backends_in_order(
        self, fake_hid: FakeHIDModule, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test the first backend that finds an interface is used, also to open it."""
        monkeypatch.setattr(hid_device, "_BACKENDS", ("hidraw", "hid"))
        hidraw = FakeHIDModule()
        monkeypatch.setitem(sys.modules, "hidraw", hidraw)
        # hidraw finds nothing (a kernel without it): libusb's
        hidraw.enumeration.clear()
        devices = find_usb_interfaces()
        assert [device.backend for device in devices] == ["hid"]
        # hidraw finds it
        hidraw.enumeration.append({**SPACELOGIC_ENUMERATION, "path": b"/dev/hidraw3"})
        hidraw.interfaces[b"/dev/hidraw3"] = hidraw.interface
        devices = find_usb_interfaces()
        assert [(device.backend, device.path) for device in devices] == [
            ("hidraw", b"/dev/hidraw3")
        ]
        device = HIDDevice(devices[0], report_received=Mock(), connection_lost=Mock())
        await device.open()
        await device.close()
        assert hidraw.interface.open_count == 1
        assert fake_hid.interface.open_count == 0


class TestKNXIPInterfaceUSB:
    """Test starting a USB connection from the connection config."""

    async def test_start_usb(self) -> None:
        """Test ConnectionType.USB starts a USB tunnel."""
        xknx = XKNX()
        interface = KNXIPInterface(
            xknx,
            connection_config=ConnectionConfig(
                connection_type=ConnectionType.USB,
                usb_config=USBConfig(vendor_id=0x16DE, serial_number="00C501053FB2"),
                auto_reconnect_wait=7,
            ),
        )
        with patch.object(USBTunnel, "connect", AsyncMock()) as connect:
            await interface.start()
        connect.assert_awaited_once()
        tunnel = interface._interface
        assert isinstance(tunnel, USBTunnel)
        assert tunnel.vendor_id == 0x16DE
        assert tunnel.serial_number == "00C501053FB2"
        assert tunnel.auto_reconnect_wait == 7
        assert interface.usb_interface_info() is None
        assert await interface.gateway_info() is None

    def test_usb_config_default(self) -> None:
        """Test the default USB config."""
        assert ConnectionConfig().usb_config == USBConfig()
