"""
Output reports over the control pipe of a KNX USB interface.

hidapi's `write` sends an output report over the interrupt OUT endpoint of an
interface that has one, else over the control pipe - KNX v01.03.04 - Basic and
System Components - Couplers 09.03 - §3.3.2.3. Some interfaces never take a report
over their interrupt OUT endpoint (the write times out, hidapi returns -1) but take
it as the HID class request SET_REPORT over the control pipe - Device Class
Definition for HID 1.11 - §7.2.2. hidapi sends that one
with `hid_send_output_report`, which hidapi's Python binding doesn't offer (up to
0.15.0): it is used when the binding has it, else the same request is sent through
the HID driver of the operating system, as hidapi does - Windows HidD_SetOutputReport,
Linux hidraw HIDIOCSOUTPUT. Through libusb and on macOS (IOHIDDeviceSetReport, the
same call as hidapi's `write` there) there is none without the binding's.
"""

from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Final, Protocol

# hidraw ioctl HIDIOCSOUTPUT(len): _IOC(_IOC_WRITE | _IOC_READ, 'H', 0x0B, len) -
# Linux include/uapi/linux/hidraw.h (kernel 5.11 and later)
_IOC_READ_WRITE: Final = 3
_IOC_SIZE_SHIFT: Final = 16
_IOC_DIR_SHIFT: Final = 30
_HIDRAW_IOCTL_TYPE: Final = ord("H")
_HIDIOCSOUTPUT_NUMBER: Final = 0x0B


def hidiocsoutput(length: int) -> int:
    """Return the hidraw ioctl request HIDIOCSOUTPUT for a report of `length` octets."""
    return (
        (_IOC_READ_WRITE << _IOC_DIR_SHIFT)
        | (length << _IOC_SIZE_SHIFT)
        | (_HIDRAW_IOCTL_TYPE << 8)
        | _HIDIOCSOUTPUT_NUMBER
    )


class ControlPipe(Protocol):
    """Sends output reports to an open interface over its control pipe."""

    def send(self, report: bytes) -> None:
        """Send one output report (report id first). Raise OSError on failure. Blocks."""

    def close(self) -> None:
        """Release what was opened for it. Blocks."""


class _HidapiControlPipe:
    """`send_output_report` of the hidapi device: SET_REPORT through hidapi itself."""

    __slots__ = ("_send",)

    def __init__(self, send: Any) -> None:
        """Initialize _HidapiControlPipe."""
        self._send = send

    def send(self, report: bytes) -> None:
        """Send one output report."""
        sent: int = self._send(report)
        if sent < 0:
            raise OSError(f"hidapi send_output_report returned {sent}")

    def close(self) -> None:
        """Nothing to release: the hidapi device is closed with the interface."""


class _HidrawControlPipe:
    """A second file descriptor of the interface's /dev/hidraw* for HIDIOCSOUTPUT."""

    __slots__ = ("_fd",)

    def __init__(self, path: bytes) -> None:
        """Open the hidraw device. Raise OSError on failure."""
        self._fd = os.open(path, os.O_RDWR | getattr(os, "O_CLOEXEC", 0))

    def send(self, report: bytes) -> None:
        """Send one output report."""
        _hidraw_ioctl(self._fd, hidiocsoutput(len(report)), report)

    def close(self) -> None:
        """Close the file descriptor."""
        os.close(self._fd)


def _hidraw_ioctl(fd: int, request: int, report: bytes) -> None:
    """Call a hidraw ioctl with a report. Raise OSError on failure."""
    try:
        fcntl = importlib.import_module("fcntl")  # not on Windows
    except ImportError as err:
        raise OSError("hidraw is only available on Linux") from err
    fcntl.ioctl(fd, request, report)


class _WindowsControlPipe:
    """A second handle of the interface for HidD_SetOutputReport."""

    __slots__ = ("_handle",)

    def __init__(self, path: bytes) -> None:
        """Open the HID device. Raise OSError on failure."""
        self._handle = _windows_open(path.decode("utf-8", "surrogateescape"))

    def send(self, report: bytes) -> None:
        """Send one output report."""
        _windows_set_output_report(self._handle, report)

    def close(self) -> None:
        """Close the handle."""
        _windows_close(self._handle)


# CreateFileW
_GENERIC_READ: Final = 0x80000000
_GENERIC_WRITE: Final = 0x40000000
_FILE_SHARE_READ: Final = 0x00000001
_FILE_SHARE_WRITE: Final = 0x00000002
_OPEN_EXISTING: Final = 3

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    def _windows_open(path: str) -> int:
        """Open a HID device by its path, shared like hidapi opens it. Raise OSError on failure."""
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create_file = kernel32.CreateFileW
        create_file.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        create_file.restype = wintypes.HANDLE
        handle: int | None = create_file(
            path,
            _GENERIC_READ | _GENERIC_WRITE,
            _FILE_SHARE_READ | _FILE_SHARE_WRITE,
            None,
            _OPEN_EXISTING,
            0,
            None,
        )
        if handle is None or handle == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def _windows_set_output_report(handle: int, report: bytes) -> None:
        """Send an output report with HidD_SetOutputReport. Raise OSError on failure."""
        hid = ctypes.WinDLL("hid", use_last_error=True)
        set_output_report = hid.HidD_SetOutputReport
        set_output_report.argtypes = (wintypes.HANDLE, ctypes.c_void_p, wintypes.ULONG)
        set_output_report.restype = wintypes.BOOLEAN
        buffer = ctypes.create_string_buffer(report, len(report))
        if not set_output_report(handle, buffer, len(report)):
            raise ctypes.WinError(ctypes.get_last_error())

    def _windows_close(handle: int) -> None:
        """Close a handle."""
        close_handle = ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle
        close_handle.argtypes = (wintypes.HANDLE,)
        close_handle.restype = wintypes.BOOL
        close_handle(handle)

else:

    def _windows_open(path: str) -> int:
        """Raise OSError: Windows' HID API is only available on Windows."""
        raise OSError("HidD_SetOutputReport is only available on Windows")

    def _windows_set_output_report(handle: int, report: bytes) -> None:
        """Raise OSError: Windows' HID API is only available on Windows."""
        raise OSError("HidD_SetOutputReport is only available on Windows")

    def _windows_close(handle: int) -> None:
        """Nothing to close without Windows' HID API."""


def open_control_pipe(device: Any, backend: str, path: bytes) -> ControlPipe | None:
    """
    Open the control pipe of an interface opened through hidapi `backend` at `path`.

    None where output reports can't be sent over it. Raise OSError when it can't be
    opened. Blocks.
    """
    send = getattr(device, "send_output_report", None)
    if send is not None:
        return _HidapiControlPipe(send)
    if backend == "hidraw":
        return _HidrawControlPipe(path)
    if backend == "hid" and _on_windows():
        return _WindowsControlPipe(path)
    return None


def _on_windows() -> bool:
    """
    Return whether this runs on Windows, where hidapi's `hid` backend is Windows' HID API.

    A function, so type checkers on other platforms don't take the Windows branch
    for unreachable.
    """
    return sys.platform == "win32"
