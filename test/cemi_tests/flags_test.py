"""Tests for the cEMI L_Data control fields."""

import pytest

from xknx.cemi import CEMIFlags, CEMIFrameFormat, CEMIFrameType, CEMIPriority
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
            # Ctrl1 0x3C: extended frame - kept, but not evaluated
            bytes((0x3C, 0xE0)),
            CEMIFlags(
                priority=CEMIPriority.LOW,
                hop_count=6,
                frame_type=CEMIFrameType.EXTENDED,
            ),
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
    assert CEMIFlags.from_knx(bytes((0xBC, 0xE0 | eff))).frame_format is frame_format


@pytest.mark.parametrize("eff", [0b0001, 0b0010, 0b0011, 0b1000, 0b1100, 0b1111])
def test_reserved_frame_format(eff: int) -> None:
    """Test parsing of a reserved Extended Frame Format."""
    with pytest.raises(ConversionError, match=r".*Reserved Extended Frame Format.*"):
        CEMIFlags.from_knx(bytes((0xBC, 0xE0 | eff)))


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
        frame_type=CEMIFrameType.STANDARD, dst_is_group_address=False
    )
    assert raw[0] == ctrl1


def test_to_knx_derived_fields() -> None:
    """Test Frame Type and Address Type are supplied by the frame, not by `flags`."""
    flags = CEMIFlags()
    assert flags.to_knx(
        frame_type=CEMIFrameType.STANDARD, dst_is_group_address=True
    ) == bytes((0xBC, 0xE0))
    assert flags.to_knx(
        frame_type=CEMIFrameType.EXTENDED, dst_is_group_address=True
    ) == bytes((0x3C, 0xE0))
    assert flags.to_knx(
        frame_type=CEMIFrameType.STANDARD, dst_is_group_address=False
    ) == bytes((0xBC, 0x60))


def test_to_knx_ignores_received_frame_type() -> None:
    """Test the Frame Type of a received frame is not used when serializing."""
    flags = CEMIFlags.from_knx(bytes((0x3C, 0xE0)))
    assert flags.frame_type is CEMIFrameType.EXTENDED
    assert flags.to_knx(
        frame_type=CEMIFrameType.STANDARD, dst_is_group_address=True
    ) == bytes((0xBC, 0xE0))


def test_round_trip() -> None:
    """Test parsing and serializing yields the same octets."""
    for ctrl1 in (0xBC, 0xB0, 0x9C, 0xBF, 0x3C):
        for ctrl2 in (0xE0, 0x60, 0xF0, 0x00):
            raw = bytes((ctrl1, ctrl2))
            flags = CEMIFlags.from_knx(raw)
            assert (
                flags.to_knx(
                    frame_type=flags.frame_type,
                    dst_is_group_address=bool(ctrl2 & 0x80),
                )
                == raw
            )


@pytest.mark.parametrize("hop_count", [-1, 8, 255])
def test_invalid_hop_count(hop_count: int) -> None:
    """Test hop count out of range."""
    flags = CEMIFlags(hop_count=hop_count)
    with pytest.raises(ConversionError, match=r".*Hop count out of range.*"):
        flags.to_knx(frame_type=CEMIFrameType.STANDARD, dst_is_group_address=True)


def test_str() -> None:
    """Test the compact string representation only lists flags that are set."""
    assert str(CEMIFlags()) == "LOW STANDARD hop_count=6"
    assert (
        str(CEMIFlags.from_knx(bytes((0b1000_1011, 0b0111_0000))))
        == "URGENT STANDARD hop_count=7 repeat_on_error system_broadcast "
        "acknowledge_request confirm_error"
    )
