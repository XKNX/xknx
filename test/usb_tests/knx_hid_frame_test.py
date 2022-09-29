from typing import Tuple
import pytest

from xknx.usb.knx_hid_datatypes import PacketType, SequenceNumber
from xknx.usb.knx_hid_frame import PacketInfo


class TestPacketInfoData:
    """ """
    @pytest.mark.parametrize(
    "sequence_number,packet_type,expected",
    [
        (SequenceNumber.FIRST_PACKET, PacketType.START_AND_END, (SequenceNumber.FIRST_PACKET, PacketType.START_AND_END)),
        (SequenceNumber.FIRST_PACKET, PacketType.START_AND_PARTIAL, (SequenceNumber.FIRST_PACKET, PacketType.START_AND_PARTIAL)),
        (SequenceNumber.SECOND_PACKET, PacketType.PARTIAL, (SequenceNumber.SECOND_PACKET, PacketType.PARTIAL)),
        (SequenceNumber.SECOND_PACKET, PacketType.PARTIAL_AND_END, (SequenceNumber.SECOND_PACKET, PacketType.PARTIAL_AND_END)),
        (SequenceNumber.FIFTH_PACKET, PacketType.PARTIAL_AND_END, (SequenceNumber.FIFTH_PACKET, PacketType.PARTIAL_AND_END)),
    ],
    )
    def test_initialization(self, sequence_number: SequenceNumber, packet_type: PacketType, expected: Tuple[SequenceNumber, PacketType]):
        assert expected[0] == sequence_number
        assert expected[1] == packet_type


class TestPacketInfo:
    """ """


class TestKNXHIDReportHeaderData:
    """ """
    @pytest.mark.parametrize(
    "packet_info,data_length,expected",
    [
        ("a", 1, ("a",1)),
        ("b", 1, ("b",1)),
        ("a", 2, ("a",2)),
        ("b", 2, ("b",2)),
    ],
    )
    def test_initialization(self, packet_info, data_length, expected):
        assert expected[0] == packet_info
        assert expected[1] == data_length


class TestKNXHIDReportHeader:
    """ """


class TestKNXHIDReportBodyData:
    """ """


class TestKNXHIDReportBody:
    """ """


class TestKNXHIDFrameData:
    """ """


class TestKNXHIDFrame:
    """ """
