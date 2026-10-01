"""Tests for run_state — KNX v01.10.01 - Resources 03.05.01 - §4.24.2, KNX v02.01.02 - Management Procedures 03.05.02 - §3.34.3."""

import pytest

from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device import run_state
from xknx.management.procedures.device.run_state import RunState


def test_no_operation() -> None:
    """Test no_operation() encodes 00h + 9 reserved octets."""
    assert run_state.no_operation() == bytes(10)


def test_restart() -> None:
    """Test restart() encodes 01h + 9 reserved octets."""
    assert run_state.restart() == bytes([0x01]) + bytes(9)


def test_stop() -> None:
    """Test stop() encodes 02h + 9 reserved octets."""
    assert run_state.stop() == bytes([0x02]) + bytes(9)


def test_decode_run_state_success() -> None:
    """Test decode_run_state() maps a known octet to its RunState member."""
    assert run_state.decode_run_state(bytes([2]), "object 1") == RunState.READY


def test_decode_run_state_wrong_length() -> None:
    """Test decode_run_state() raises for data that isn't exactly 1 octet."""
    with pytest.raises(
        ManagementConnectionError,
        match=r"object 1 Run State Machine returned 0 octets, expected 1",
    ):
        run_state.decode_run_state(b"", "object 1")


def test_decode_run_state_unknown_value() -> None:
    """Test decode_run_state() raises for an undefined state value."""
    with pytest.raises(
        ManagementConnectionError,
        match=r"object 1 Run State Machine reported unknown state 0xff",
    ):
        run_state.decode_run_state(bytes([0xFF]), "object 1")


def test_pad_rejects_oversized_event() -> None:
    """Test _pad() raises ValueError for a payload longer than the 10 octet width."""
    with pytest.raises(ValueError, match=r"run event too long: 11 > 10"):
        run_state._pad(bytes(11))
