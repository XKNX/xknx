"""A simulated KNX USB interface behind a fake `hid` module."""

from __future__ import annotations

from collections.abc import Iterator
import queue
import sys
import threading
from types import ModuleType
from typing import Any

import pytest

from xknx.io.usb.const import (
    EMIID,
    DeviceFeature,
    DeviceFeatureService,
    ProtocolID,
)
from xknx.io.usb.frame import ReportAssembler, USBTransferFrame, device_feature_frame

# what the SpaceLogic KNX USB Interface DIN Rail (16DE:008E) answered
SPACELOGIC_FEATURES = {
    DeviceFeature.SUPPORTED_EMI_TYPE: bytes.fromhex("0004"),
    DeviceFeature.DEVICE_DESCRIPTOR_TYPE_0: bytes.fromhex("07b0"),
    DeviceFeature.BUS_CONNECTION_STATUS: bytes.fromhex("01"),
    DeviceFeature.MANUFACTURER_CODE: bytes.fromhex("00c5"),
    DeviceFeature.ACTIVE_EMI_TYPE: bytes.fromhex("00"),
}
# (object type, property id) -> value
SPACELOGIC_PROPERTIES = {
    (0, 56): bytes.fromhex("0037"),  # PID_MAX_APDU_LENGTH
    (0, 57): bytes.fromhex("10"),  # PID_SUBNET_ADDR
    (0, 58): bytes.fromhex("02"),  # PID_DEVICE_ADDR
    (8, 52): bytes.fromhex("ff"),  # PID_COMM_MODE
}
SPACELOGIC_ENUMERATION = {
    "path": b"usb-path-1",
    "vendor_id": 0x16DE,
    "product_id": 0x008E,
    "serial_number": "00C501053FB2",
    "manufacturer_string": "KNX Manufacturer",
    "product_string": "KNX-USB Interface",
    "usage_page": 0xFF00,
    "usage": 1,
}


