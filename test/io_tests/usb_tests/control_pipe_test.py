"""Tests for output reports over the control pipe of KNX USB interfaces."""

import logging
import os
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest

from xknx import XKNX
from xknx.exceptions import CommunicationError
from xknx.io.usb import USBTunnel, control_pipe, tunnel as usb_tunnel
from xknx.io.usb.const import EMIID
from xknx.io.usb.hid_device import (
    HIDDevice,
    find_usb_interfaces,
)

from .conftest import FakeHIDModule, make_emi_interface

# a Device Feature Get "supported EMI types" in one HID report
REPORT = bytes.fromhex("011309000800010f01000001").ljust(64, b"\x00")


@pytest.fixture(autouse=True)
def short_timeouts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Don't wait long for answers the fake interface doesn't give."""
    monkeypatch.setattr(usb_tunnel, "DEVICE_FEATURE_GET_TIMEOUT", 0.2)
    monkeypatch.setattr(usb_tunnel, "LOCAL_MANAGEMENT_TIMEOUT", 0.2)


def _tunnel() -> USBTunnel:
    return USBTunnel(XKNX(), cemi_received_callback=Mock(), auto_reconnect=False)


class TestFallback:
    """Test reports go over the control pipe when the interrupt OUT endpoint takes none."""

    async def test_emi1_interface_without_interrupt_out(
        self, fake_hid: FakeHIDModule, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test an EMI1 interface that only takes SET_REPORT (Hager 135E:0025) connects."""
        fake_hid.output_report = True
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI1, 0x0012)
        interface.interrupt_out = False
        tunnel = _tunnel()
        with caplog.at_level(logging.INFO, logger="xknx.log"):
            await tunnel.connect()
        assert tunnel.info is not None
        assert tunnel.info.emi_type is EMIID.EMI1
        # every report went over the control pipe; the interrupt OUT endpoint was
        # tried once only
        assert interface.interrupt_reports == 0
        assert interface.control_pipe_reports == len(interface.written)
        assert (
            sum("sending them over the control pipe" in m for m in caplog.messages) == 1
        )
        await tunnel.disconnect()
        assert fake_hid.closed == 1

    async def test_interrupt_out_kept_while_it_works(
        self, fake_hid: FakeHIDModule
    ) -> None:
        """Test an interface taking reports over its interrupt OUT endpoint keeps it."""
        fake_hid.output_report = True
        tunnel = _tunnel()
        await tunnel.connect()
        interface = fake_hid.interface
        assert interface.control_pipe_reports == 0
        assert interface.interrupt_reports == len(interface.written)
        await tunnel.disconnect()

    async def test_write_raising(self, fake_hid: FakeHIDModule) -> None:
        """Test a write raising OSError is sent over the control pipe too."""
        fake_hid.output_report = True
        device = HIDDevice(
            find_usb_interfaces()[0], report_received=Mock(), connection_lost=Mock()
        )
        await device.open()
        interface = fake_hid.interface

        def failing_write(report: bytes) -> int:
            raise OSError("timed out")

        interface.write = failing_write  # type: ignore[method-assign]
        await device.write(REPORT)
        await device.write(REPORT)
        assert interface.control_pipe_reports == 2
        await device.close()

    async def test_both_pipes_fail(self, fake_hid: FakeHIDModule) -> None:
        """Test the error names both failed writes."""
        fake_hid.output_report = True
        interface = fake_hid.interface
        interface.interrupt_out = False
        interface.control_pipe = False
        device = HIDDevice(
            find_usb_interfaces()[0], report_received=Mock(), connection_lost=Mock()
        )
        await device.open()
        with pytest.raises(
            CommunicationError,
            match="hidapi write returned -1; over the control pipe: "
            "hidapi send_output_report returned -1",
        ):
            await device.write(REPORT)
        # tried again with the next report
        interface.control_pipe = True
        await device.write(REPORT)
        assert interface.control_pipe_reports == 1
        await device.close()

    async def test_without_control_pipe(self, fake_hid: FakeHIDModule) -> None:
        """Test the write error alone where no control pipe can be used."""
        fake_hid.interface.interrupt_out = False
        device = HIDDevice(
            find_usb_interfaces()[0], report_received=Mock(), connection_lost=Mock()
        )
        await device.open()
        with pytest.raises(CommunicationError, match=r"hidapi write returned -1$"):
            await device.write(REPORT)
        await device.close()

    async def test_control_pipe_closed(
        self, fake_hid: FakeHIDModule, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test the control pipe is closed with the device, and a failure only logged."""
        pipe = Mock()
        monkeypatch.setattr(
            "xknx.io.usb.hid_device.open_control_pipe",
            lambda device, backend, path: pipe,
        )
        fake_hid.interface.interrupt_out = False
        device = HIDDevice(
            find_usb_interfaces()[0], report_received=Mock(), connection_lost=Mock()
        )
        await device.open()
        await device.write(REPORT)
        await device.write(REPORT)
        assert pipe.send.call_count == 2
        pipe.close.side_effect = OSError("gone")
        await device.close()
        pipe.close.assert_called_once()

    async def test_control_pipe_closed_when_sending_fails(
        self, fake_hid: FakeHIDModule, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test a control pipe that couldn't send is closed again."""
        pipe = Mock()
        pipe.send.side_effect = OSError("stalled")
        pipe.close.side_effect = OSError("gone")
        monkeypatch.setattr(
            "xknx.io.usb.hid_device.open_control_pipe",
            lambda device, backend, path: pipe,
        )
        fake_hid.interface.interrupt_out = False
        device = HIDDevice(
            find_usb_interfaces()[0], report_received=Mock(), connection_lost=Mock()
        )
        await device.open()
        with pytest.raises(CommunicationError, match="over the control pipe: stalled"):
            await device.write(REPORT)
        pipe.close.assert_called_once()
        await device.close()


class TestOpenControlPipe:
    """Test the control pipe chosen for an interface."""

    def test_hidapi_binding_first(self) -> None:
        """Test hidapi's `send_output_report` is used when the binding has it."""
        device = Mock()
        device.send_output_report.return_value = 64
        pipe = control_pipe.open_control_pipe(device, "hidraw", b"/dev/hidraw3")
        assert pipe is not None
        pipe.send(REPORT)
        device.send_output_report.assert_called_once_with(REPORT)
        pipe.close()

    def test_none_without_driver(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test libusb and macOS have none without the binding's."""
        monkeypatch.setattr(control_pipe, "_on_windows", lambda: False)
        device = Mock(spec=["write"])
        assert control_pipe.open_control_pipe(device, "hid", b"1-2:1.0") is None
        assert control_pipe.open_control_pipe(device, "other", b"p") is None

    def test_hidraw(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test HIDIOCSOUTPUT on a second file descriptor of the hidraw device."""
        opened: list[bytes] = []
        closed: list[int] = []
        calls: list[tuple[int, int, bytes]] = []

        def fake_open(path: bytes, flags: int) -> int:
            opened.append(path)
            return 7

        monkeypatch.setattr(control_pipe.os, "open", fake_open)
        monkeypatch.setattr(control_pipe.os, "close", closed.append)
        monkeypatch.setattr(
            control_pipe,
            "_hidraw_ioctl",
            lambda fd, request, report: calls.append((fd, request, report)),
        )
        pipe = control_pipe.open_control_pipe(
            Mock(spec=["write"]), "hidraw", b"/dev/hidraw3"
        )
        assert pipe is not None
        pipe.send(REPORT)
        pipe.close()
        assert opened == [b"/dev/hidraw3"]
        assert calls == [(7, 0xC040480B, REPORT)]
        assert closed == [7]

    def test_windows(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test HidD_SetOutputReport on a second handle of the HID device."""
        calls: list[tuple[str, object]] = []
        monkeypatch.setattr(control_pipe, "_on_windows", lambda: True)
        monkeypatch.setattr(
            control_pipe,
            "_windows_open",
            lambda path: calls.append(("open", path)) or 42,
        )
        monkeypatch.setattr(
            control_pipe,
            "_windows_set_output_report",
            lambda handle, report: calls.append(("set", (handle, report))),
        )
        monkeypatch.setattr(
            control_pipe,
            "_windows_close",
            lambda handle: calls.append(("close", handle)),
        )
        path = rb"\\?\hid#vid_135e&pid_0025#7&1&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}"
        pipe = control_pipe.open_control_pipe(Mock(spec=["write"]), "hid", path)
        assert pipe is not None
        pipe.send(REPORT)
        pipe.close()
        assert calls == [
            ("open", path.decode()),
            ("set", (42, REPORT)),
            ("close", 42),
        ]

    def test_hidiocsoutput(self) -> None:
        """Test the hidraw ioctl request for 64 octet reports."""
        assert control_pipe.hidiocsoutput(64) == 0xC040480B

    def test_on_windows(self) -> None:
        """Test Windows' HID API is taken on Windows only."""
        assert control_pipe._on_windows() is (sys.platform == "win32")

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows' HID API")
    def test_windows_handle_opened_and_closed(self, tmp_path: Path) -> None:
        """Test a path that exists is opened, shared as hidapi opens it, and closed."""
        path = tmp_path / "device"
        path.write_bytes(b"")
        handle = control_pipe._windows_open(str(path))
        assert handle
        control_pipe._windows_close(handle)

    def test_operating_system_calls_fail_cleanly(self) -> None:
        """Test the operating system calls raise OSError for what can't be opened or sent."""
        with pytest.raises(OSError):
            control_pipe._windows_open(r"\\?\hid#no-such-device")
        with pytest.raises(OSError):
            control_pipe._windows_set_output_report(0, REPORT)
        # a descriptor that is no longer open, as of a device that is gone
        closed = os.open(os.devnull, os.O_RDONLY)
        os.close(closed)
        with pytest.raises(OSError):
            control_pipe._hidraw_ioctl(closed, control_pipe.hidiocsoutput(64), REPORT)
        # nothing to close
        control_pipe._windows_close(0)
