"""
Access to KNX USB interfaces through hidapi.

KNX USB interfaces are HID class devices with one interrupt IN and one interrupt
OUT endpoint exchanging 64 octet reports - KNX v01.03.04 - Basic and System
Components - Couplers 09.03 - §3.3.2.4. hidapi talks to them without a special
driver on Windows, Linux and macOS. It is an optional dependency: `pip install xknx[usb]`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
import importlib
import logging
import sys
import threading
from typing import Any, Final

from xknx.exceptions import CommunicationError

from .const import HID_REPORT_LENGTH

logger = logging.getLogger("xknx.log")
raw_socket_logger = logging.getLogger("xknx.raw_socket")

# USB vendors whose HID devices are KNX USB interfaces, whatever the product id
KNX_USB_VENDOR_IDS: Final = frozenset(
    {
        0x0E77,  # Weinzierl Engineering
        0x135E,  # Insta
        0x28C2,  # Tapko Technologies
        0x2A07,  # ise
    }
)
# further KNX USB interfaces by vendor and product id
KNX_USB_DEVICE_IDS: Final = frozenset(
    {
        (0x0111, 0x1022),
        (0x0403, 0x6898),
        (0x04CC, 0x0301),
        (0x0681, 0x0014),
        (0x0908, 0x02DC),
        (0x0908, 0x02DD),
        (0x0908, 0x02E6),
        (0x145C, 0x1330),
        (0x145C, 0x1490),
        (0x147B, 0x2200),
        (0x147B, 0x5120),
        (0x16D0, 0x0490),
        (0x16D0, 0x0491),
        (0x16D0, 0x0492),
        (0x16DE, 0x008E),
        (0x24D5, 0x0106),
        (0x2D72, 0x0002),
        (0x36CE, 0x0001),
        (0x7660, 0x0002),
    }
)
# usage pages below this are standard HID devices (keyboards, mice, ...)
_VENDOR_DEFINED_USAGE_PAGE: Final = 0xFF00
# hidapi read timeout in ms - bounds how long closing waits for the reader thread
_READ_TIMEOUT_MS: Final = 100


# hidapi backends, in the order they are tried: on Linux the kernel's hidraw driver
# first - the interface stays with the kernel's HID driver and access is granted by
# the permissions of /dev/hidraw* - then libusb, e.g. for a kernel without hidraw
_BACKENDS: Final = ("hidraw", "hid") if sys.platform.startswith("linux") else ("hid",)
_MISSING_HIDAPI: Final = (
    "KNX USB interfaces need the 'hidapi' package: pip install xknx[usb]"
)


def _backend(name: str) -> Any:
    """Import a hidapi backend module."""
    try:
        return importlib.import_module(name)
    except ImportError as err:
        raise CommunicationError(_MISSING_HIDAPI) from err


def _backends() -> list[tuple[str, Any]]:
    """Import the hidapi backends available here."""
    modules: list[tuple[str, Any]] = []
    for name in _BACKENDS:
        try:
            modules.append((name, importlib.import_module(name)))
        except ImportError:
            continue
    if not modules:
        raise CommunicationError(_MISSING_HIDAPI)
    return modules


@dataclass(frozen=True, slots=True)
class USBDeviceInfo:
    """A KNX USB interface found on this host."""

    vendor_id: int
    product_id: int
    path: bytes
    serial_number: str = ""
    manufacturer: str = ""
    product: str = ""
    # the hidapi backend module the path belongs to
    backend: str = "hid"

    @classmethod
    def from_hid(cls, device: dict[str, Any], backend: str = "hid") -> USBDeviceInfo:
        """Create from an entry of `hid.enumerate()`."""
        return cls(
            vendor_id=device.get("vendor_id") or 0,
            product_id=device.get("product_id") or 0,
            path=device.get("path") or b"",
            serial_number=device.get("serial_number") or "",
            manufacturer=device.get("manufacturer_string") or "",
            product=device.get("product_string") or "",
            backend=backend,
        )

    def __str__(self) -> str:
        """Return a readable description."""
        name = " ".join(part for part in (self.manufacturer, self.product) if part)
        serial = f" serial {self.serial_number}" if self.serial_number else ""
        return f"{name or 'KNX USB interface'} ({self.vendor_id:04x}:{self.product_id:04x}{serial})"


def is_knx_usb_interface(vendor_id: int, product_id: int) -> bool:
    """Return whether vendor and product id belong to a known KNX USB interface."""
    return (
        vendor_id in KNX_USB_VENDOR_IDS or (vendor_id, product_id) in KNX_USB_DEVICE_IDS
    )


def find_usb_interfaces(
    vendor_id: int | None = None,
    product_id: int | None = None,
    serial_number: str | None = None,
) -> list[USBDeviceInfo]:
    """
    List the KNX USB interfaces connected to this host.

    Without `vendor_id` only known KNX USB interfaces are listed; with it, every
    HID device of that vendor (and product) is, so an interface missing from the
    known ones can be used too. The interfaces come from the first hidapi backend
    that finds any.
    """
    for backend, hid in _backends():
        found: dict[bytes, USBDeviceInfo] = {}
        for device in hid.enumerate(vendor_id or 0, product_id or 0):
            info = USBDeviceInfo.from_hid(device, backend)
            # hidapi reports usage page 0 where the platform doesn't know it (libusb)
            usage_page = device.get("usage_page") or 0
            if 0 < usage_page < _VENDOR_DEFINED_USAGE_PAGE:
                continue
            if vendor_id is None and not is_knx_usb_interface(
                info.vendor_id, info.product_id
            ):
                continue
            if serial_number and info.serial_number != serial_number:
                continue
            found.setdefault(info.path, info)
        if found:
            return list(found.values())
    return []


class HIDDevice:
    """
    An open KNX USB interface.

    A reader thread passes every incoming HID report to `report_received` in the
    event loop; when reading fails (eg. the interface was unplugged)
    `connection_lost` is called once. Reports are written one after another by a
    worker thread, so the event loop never blocks on USB.
    """

    __slots__ = (
        "_closing",
        "_device",
        "_loop",
        "_reader",
        "_writer",
        "connection_lost",
        "info",
        "report_received",
    )

    def __init__(
        self,
        info: USBDeviceInfo,
        report_received: Callable[[bytes], None],
        connection_lost: Callable[[], None],
    ) -> None:
        """Initialize HIDDevice."""
        self.info = info
        self.report_received = report_received
        self.connection_lost = connection_lost
        self._closing = threading.Event()
        self._device: Any = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._reader: threading.Thread | None = None
        self._writer: ThreadPoolExecutor | None = None

    async def open(self) -> None:
        """Open the device and start reading. Raise CommunicationError on failure."""
        hid = _backend(self.info.backend)
        self._loop = asyncio.get_running_loop()
        device = hid.device()
        try:
            await self._loop.run_in_executor(None, device.open_path, self.info.path)
        except (OSError, ValueError) as err:
            raise CommunicationError(
                f"Could not open KNX USB interface {self.info}: {err}"
            ) from err
        self._device = device
        self._closing.clear()
        self._writer = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="xknx-usb-write"
        )
        self._reader = threading.Thread(
            target=self._read_reports, name="xknx-usb-read", daemon=True
        )
        self._reader.start()

    def _read_reports(self) -> None:
        """Read HID reports until closed. Runs in the reader thread."""
        assert self._loop is not None
        loop = self._loop
        device = self._device
        try:
            while not self._closing.is_set():
                try:
                    data = device.read(HID_REPORT_LENGTH, _READ_TIMEOUT_MS)
                except (OSError, ValueError) as err:
                    if not self._closing.is_set():
                        logger.debug("Reading from %s failed: %s", self.info, err)
                        loop.call_soon_threadsafe(self.connection_lost)
                    return
                if data:
                    report = bytes(data)
                    raw_socket_logger.debug("Received from USB: %s", report.hex())
                    loop.call_soon_threadsafe(self.report_received, report)
        except RuntimeError:
            # the event loop was closed without closing the device first
            logger.debug("Event loop closed - stopped reading from %s", self.info)

    def _write_report(self, report: bytes) -> None:
        """Write one HID report. Runs in the writer thread."""
        written = self._device.write(report)
        if written < 0:
            raise OSError(f"hidapi write returned {written}")

    async def write(self, report: bytes) -> None:
        """Write one HID report. Raise CommunicationError on failure."""
        if self._device is None or self._writer is None or self._loop is None:
            raise CommunicationError("KNX USB interface is not open")
        raw_socket_logger.debug("Sending to USB: %s", report.hex())
        try:
            await self._loop.run_in_executor(self._writer, self._write_report, report)
        except (OSError, ValueError) as err:
            raise CommunicationError(
                f"Writing to KNX USB interface {self.info} failed: {err}"
            ) from err

    async def close(self) -> None:
        """Stop reading and close the device."""
        self._closing.set()
        loop = asyncio.get_running_loop()
        if self._reader is not None:
            await loop.run_in_executor(None, self._reader.join, 1.0)
            self._reader = None
        if self._writer is not None:
            writer, self._writer = self._writer, None
            # a write blocked on a vanished device must not block the event loop
            await loop.run_in_executor(
                None, partial(writer.shutdown, wait=True, cancel_futures=True)
            )
        if self._device is not None:
            device, self._device = self._device, None
            try:
                device.close()
            except (OSError, ValueError) as err:
                logger.debug("Closing %s failed: %s", self.info, err)
