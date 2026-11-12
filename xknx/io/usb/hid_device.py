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
from concurrent.futures import Future, ThreadPoolExecutor
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

# Known KNX USB interfaces by USB vendor and product id, with the manufacturer selling
# them. Unless noted otherwise the entries are the list `KNOWN_DEVICES` of the KNX USB
# proof of concept for xknx by kistlin (https://github.com/kistlin/xknx, branch
# usb-interface-support, xknx/usb/util.py, MIT licence), which names calimero's
# knxUsbVendorProductIds of 2020-06-20 as its source. An interface missing here is
# found by giving its vendor id (and product id) or its path.
KNX_USB_DEVICE_IDS: Final = frozenset(
    {
        (0x0111, 0x1022),  # Makel Elektrik
        (0x0403, 0x6898),  # Tokka
        (0x04CC, 0x0301),  # b+b Automations- und Steuerungstechnik
        (0x0681, 0x0014),  # Siemens HVAC
        (0x0908, 0x02DC),  # Siemens HVAC
        (0x0908, 0x02DD),  # Siemens
        (0x0908, 0x02E6),  # Schrack
        (0x0E77, 0x0102),  # Weinzierl Engineering
        (0x0E77, 0x0103),  # Weinzierl Engineering
        (0x0E77, 0x0104),  # Weinzierl Engineering, GEWISS, Somfy
        (0x0E77, 0x0111),  # Siemens
        (0x0E77, 0x0112),  # Siemens
        (0x0E77, 0x0115),  # CONTROLtronic
        (0x0E77, 0x0121),  # Gustav Hensel
        (0x0E77, 0x0141),  # Schneider Electric (MG)
        (0x0E77, 0x2001),  # Weinzierl Engineering
        (0x0E77, 0x6910),  # Busch-Jaeger Elektro
        (0x135E, 0x0020),  # Insta
        (0x135E, 0x0021),  # Berker
        (0x135E, 0x0022),  # Gira Giersiepen
        (0x135E, 0x0023),  # Albrecht Jung
        (0x135E, 0x0024),  # Merten
        (0x135E, 0x0025),  # Hager Electro
        (0x135E, 0x0026),  # Feller
        (0x135E, 0x0027),  # Panasonic
        (0x135E, 0x0028),  # Glamox
        (0x135E, 0x0122),  # Gira Giersiepen
        (0x135E, 0x0123),  # Albrecht Jung
        (0x135E, 0x0320),  # Insta
        (0x135E, 0x0322),  # Gira Giersiepen
        (0x135E, 0x0323),  # Albrecht Jung
        (0x135E, 0x0326),  # Feller
        (0x135E, 0x0329),  # B.E.G.
        (0x145C, 0x1330),  # Busch-Jaeger Elektro
        (0x145C, 0x1490),  # Busch-Jaeger Elektro
        (0x147B, 0x2200),  # ABB
        (0x147B, 0x5120),  # ABB
        (0x16D0, 0x0490),  # TAPKO Technologies
        (0x16D0, 0x0491),  # MDT technologies
        (0x16D0, 0x0492),  # preussen automation
        # Schneider Electric SpaceLogic KNX USB Interface DIN Rail - tested with xknx
        (0x16DE, 0x008E),
        (0x24D5, 0x0106),  # Satel
        (0x28C2, 0x0002),  # Zennio
        (0x28C2, 0x0003),  # Ekinex
        (0x28C2, 0x0004),  # TAPKO Technologies
        (0x28C2, 0x0005),  # Philips Controls
        (0x28C2, 0x0006),  # HDL
        (0x28C2, 0x0007),  # Niko-Zublin
        (0x28C2, 0x0008),  # TAPKO Technologies
        (0x28C2, 0x000B),  # VIVO
        (0x28C2, 0x000C),  # ESYLUX
        (0x28C2, 0x000D),  # VIVO
        (0x28C2, 0x000E),  # APRICUM
        (0x28C2, 0x000F),  # APRICUM
        (0x28C2, 0x0010),  # Video-Star
        (0x28C2, 0x0011),  # Griesser
        (0x28C2, 0x0012),  # Griesser
        (0x28C2, 0x0013),  # MEAN WELL Enterprises
        (0x28C2, 0x0014),  # Ergo3
        (0x28C2, 0x0015),  # Bes - Ingenium
        (0x28C2, 0x0017),  # Interra
        (0x28C2, 0x001A),  # VIMAR
        (0x2A07, 0x0001),  # ise
        (0x2A07, 0x0002),  # Elsner Elektronik
        (0x2D72, 0x0002),  # PEAKnx
        (0x7660, 0x0002),  # KNX Association
    }
)
# usage pages below this are standard HID devices (keyboards, mice, ...)
_VENDOR_DEFINED_USAGE_PAGE: Final = 0xFF00
# hidapi read timeout in ms - bounds how long closing waits for the reader thread
_READ_TIMEOUT_MS: Final = 100