class FakeInterface:
    """A cEMI KNX USB interface answering like the real one."""

    def __init__(self) -> None:
        """Initialize FakeInterface."""
        self.features: dict[int, bytes] = dict(SPACELOGIC_FEATURES)
        self.properties: dict[tuple[int, int], bytes] = dict(SPACELOGIC_PROPERTIES)
        # features the interface doesn't answer
        self.silent_features: set[int] = set()
        # set the active EMI type when it is set (False: ignore Set)
        self.accepts_emi_set = True
        # answer requests at all
        self.answers = True
        # what hidapi's write returns - None: the length written
        self.write_result: int | None = None
        # EMI1/EMI2: the memory of the BCU (system status, individual address 1.1.5)
        self.memory: dict[int, bytes] = {0x0060: b"\x1e", 0x0117: b"\x11\x05"}
        self.accepts_memory_writes = True
        self.pei_switch = b""
        # cEMI: the source the interface puts in an L_Data.con (None: the requested)
        self.confirmation_source: bytes | None = None
        self.written: list[USBTransferFrame] = []
        self.unplugged = threading.Event()
        self.open_count = 0
        self._incoming: queue.Queue[bytes] = queue.Queue()
        self._assembler = ReportAssembler()

    def send_report(self, data: bytes) -> None:
        """Send a raw HID report from the interface to the host."""
        self._incoming.put(data.ljust(64, b"\x00"))

    def send_frame(self, frame: USBTransferFrame) -> None:
        """Send a frame from the interface to the host."""
        for report in frame.to_reports():
            self._incoming.put(report)

    def send_cemi(self, raw_cemi: bytes) -> None:
        """Send a cEMI frame from the interface to the host."""
        self.send_frame(
            USBTransferFrame(
                protocol=ProtocolID.KNX_TUNNEL, service=EMIID.CEMI, body=raw_cemi
            )
        )

    def written_cemi(self) -> list[bytes]:
        """Return the cEMI frames the host wrote."""
        return [
            frame.body
            for frame in self.written
            if frame.protocol == ProtocolID.KNX_TUNNEL
        ]

    def read(self, timeout_ms: int) -> list[int]:
        """Return the next report from the interface, or an empty list."""
        if self.unplugged.is_set():
            raise OSError("device disconnected")
        try:
            return list(self._incoming.get(timeout=timeout_ms / 1000))
        except queue.Empty:
            return []

    def write(self, report: bytes) -> int:
        """Handle one report from the host."""
        if self.unplugged.is_set():
            raise OSError("device disconnected")
        if self.write_result is not None:
            return self.write_result
        frame = self._assembler.feed(report)
        if frame is not None:
            self.written.append(frame)
            if self.answers:
                self._handle(frame)
        return len(report)

    def _handle(self, frame: USBTransferFrame) -> None:
        if frame.protocol == ProtocolID.BUS_ACCESS_SERVER_FEATURE:
            feature = frame.body[0]
            if frame.service == DeviceFeatureService.GET:
                if feature in self.features and feature not in self.silent_features:
                    self.send_frame(
                        device_feature_frame(
                            DeviceFeatureService.RESPONSE,
                            DeviceFeature(feature),
                            self.features[feature],
                        )
                    )
            elif (
                frame.service == DeviceFeatureService.SET
                and feature == DeviceFeature.ACTIVE_EMI_TYPE
                and self.accepts_emi_set
            ):
                self.features[feature] = frame.body[1:]
            return
        if frame.service in (EMIID.EMI1, EMIID.EMI2):
            self._handle_emi(EMIID(frame.service), frame.body)
            return
        cemi = frame.body
        code = cemi[0]
        if code == 0xFC:  # M_PropRead.req
            key = (int.from_bytes(cemi[1:3], "big"), cemi[4])
            if key in self.properties:
                self.send_cemi(bytes((0xFB,)) + cemi[1:7] + self.properties[key])
            else:
                # number of elements 0, error "void DP"
                self.send_cemi(
                    bytes((0xFB,)) + cemi[1:5] + bytes((cemi[5] & 0x0F, cemi[6], 0x07))
                )
        elif code == 0xF6:  # M_PropWrite.req
            key = (int.from_bytes(cemi[1:3], "big"), cemi[4])
            self.properties[key] = cemi[7:]
            self.send_cemi(bytes((0xF5,)) + cemi[1:7])
        elif code == 0x11:  # L_Data.req -> L_Data.con
            confirmation = bytes((0x2E,)) + cemi[1:]
            if self.confirmation_source is not None:
                offset = 2 + cemi[1] + 2
                confirmation = (
                    confirmation[:offset]
                    + self.confirmation_source
                    + confirmation[offset + 2 :]
                )
            self.send_cemi(confirmation)
        elif code == 0xF1:  # M_Reset.req
            self.reset()

    def reset(self) -> None:
        """Reset like after a power-up: no layer, no active EMI type, M_Reset.ind."""
        self.properties[(8, 52)] = b"\xff"
        self.features[DeviceFeature.ACTIVE_EMI_TYPE] = b"\x00"
        self.send_cemi(b"\xf0")

    def send_emi(self, emi: EMIID, raw: bytes) -> None:
        """Send an EMI1/EMI2 message from the interface to the host."""
        self.send_frame(
            USBTransferFrame(protocol=ProtocolID.KNX_TUNNEL, service=emi, body=raw)
        )

    def _handle_emi(self, emi: EMIID, raw: bytes) -> None:
        """Answer like a BCU1 (EMI1) or BCU2 (EMI2) based interface."""
        codes = {  # PC_Set_Value.req, PC_Get_Value.req/.con, L_Data.con
            EMIID.EMI1: (0x46, 0x4C, 0x4B, 0x4E),
            EMIID.EMI2: (0xA6, 0xAC, 0xAB, 0x2E),
        }[emi]
        code = raw[0]
        if code == codes[0] and self.accepts_memory_writes:
            address = int.from_bytes(raw[2:4], "big")
            self.memory[address] = raw[4 : 4 + raw[1]]
        elif code == codes[1]:
            address = int.from_bytes(raw[2:4], "big")
            if address in self.memory:
                data = self.memory[address][: raw[1]]
                self.send_emi(emi, bytes((codes[2], raw[1])) + raw[2:4] + data)
        elif code == 0xA9:  # PEI_Switch.req
            self.pei_switch = raw[1:]
        elif code == 0x11:  # L_Data.req -> L_Data.con with the frame's priority
            # the "x" bits set: the host must not interpret them; source unused
            control = 0xD2 | (raw[1] & 0x0C)
            self.send_emi(emi, bytes((codes[3], control)) + b"\xff\xff" + raw[4:])


