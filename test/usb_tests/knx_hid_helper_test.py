import pytest
import unittest
from typing import Tuple

from xknx.usb.knx_hid_helper import get_packet_type, KNXToTelegram
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
    def test_process(self, data, expected):
        """ """
        converter = KNXToTelegram()
        for frame in data:
            done, _ = converter.process(frame)
        assert expected == done


@pytest.mark.parametrize(
"overall_length, remaining_length, sequence_number, expected",
[
    (20, 20, 1, PacketType.START_AND_END),
    (61-8, 61-8, 1, PacketType.START_AND_END),  # subtract the KNX USB Transfer Protocol Header (only in start packet!)
    (100, 100, 1, PacketType.START_AND_PARTIAL),
    (100, 100-53, 2, PacketType.PARTIAL_AND_END),  # subtract 53 (64 - 3 - 8) for the payload size fo the first frame
    (120, 120, 1, PacketType.START_AND_PARTIAL),
    (120, 120-53, 2, PacketType.PARTIAL),
    (120, 120-53-61, 3, PacketType.PARTIAL_AND_END),
    (240, 240, 1, PacketType.START_AND_PARTIAL),
    (240, 240-53-61, 2, PacketType.PARTIAL),
    (240, 240-53-61-61, 3, PacketType.PARTIAL),
    (240, 240-53-61-61-61, 4, PacketType.PARTIAL_AND_END),
],
)
def test_get_packet_type(overall_length, remaining_length, sequence_number, expected):
    """ """
    assert expected == get_packet_type(overall_length, remaining_length, sequence_number)


class TestKNXToUSBHIDConverter:
    """ """
    @pytest.mark.parametrize(
    "sequence_number,packet_type,expected",
    [
    ],
    )
    def test_initialization(self, sequence_number: SequenceNumber, packet_type: PacketType, expected: Tuple[SequenceNumber, PacketType]):
        assert expected[0] == sequence_number
        assert expected[1] == packet_type
