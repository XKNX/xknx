"""Tests for decoding TP1 frames of a cEMI L_Busmon.ind."""

import pytest

from xknx.cemi import (
    CEMIAddressType,
    CEMIFrameType,
    CEMILData,
    CEMIPriority,
    TP1Acknowledgement,
    TP1DataFrame,
    parse_tp1_frame,
)
from xknx.cemi.tp1_frame import calculate_checksum
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseCEMI, UnsupportedCEMIMessage
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDirection,
)
from xknx.telegram.apci import GroupValueWrite
from xknx.telegram.tpci import TConnect, TDataGroup

# GroupValueWrite 1 from 1.1.10 to 1/2/12 - low priority, not repeated, hop count 6
STANDARD_FRAME = bytes.fromhex("bc110a0a0ce100813e")


def test_checksum() -> None:
    """Test the check octet is a NOT XOR over all preceding octets."""
    assert calculate_checksum(b"") == 0xFF
    assert calculate_checksum(bytes.fromhex("bc110a0a0ce10081")) == 0x3E
    assert calculate_checksum(STANDARD_FRAME) == 0x00


def test_standard_frame() -> None:
    """Test parsing an L_Data_Standard frame."""
    frame = parse_tp1_frame(STANDARD_FRAME)
    assert isinstance(frame, TP1DataFrame)
    assert frame.frame_type is CEMIFrameType.STANDARD
    assert frame.src_addr == IndividualAddress("1.1.10")
    assert frame.dst_addr == GroupAddress("1/2/12")
    assert frame.address_type is CEMIAddressType.GROUP
    assert frame.priority is CEMIPriority.LOW
    assert frame.repeated is False
    assert frame.hop_count == 6
    assert frame.tpdu == bytes.fromhex("0081")
    assert frame.checksum == 0x3E
    assert frame.checksum_valid
    assert frame.to_knx() == STANDARD_FRAME
    assert frame == TP1DataFrame(
        src_addr=IndividualAddress("1.1.10"),
        dst_addr=GroupAddress("1/2/12"),
        tpdu=bytes.fromhex("0081"),
    )

    assert frame.telegram() == Telegram(
        destination_address=GroupAddress("1/2/12"),
        direction=TelegramDirection.INCOMING,
        payload=GroupValueWrite(DPTBinary(1)),
        source_address=IndividualAddress("1.1.10"),
        tpci=TDataGroup(),
    )
    cemi_l_data = frame.cemi_l_data()
    assert cemi_l_data.flags.priority is CEMIPriority.LOW
    assert cemi_l_data.flags.hop_count == 6
    assert cemi_l_data.flags.frame_type is CEMIFrameType.STANDARD


def test_repeated_frame() -> None:
    """Test the repeat flag - 0 for a repeated frame."""
    raw = bytes.fromhex("9c110a0a0ce10081")
    raw += bytes((calculate_checksum(raw),))
    frame = parse_tp1_frame(raw)
    assert isinstance(frame, TP1DataFrame)
    assert frame.repeated is True
    assert frame.checksum_valid
    assert frame.to_knx() == raw
    # repeated frames are indicated as repeated in cEMI too
    assert frame.cemi_l_data().flags.repeat_on_error is True


def test_individual_control_frame() -> None:
    """Test parsing an individually addressed T_Connect frame with system priority."""
    raw = bytes.fromhex("b0110a11056080")
    raw += bytes((calculate_checksum(raw),))
    frame = parse_tp1_frame(raw)
    assert isinstance(frame, TP1DataFrame)
    assert frame.priority is CEMIPriority.SYSTEM
    assert frame.dst_addr == IndividualAddress("1.1.5")
    assert frame.address_type is CEMIAddressType.INDIVIDUAL
    assert frame.tpdu == b"\x80"
    assert frame.checksum_valid
    assert frame.to_knx() == raw
    telegram = frame.telegram()
    assert telegram.tpci == TConnect()
    assert telegram.payload is None
    assert telegram.destination_address == IndividualAddress("1.1.5")