# hidapi backends, in the order they are tried: on Linux the kernel's hidraw driver
# first - the interface stays with the kernel's HID driver and access is granted by
# the permissions of /dev/hidraw* - then libusb, e.g. for a kernel without hidraw or
# a /dev/hidraw* the user may not open
_BACKENDS: Final = ("hidraw", "hid") if sys.platform.startswith("linux") else ("hid",)
_MISSING_HIDAPI: Final = (
    "KNX USB interfaces need the 'hidapi' package: pip install xknx[usb]"
)


# Serializes the first import of a hidapi backend on macOS (see _import).
_IMPORT_LOCK: Final = threading.Lock()


def _import(name: str) -> Any:
    """
    Import a hidapi backend module. Raise ImportError when it is missing.

    hidapi initializes itself when it is imported (`hid_init()`), and on macOS it
    has to be shut down (`hid_exit()`, at interpreter exit) while the thread that
    initialized it is still running, else the interpreter crashes at exit
    (https://github.com/libusb/hidapi/issues/666). A thread of an executor or of
    `ConnectionConfig(threaded=True)` has ended by then, so on macOS the first
    import runs on a daemon thread that is kept until the interpreter exits; later
    imports, from any thread, find the module imported already.
    """
    if not _on_macos() or name in sys.modules:
        return importlib.import_module(name)
    with _IMPORT_LOCK:
        if name in sys.modules:
            return importlib.import_module(name)
        return _import_on_parked_thread(name)


def _on_macos() -> bool:
    """
    Return whether this runs on macOS.

    A function, so type checkers on other platforms don't take the macOS branch
    for unreachable.
    """
    return sys.platform == "darwin"


def _import_on_parked_thread(name: str) -> Any:
    """Import `name` on a new daemon thread that is kept until the interpreter exits."""
    result: Future[Any] = Future()

    def run() -> None:
        try:
            result.set_result(importlib.import_module(name))
        except BaseException as err:  # pylint: disable=broad-exception-caught
            # handed to the importing thread, which raises it
            result.set_exception(err)
            return
        threading.Event().wait()  # kept: hidapi is shut down with this thread alive

    threading.Thread(target=run, name=f"xknx-{name}-import", daemon=True).start()
    return result.result()


def _backend(name: str) -> Any:
    """Import a hidapi backend module. Raise CommunicationError without hidapi."""
    try:
        return _import(name)
    except ImportError as err:
        raise CommunicationError(_MISSING_HIDAPI) from err


def _backends(names: tuple[str, ...] | None = None) -> list[tuple[str, Any]]:
    """Import the hidapi backends available here (all of them without `names`)."""
    modules: list[tuple[str, Any]] = []
    for name in names or _BACKENDS:
        try:
            modules.append((name, _import(name)))
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
    return (vendor_id, product_id) in KNX_USB_DEVICE_IDS


