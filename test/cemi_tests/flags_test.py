"""Tests for the cEMI L_Data control fields."""

import pytest

from xknx.cemi import CEMIFlags, CEMIPriority
from xknx.exceptions import ConversionError


@pytest.mark.parametrize(
    "raw,flags",
    [
        (
            # Ctrl1 0xBC: standard frame, do not repeat, broadcast, low priority
            # Ctrl2 0xE0: group address, hop count 6, standard frame format
            bytes((0xBC, 0xE0)),
            CEMIFlags(priority=CEMIPriority.LOW, hop_count=6),
        ),
        (
            # Ctrl1 0x3C: extended frame - not evaluated when parsing
            bytes((0x3C, 0xE0)),
            CEMIFlags(priority=CEMIPriority.LOW, hop_count=6),
        ),
        (
            # Ctrl1 0xB0: system priority; Ctrl2 0x60: individual address
            bytes((0xB0, 0x60)),
            CEMIFlags(priority=CEMIPriority.SYSTEM, hop_count=6),
        ),
        (
            # every optional flag set: repeat on error, system broadcast,
            # acknowledge requested, confirm error, urgent priority, hop count 7
            bytes((0b1000_1011, 0b0111_0000)),
            CEMIFlags(
                priority=CEMIPriority.URGENT,
                repeat_on_error=True,
                system_broadcast=True,
                acknowledge_request=True,
                confirm_error=True,
                hop_count=7,
            ),
        ),
    ],
)
def test_from_knx(raw: bytes, flags: CEMIFlags) -> None:
    """Test parsing of Ctrl1 and Ctrl2."""
    assert CEMIFlags.from_knx(raw) == flags


@pytest.mark.parametrize(
    "priority,ctrl1",
    [
        (CEMIPriority.SYSTEM, 0b1011_0000),
        (CEMIPriority.NORMAL, 0b1011_0100),
        (CEMIPriority.URGENT, 0b1011_1000),
        (CEMIPriority.LOW, 0b1011_1100),
    ],
)
def test_priority_to_knx(priority: CEMIPriority, ctrl1: int) -> None:
    """Test priority encoding - 3/2/2 §2.2.2 Figure 28."""
    raw = CEMIFlags(priority=priority).to_knx(
        frame_type_standard=True, dst_is_group_address=False
    )
    assert raw[0] == ctrl1


def test_to_knx_derived_fields() -> None:
    """Test Frame Type and Address Type are supplied by the frame, not by `flags`."""
    flags = CEMIFlags()
    assert flags.to_knx(frame_type_standard=True, dst_is_group_address=True) == bytes(
        (0xBC, 0xE0)
    )
    assert flags.to_knx(frame_type_standard=False, dst_is_group_address=True) == bytes(
        (0x3C, 0xE0)
    )
    assert flags.to_knx(frame_type_standard=True, dst_is_group_address=False) == bytes(
        (0xBC, 0x60)
    )


def test_round_trip() -> None:
    """Test parsing and serializing yields the same octets."""
    for ctrl1 in (0xBC, 0xB0, 0x9C, 0xBF):
        for ctrl2 in (0xE0, 0x60, 0xF0, 0x00):
            raw = bytes((ctrl1, ctrl2))
            flags = CEMIFlags.from_knx(raw)
            assert (
                flags.to_knx(
                    frame_type_standard=bool(ctrl1 & 0x80),
                    dst_is_group_address=bool(ctrl2 & 0x80),
                )
                == raw
            )


@pytest.mark.parametrize("hop_count", [-1, 8, 255])
def test_invalid_hop_count(hop_count: int) -> None:
    """Test hop count out of range."""
    flags = CEMIFlags(hop_count=hop_count)
    with pytest.raises(ConversionError, match=r".*Hop count out of range.*"):
        flags.to_knx(frame_type_standard=True, dst_is_group_address=True)