@pytest.mark.parametrize(
    ("priority", "ctrl"),
    [
        (CEMIPriority.SYSTEM, 0xB0),
        (CEMIPriority.NORMAL, 0xB4),
        (CEMIPriority.URGENT, 0xB8),
        (CEMIPriority.LOW, 0xBC),
    ],
)
def test_priority(priority: CEMIPriority, ctrl: int) -> None:
    """Test the priority bits of the Control field."""
    frame = TP1DataFrame(
        src_addr=IndividualAddress("1.1.10"),
        dst_addr=GroupAddress("1/2/12"),
        tpdu=bytes.fromhex("0081"),
        priority=priority,
    )
    raw = frame.to_knx()
    assert raw[0] == ctrl
    assert parse_tp1_frame(raw) == frame


def test_extended_frame() -> None:
    """Test parsing an L_Data_Extended frame."""
    payload = GroupValueWrite(DPTArray(tuple(range(16))))
    raw = bytes.fromhex("3ce0110a0a0c11") + payload.to_knx()
    raw += bytes((calculate_checksum(raw),))
    frame = parse_tp1_frame(raw)
    assert isinstance(frame, TP1DataFrame)
    assert frame.frame_type is CEMIFrameType.EXTENDED
    assert frame.src_addr == IndividualAddress("1.1.10")
    assert frame.dst_addr == GroupAddress("1/2/12")
    assert frame.priority is CEMIPriority.LOW
    assert frame.repeated is False
    assert frame.hop_count == 6
    assert len(frame.tpdu) == 18
    assert frame.checksum_valid
    assert frame.to_knx() == raw

    telegram = frame.telegram()
    assert telegram.payload == payload
    assert frame.cemi_l_data().flags.frame_type is CEMIFrameType.EXTENDED
    # the cEMI frame derives the frame type from the length again
    assert frame.cemi_l_data().to_knx()[6] == 0x11


def test_extended_frame_with_short_tpdu() -> None:
    """Test an L_Data_Extended frame is kept even if a standard frame would fit."""
    frame = TP1DataFrame(
        src_addr=IndividualAddress("1.1.10"),
        dst_addr=IndividualAddress("1.1.5"),
        tpdu=b"\x80",
        priority=CEMIPriority.SYSTEM,
        hop_count=5,
        frame_type=CEMIFrameType.EXTENDED,
    )
    raw = frame.to_knx()
    assert raw[:7] == bytes.fromhex("3050110a110500")
    assert parse_tp1_frame(raw) == frame


def test_bad_checksum() -> None:
    """Test a frame with a wrong check octet is decoded and flagged."""
    raw = STANDARD_FRAME[:-1] + b"\x3f"
    frame = parse_tp1_frame(raw)
    assert isinstance(frame, TP1DataFrame)
    assert frame.checksum == 0x3F
    assert not frame.checksum_valid
    assert frame.to_knx() == raw
    assert frame.telegram().payload == GroupValueWrite(DPTBinary(1))


@pytest.mark.parametrize(
    ("raw", "acknowledgement", "busy"),
    [
        (b"\xcc", TP1Acknowledgement.ACK, False),
        (b"\x0c", TP1Acknowledgement.NAK, False),
        (b"\xc0", TP1Acknowledgement.BUSY, True),
        (b"\x00", TP1Acknowledgement.NAK_BUSY, True),
    ],
)
def test_acknowledgement(
    raw: bytes, acknowledgement: TP1Acknowledgement, busy: bool
) -> None:
    """Test parsing short acknowledgement frames."""
    frame = parse_tp1_frame(raw)
    assert frame is acknowledgement
    assert isinstance(frame, TP1Acknowledgement)
    assert frame.busy is busy
    assert frame.to_knx() == raw


def test_acknowledgement_invalid() -> None:
    """Test invalid acknowledgement frames."""
    with pytest.raises(UnsupportedCEMIMessage, match=r"Unknown TP1 acknowledgement"):
        parse_tp1_frame(b"\x4c")
    with pytest.raises(CouldNotParseCEMI, match=r"Invalid TP1 acknowledgement"):
        TP1Acknowledgement.from_knx(b"\xcc\xcc")