def _find(
    backends: list[tuple[str, Any]],
    vendor_id: int | None,
    product_id: int | None,
    serial_number: str | None,
    path: bytes | None,
) -> list[USBDeviceInfo]:
    """List the KNX USB interfaces of the first backend that finds any."""
    for backend, hid in backends:
        found: dict[bytes, USBDeviceInfo] = {}
        for device in hid.enumerate(vendor_id or 0, product_id or 0):
            info = USBDeviceInfo.from_hid(device, backend)
            # hidapi reports usage page 0 where the platform doesn't know it (libusb)
            usage_page = device.get("usage_page") or 0
            if 0 < usage_page < _VENDOR_DEFINED_USAGE_PAGE:
                continue
            if path is not None and info.path != path:
                continue
            if (
                vendor_id is None
                and path is None
                and not is_knx_usb_interface(info.vendor_id, info.product_id)
            ):
                continue
            if serial_number and info.serial_number != serial_number:
                continue
            found.setdefault(info.path, info)
        if found:
            return list(found.values())
    return []


def find_usb_interfaces(
    vendor_id: int | None = None,
    product_id: int | None = None,
    serial_number: str | None = None,
    path: bytes | None = None,
) -> list[USBDeviceInfo]:
    """
    List the KNX USB interfaces connected to this host.

    Without `vendor_id` and `path` only known KNX USB interfaces are listed; with
    `vendor_id` every HID device of that vendor (and product) is, and with `path`
    the HID device at that path, so an interface missing from the known ones can be
    used too. The interfaces come from the first hidapi backend that finds any.

    This blocks while the operating system enumerates the USB devices - call it
    through `loop.run_in_executor()` from an event loop.
    """
    return _find(_backends(), vendor_id, product_id, serial_number, path)


def _in_other_backends(info: USBDeviceInfo) -> list[USBDeviceInfo]:
    """Find an interface in the backends tried after its own one."""
    if info.backend not in _BACKENDS:
        return []
    names = _BACKENDS[_BACKENDS.index(info.backend) + 1 :]
    if not names:
        return []
    try:
        backends = _backends(names)
    except CommunicationError:
        return []
    return _find(
        backends, info.vendor_id, info.product_id, info.serial_number or None, None
    )


def _open_device(info: USBDeviceInfo) -> Any:
    """Import the backend of an interface and open it. Blocks."""
    hid = _backend(info.backend)
    device = hid.device()
    try:
        device.open_path(info.path)
    except (OSError, ValueError) as err:
        raise CommunicationError(
            f"Could not open KNX USB interface {info}: {err}"
        ) from err
    return device


class HIDDevice:
    """
    An open KNX USB interface.

    A reader thread passes every incoming HID report to `report_received` in the
    event loop; when reading fails (e.g. the interface was unplugged)
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
        """
        Open the device and start reading. Raise CommunicationError on failure.

        When the interface can't be opened through its backend (e.g. no permission
        for its /dev/hidraw*), the same interface is looked up and opened through
        the next backend (libusb); `info` is then the one opened.
        """
        self._loop = asyncio.get_running_loop()
        try:
            device = await self._loop.run_in_executor(None, _open_device, self.info)
        except CommunicationError as err:
            device = None
            for alternative in await self._loop.run_in_executor(
                None, _in_other_backends, self.info
            ):
                try:
                    device = await self._loop.run_in_executor(
                        None, _open_device, alternative
                    )
                except CommunicationError as alternative_err:
                    logger.debug("%s", alternative_err)
                    continue
                logger.debug(
                    "Opened %s through the %s backend after: %s",
                    alternative,
                    alternative.backend,
                    err,
                )
                self.info = alternative
                break
            if device is None:
                raise
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
                await loop.run_in_executor(None, device.close)
            except (OSError, ValueError) as err:
                logger.debug("Closing %s failed: %s", self.info, err)