class FakeHIDDevice:
    """Fake `hid.device`."""

    def __init__(self, module: FakeHIDModule) -> None:
        """Initialize FakeHIDDevice."""
        self._module = module
        self._interface: FakeInterface | None = None

    def open_path(self, path: bytes) -> None:
        """Open a device by its path."""
        interface = self._module.interfaces.get(path)
        if interface is None or interface.unplugged.is_set():
            raise OSError("open failed")
        interface.open_count += 1
        self._interface = interface

    def read(self, max_length: int, timeout_ms: int = 0) -> list[int]:
        """Read one report."""
        assert self._interface is not None
        return self._interface.read(timeout_ms)

    def write(self, data: bytes) -> int:
        """Write one report."""
        assert self._interface is not None
        return self._interface.write(bytes(data))

    def close(self) -> None:
        """Close the device."""
        if self._module.close_error:
            raise OSError("close failed")
        self._module.closed += 1


class FakeHIDModule(ModuleType):
    """Fake hidapi module with simulated KNX USB interfaces."""

    def __init__(self) -> None:
        """Initialize FakeHIDModule."""
        super().__init__("hid")
        self.enumeration: list[dict[str, Any]] = [dict(SPACELOGIC_ENUMERATION)]
        self.interfaces: dict[bytes, FakeInterface] = {
            SPACELOGIC_ENUMERATION["path"]: FakeInterface()
        }
        self.closed = 0
        self.close_error = False

    @property
    def interface(self) -> FakeInterface:
        """Return the first simulated interface."""
        return self.interfaces[SPACELOGIC_ENUMERATION["path"]]

    def enumerate(
        self, vendor_id: int = 0, product_id: int = 0
    ) -> list[dict[str, Any]]:
        """List HID devices like hidapi."""
        return [
            dict(device)
            for device in self.enumeration
            if (not vendor_id or device["vendor_id"] == vendor_id)
            and (not product_id or device["product_id"] == product_id)
            and not self.interfaces.get(
                device["path"], FakeInterface()
            ).unplugged.is_set()
        ]

    def device(self) -> FakeHIDDevice:
        """Create a device handle."""
        return FakeHIDDevice(self)


def make_emi_interface(
    interface: FakeInterface, emi: EMIID, mask_version: int | None
) -> None:
    """Make the simulated interface one with EMI1 or EMI2 only, of a mask version (None: not answered)."""
    interface.features[DeviceFeature.SUPPORTED_EMI_TYPE] = (1 << (emi - 1)).to_bytes(
        2, "big"
    )
    if mask_version is None:
        interface.silent_features.add(DeviceFeature.DEVICE_DESCRIPTOR_TYPE_0)
    else:
        interface.features[DeviceFeature.DEVICE_DESCRIPTOR_TYPE_0] = (
            mask_version.to_bytes(2, "big")
        )


@pytest.fixture
def fake_hid(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeHIDModule]:
    """Replace hidapi by a fake module with a simulated KNX USB interface."""
    module = FakeHIDModule()
    monkeypatch.setitem(sys.modules, "hid", module)
    # not the real hidraw backend of an installed hidapi on Linux
    monkeypatch.setitem(sys.modules, "hidraw", None)
    yield module
    for interface in module.interfaces.values():
        interface.unplugged.set()