@pytest.mark.parametrize(
    ("raw", "exception", "err_msg"),
    [
        (b"", CouldNotParseCEMI, r"Empty TP1 frame"),
        (bytes.fromhex("bc110a0a0c"), CouldNotParseCEMI, r"TP1 frame too small"),
        # length 2 but only 1 octet after the TPCI octet
        (
            bytes.fromhex("bc110a0a0ce2008100"),
            CouldNotParseCEMI,
            r"TP1 frame length should be 10 but is 9",
        ),
        # trailing octet
        (
            STANDARD_FRAME + b"\xcc",
            CouldNotParseCEMI,
            r"TP1 frame length should be 9 but is 10",
        ),
        (
            bytes.fromhex("f0110a0001010000"),
            UnsupportedCEMIMessage,
            r"L_Poll_Data frame not supported",
        ),
        # reserved bit 6 set
        (
            bytes.fromhex("fc110a0a0ce1008100"),
            UnsupportedCEMIMessage,
            r"No TP1 L_Data frame",
        ),
        # LTE-HEE Extended Frame Format
        (
            bytes.fromhex("3ce4110a0a0c01008100"),
            UnsupportedCEMIMessage,
            r"Extended Frame Format not supported: 0b0100",
        ),
        # length escape code
        (
            bytes.fromhex("3ce0110a0a0cff008100"),
            UnsupportedCEMIMessage,
            r"length escape code not supported",
        ),
    ],
)
def test_invalid_frame(raw: bytes, exception: type[Exception], err_msg: str) -> None:
    """Test invalid or unsupported frames."""
    with pytest.raises(exception, match=err_msg):
        parse_tp1_frame(raw)


def test_unsupported_tpdu() -> None:
    """Test the header of a frame with an unsupported APDU is decoded."""
    # reserved APCI between A_FilterTable_Write and A_RouterMemory_Read
    raw = bytes.fromhex("b0110a11056103c4")
    raw += bytes((calculate_checksum(raw),))
    frame = parse_tp1_frame(raw)
    assert isinstance(frame, TP1DataFrame)
    assert frame.src_addr == IndividualAddress("1.1.10")
    assert frame.dst_addr == IndividualAddress("1.1.5")
    assert frame.to_knx() == raw
    with pytest.raises(UnsupportedCEMIMessage, match=r"APDU not supported"):
        frame.telegram()


def test_serialize_invalid() -> None:
    """Test serializing invalid fields."""
    kwargs = {
        "src_addr": IndividualAddress("1.1.10"),
        "dst_addr": GroupAddress("1/2/12"),
    }
    with pytest.raises(ConversionError, match=r"requires a TPCI octet"):
        TP1DataFrame(**kwargs, tpdu=b"")  # type: ignore[arg-type]
    with pytest.raises(ConversionError, match=r"Hop count out of range"):
        TP1DataFrame(**kwargs, tpdu=b"\x00\x80", hop_count=8)  # type: ignore[arg-type]
    with pytest.raises(ConversionError, match=r"too long for an L_Data_Standard"):
        TP1DataFrame(**kwargs, tpdu=bytes(17))  # type: ignore[arg-type]
    with pytest.raises(ConversionError, match=r"too long for an L_Data_Extended"):
        TP1DataFrame(
            **kwargs,  # type: ignore[arg-type]
            tpdu=bytes(256),
            frame_type=CEMIFrameType.EXTENDED,
        )


def test_cemi_l_data_matches_cemi_frame() -> None:
    """Test the frame is parsed like the same frame received as L_Data.ind."""
    frame = parse_tp1_frame(STANDARD_FRAME)
    assert isinstance(frame, TP1DataFrame)
    # Ctrl1 equals the TP1 Control field, Ctrl2 holds AT and hop count
    assert frame.cemi_l_data() == CEMILData.from_knx(
        bytes.fromhex("bce0110a0a0c010081")
    )


def test_repr() -> None:
    """Test string representation."""
    frame = parse_tp1_frame(STANDARD_FRAME)
    assert repr(frame) == (
        'TP1DataFrame(src_addr="1.1.10" dst_addr="1/2/12" priority=LOW '
        'frame_type=STANDARD repeated=False hop_count=6 tpdu="0081" '
        "checksum_valid=True)"
    )
