"""Tests for the cEMI L_Data control fields."""

import pytest

from xknx.cemi import (
    CEMIAddressType,
    CEMIFlags,
    CEMIFrameFormat,
    CEMIFrameType,
    CEMIPriority,
)
from xknx.exceptions import ConversionError


def control_field(ctrl1: int, ctrl2: int) -> int:
    """Return Ctrl1 and Ctrl2 as one 16 bit control field."""
    return ctrl1 << 8 | ctrl2


@pytest.mark.parametrize(
    "ctrl1,ctrl2,flags",
    [
        (
            # Ctrl1 0xBC: standard frame, do not repeat, broadcast, low priority
            # Ctrl2 0xE0: group address, hop count 6, standard frame format
            0xBC,
            0xE0,
            CEMIFlags(priority=CEMIPriority.LOW, hop_count=6),
        ),
        (
            # Ctrl1 0x3C: extended frame - kept, but not evaluated
            0x3C,
            0xE0,
            CEMIFlags(
                priority=CEMIPriority.LOW,
                hop_count=6,
                frame_type=CEMIFrameType.EXTENDED,
            ),
        ),
        (
            # Ctrl1 0xB0: system priority; Ctrl2 0x60: individual address
            0xB0,
            0x60,
            CEMIFlags(priority=CEMIPriority.SYSTEM, hop_count=6),
        ),
        (
            # every optional flag set: repeat on error, system broadcast,
            # acknowledge requested, confirm error, urgent priority, hop count 7
            0b1000_1011,
            0b0111_0000,
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
def test_from_knx(ctrl1: int, ctrl2: int, flags: CEMIFlags) -> None:
    """Test parsing of the control field."""
    assert CEMIFlags.from_knx(control_field(ctrl1, ctrl2)) == flags


@pytest.mark.parametrize(
    "eff,frame_format",
    [
        (0b0000, CEMIFrameFormat.STANDARD),
        # the whole 01xxb range is LTE-HEE; the 2 lsb are the LTE address type
        (0b0100, CEMIFrameFormat.LTE_HEE),
        (0b0101, CEMIFrameFormat.LTE_HEE),
        (0b0110, CEMIFrameFormat.LTE_HEE),
        (0b0111, CEMIFrameFormat.LTE_HEE),
    ],
)
def test_frame_format_from_knx(eff: int, frame_format: CEMIFrameFormat) -> None:
    """Test parsing of the Extended Frame Format field."""
    flags = CEMIFlags.from_knx(control_field(0xBC, 0xE0 | eff))
    assert flags.frame_format is frame_format


@pytest.mark.parametrize("eff", [0b0001, 0b0010, 0b0011, 0b1000, 0b1100, 0b1111])
def test_reserved_frame_format(eff: int) -> None:
    """Test parsing of a reserved Extended Frame Format."""
    with pytest.raises(ConversionError, match=r".*Reserved Extended Frame Format.*"):
        CEMIFlags.from_knx(control_field(0xBC, 0xE0 | eff))


@pytest.mark.parametrize(
    "priority,ctrl1",
    [
        (CEMIPriority.SYSTEM, 0b0011_0000),
        (CEMIPriority.NORMAL, 0b0011_0100),
        (CEMIPriority.URGENT, 0b0011_1000),
        (CEMIPriority.LOW, 0b0011_1100),
    ],
)
def test_priority_to_knx(priority: CEMIPriority, ctrl1: int) -> None:
    """Test priority encoding - 3/2/2 §2.2.2 Figure 28."""
    # the Frame Type bit is not set by `CEMIFlags.to_knx()`
    assert CEMIFlags(priority=priority).to_knx() >> 8 == ctrl1


def test_to_knx_leaves_derived_bits_clear() -> None:
    """Test Frame Type and Address Type are not set by `CEMIFlags.to_knx()`."""
    raw = CEMIFlags().to_knx()
    assert raw == control_field(0b0011_1100, 0b0110_0000)
    assert CEMIFrameType.from_knx(raw) is CEMIFrameType.EXTENDED  # ie. bit not set
    assert CEMIAddressType.from_knx(raw) is CEMIAddressType.INDIVIDUAL


@pytest.mark.parametrize(
    "frame_type,address_type,expected",
    [
        (CEMIFrameType.STANDARD, CEMIAddressType.GROUP, (0xBC, 0xE0)),
        (CEMIFrameType.EXTENDED, CEMIAddressType.GROUP, (0x3C, 0xE0)),
        (CEMIFrameType.STANDARD, CEMIAddressType.INDIVIDUAL, (0xBC, 0x60)),
        (CEMIFrameType.EXTENDED, CEMIAddressType.INDIVIDUAL, (0x3C, 0x60)),
    ],
)
def test_composition(
    frame_type: CEMIFrameType,
    address_type: CEMIAddressType,
    expected: tuple[int, int],
) -> None:
    """Test the frame ORs the derived bits into the flags."""
    raw = CEMIFlags().to_knx() | frame_type.to_knx() | address_type.to_knx()
    assert raw == control_field(*expected)


def test_to_knx_serializes_frame_format() -> None:
    """Test the Extended Frame Format is serialized as held, not as a constant."""
    # Data Secure protects the Extended Frame Format - `block_0()` reads the same
    # field, so the value on the wire and the one fed to the MAC can not diverge.
    flags = CEMIFlags(frame_format=CEMIFrameFormat.LTE_HEE)
    assert flags.to_knx() & 0b1111 == CEMIFrameFormat.LTE_HEE
    assert CEMIFlags().to_knx() & 0b1111 == CEMIFrameFormat.STANDARD


def test_to_knx_ignores_received_frame_type() -> None:
    """Test the Frame Type of a received frame is not used when serializing."""
    flags = CEMIFlags.from_knx(control_field(0x3C, 0xE0))
    assert flags.frame_type is CEMIFrameType.EXTENDED
    raw = (
        flags.to_knx()
        | CEMIFrameType.STANDARD.to_knx()
        | CEMIAddressType.GROUP.to_knx()
    )
    assert raw == control_field(0xBC, 0xE0)


def test_round_trip() -> None:
    """Test parsing and serializing yields the same control field."""
    for ctrl1 in (0xBC, 0xB0, 0x9C, 0xBF, 0x3C):
        for ctrl2 in (0xE0, 0x60, 0xF0, 0x00):
            raw = control_field(ctrl1, ctrl2)
            flags = CEMIFlags.from_knx(raw)
            assert (
                flags.to_knx()
                | flags.frame_type.to_knx()
                | CEMIAddressType.from_knx(raw).to_knx()
            ) == raw


@pytest.mark.parametrize("hop_count", [-1, 8, 255])
def test_invalid_hop_count(hop_count: int) -> None:
    """Test hop count out of range."""
    with pytest.raises(ConversionError, match=r".*Hop count out of range.*"):
        CEMIFlags(hop_count=hop_count).to_knx()


def test_str() -> None:
    """Test the compact string representation only lists flags that are set."""
    assert str(CEMIFlags()) == "LOW STANDARD hop_count=6"
    assert (
        str(CEMIFlags.from_knx(control_field(0b1000_1011, 0b0111_0000)))
        == "URGENT STANDARD hop_count=7 repeat_on_error system_broadcast "
        "acknowledge_request confirm_error"
    )
