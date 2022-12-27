import pytest
import unittest
from typing import Tuple

from xknx.usb.knx_hid_helper import get_packet_type, KNXToTelegram, KNXToUSBHIDConverter
from xknx.usb.knx_hid_datatypes import PacketType, SequenceNumber


class TestKNXToTelegram:
    """ """
    @pytest.mark.parametrize(
    "data, expected",
    [
        # structure is the following
        # KNX HID Report Header (3 octets)
        # + KNX USB Transfer Protocol Header (8 octets)
        # + KNX USB Transfer Protocol Body (1 octet EMI code + payload)
        (
            # test invalid frame
            # 3.4.1.2.1 Report ID
            # the Report ID value shall have the fixed value 01h
            [
                b"\x00\x13\x0b"
                + b"\x00\x08\x00\x04\x01\x03\x00\x00"
                + b"\x29\x01\x02\x03"
                + 49 * b"\x00"
            ], False),
        (
            # test start
            [
                b"\x01\x13\x0b"
                + b"\x00\x08\x00\x04\x01\x03\x00\x00"
                + b"\x29\x01\x02\x03"
                + 49 * b"\x00"
            ], True),
        (
            # test start and partial, partial and end
            [
                b"\x01\x15\x0b"
                + b"\x00\x08\x00\x04\x01\x03\x00\x00"
                + b"\x29\x01\x02\x03"
                + 49 * b"\x00",
                b"\x01\x26\x02"
                + b"\x01\x02"
                + 59 * b"\x00"
            ], True),
        ([
            # test start and partial, partial, partial and end
            b"\x01\x15\x0b"
            + b"\x00\x08\x00\x04\x01\x03\x00\x00"
            + b"\x29\x01\x02\x03"
            + 49 * b"\x00",
            b"\x01\x24\x3d"
            + 61 * b"\x01",
            b"\x01\x36\x02"
            + b"\x02"
            + 60 * b"\x00"
        ], True),
    ],
    )
    def test_process(self, data: bytes, expected: bool):
        """ """
        converter = KNXToTelegram()
        for frame in data:
            done, _ = converter.process(frame)
        assert expected == done


@pytest.mark.parametrize(
"overall_length, remaining_length, sequence_number, expected",
[
    (20, 20, 1, PacketType.START_AND_END),
    (61-8-1, 61-8-1, 1, PacketType.START_AND_END),  # subtract the KNX USB Transfer Protocol Header (only in start packet!)
    (100, 100, 1, PacketType.START_AND_PARTIAL),
    (100, 100-53, 2, PacketType.PARTIAL_AND_END),  # subtract 52 (64 - 3 - 8 - 1) for the payload size fo the first frame
    (120, 120, 1, PacketType.START_AND_PARTIAL),
    (120, 120-53, 2, PacketType.PARTIAL),
    (120, 120-53-61, 3, PacketType.PARTIAL_AND_END),
    (240, 240, 1, PacketType.START_AND_PARTIAL),
    (240, 240-53-61, 2, PacketType.PARTIAL),
    (240, 240-53-61-61, 3, PacketType.PARTIAL),
    (240, 240-53-61-61-61, 4, PacketType.PARTIAL_AND_END),
],
)
def test_get_packet_type(overall_length: int, remaining_length: int, sequence_number: int, expected: PacketType):
    """ """
    assert expected == get_packet_type(overall_length, remaining_length, sequence_number)


class TestKNXToUSBHIDConverter:
    """ """
    @pytest.mark.parametrize(
    "data, frame_count, valid_frame",
    [
        # structure is the following
        # KNX HID Report Header (3 octets)
        # + KNX USB Transfer Protocol Header (8 octets)
        # + KNX USB Transfer Protocol Body (1 octet EMI code + payload)
        (
            # test invalid frame
            b"\x03\x01\x02\x03"
            , 1, True),
        (
            # test start
            # emi code + data (52 octet)
            b"\x03" + b"\x01\x02\x03" + 48 * b"\x00" + b"\x0f"
            , 1, True),
        (
            # test start and partial, partial and end
            b"\x03" + b"\x01\x02\x03" + 48 * b"\x00" + b"\x01"
            + b"\x0f"
            , 2, True),
        (
            # test start and partial, partial, partial and end
            b"\x03" + b"\x01\x02\x03" + 48 * b"\x00" + b"\x01"
            + b"\x0f" + 59 * b"\x01" + b"\x02"
            + b"\x0f"
            , 3, True),
    ],
    )
    def test_initialization(self, data: bytes, frame_count: int, valid_frame: bool):
        """ """
        frames = KNXToUSBHIDConverter.split_into_hid_frames(data)
        assert frame_count == len(frames)
        for index, frame in enumerate(frames):
            knx_raw = frame.to_knx()
            if frame.report_header.packet_info.sequence_number == SequenceNumber.FIRST_PACKET:
                assert frame.report_body.transfer_protocol_body.data.startswith(data[:53])
            else:
                current_data = data[53+((index-1)*61):53+(index*61)]
                assert frame.report_body.transfer_protocol_body.data.startswith(current_data)
            assert valid_frame == frame.is_valid
            # 3.4.1.2.2 Sequence number
            # Unused bytes in the last HID report frame shall be filled with 00h.
            assert len(knx_raw) == 64
