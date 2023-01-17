from typing import Tuple
from unittest.mock import Mock

import pytest

from xknx.usb.knx_hid_datatypes import PacketType, SequenceNumber
from xknx.usb.knx_hid_frame import (
    KNXHIDReportHeader,
    KNXHIDReportHeaderData,
    PacketInfo,
    PacketInfoData,
)


class TestPacketInfoData:
    """ """

    @pytest.mark.parametrize(
        "sequence_number,packet_type,expected",
        [
            (
                SequenceNumber.FIRST_PACKET,
                PacketType.START_AND_END,
                (SequenceNumber.FIRST_PACKET, PacketType.START_AND_END),
            ),
            (
                SequenceNumber.FIRST_PACKET,
                PacketType.START_AND_PARTIAL,
                (SequenceNumber.FIRST_PACKET, PacketType.START_AND_PARTIAL),
            ),
            (
                SequenceNumber.SECOND_PACKET,
                PacketType.PARTIAL,
                (SequenceNumber.SECOND_PACKET, PacketType.PARTIAL),
            ),
            (
                SequenceNumber.SECOND_PACKET,
                PacketType.PARTIAL_AND_END,
                (SequenceNumber.SECOND_PACKET, PacketType.PARTIAL_AND_END),
            ),
            (
                SequenceNumber.FIFTH_PACKET,
                PacketType.PARTIAL_AND_END,
                (SequenceNumber.FIFTH_PACKET, PacketType.PARTIAL_AND_END),
            ),
        ],
    )
    def test_initialization(
        self,
        sequence_number: SequenceNumber,
        packet_type: PacketType,
        expected: tuple[SequenceNumber, PacketType],
    ):
        """ """
        packet_info_data = PacketInfoData(sequence_number, packet_type)
        assert expected[0] == packet_info_data.sequence_number
        assert expected[1] == packet_info_data.packet_type


class TestPacketInfo:
    """ """

    @pytest.mark.parametrize(
        "sequence_number,packet_type",
        [
            (SequenceNumber.FIRST_PACKET, PacketType.START_AND_PARTIAL),
            (SequenceNumber.SECOND_PACKET, PacketType.START_AND_PARTIAL),
            (SequenceNumber.THIRD_PACKET, PacketType.START_AND_PARTIAL),
            (SequenceNumber.FOURTH_PACKET, PacketType.START_AND_PARTIAL),
            (SequenceNumber.FIFTH_PACKET, PacketType.START_AND_PARTIAL),
            (SequenceNumber.FIFTH_PACKET, PacketType.START_AND_END),
            (SequenceNumber.FOURTH_PACKET, PacketType.PARTIAL),
            (SequenceNumber.FIFTH_PACKET, PacketType.PARTIAL_AND_END),
        ],
    )
    def test_from_data(self, sequence_number, packet_type):
        """ """
        mock = Mock()
        mock.sequence_number = sequence_number
        mock.packet_type = packet_type
        packet_info = PacketInfo.from_data(mock)
        assert sequence_number == packet_info.sequence_number
        assert packet_type == packet_info.packet_type

    @pytest.mark.parametrize(
        "data,expected",
        [
            (b"\x13", (SequenceNumber.FIRST_PACKET, PacketType.START_AND_END)),
            (b"\x23", (SequenceNumber.SECOND_PACKET, PacketType.START_AND_END)),
            (b"\x33", (SequenceNumber.THIRD_PACKET, PacketType.START_AND_END)),
            (b"\x43", (SequenceNumber.FOURTH_PACKET, PacketType.START_AND_END)),
            (b"\x53", (SequenceNumber.FIFTH_PACKET, PacketType.START_AND_END)),
            (b"\x35", (SequenceNumber.THIRD_PACKET, PacketType.START_AND_PARTIAL)),
            (b"\x34", (SequenceNumber.THIRD_PACKET, PacketType.PARTIAL)),
            (b"\x36", (SequenceNumber.THIRD_PACKET, PacketType.PARTIAL_AND_END)),
        ],
    )
    def test_from_knx(self, data, expected):
        """ """
        packet_info = PacketInfo.from_knx(data)
        assert expected[0] == packet_info.sequence_number
        assert expected[1] == packet_info.packet_type

    @pytest.mark.parametrize(
        "data",
        [
            (b"\x13"),
            (b"\x23"),
            (b"\x33"),
            (b"\x43"),
            (b"\x53"),
            (b"\x23"),
            (b"\x24"),
            (b"\x25"),
            (b"\x26"),
        ],
    )
    def test_to_knx(self, data):
        """ """
        packet_info = PacketInfo.from_knx(data)
        packet_info_output = packet_info.to_knx()
        assert packet_info_output == data


class TestKNXHIDReportHeaderData:
    """ """

    @pytest.mark.parametrize(
        "packet_info,data_length",
        [
            (1, 2),
            (2, 1),
        ],
    )
    def test_initialization(self, packet_info, data_length):
        """ """
        knx_hid_report_header_data = KNXHIDReportHeaderData(packet_info, data_length)
        assert knx_hid_report_header_data.packet_info == packet_info
        assert knx_hid_report_header_data.data_length == data_length


class TestKNXHIDReportHeader:
    """ """

    def test_initialization(self):
        """ """
        knx_hid_report_header = KNXHIDReportHeader()
        assert knx_hid_report_header.report_id == 0x01
        assert knx_hid_report_header.data_length == 0
        assert not knx_hid_report_header.is_valid

    @pytest.mark.parametrize(
        "packet_info,data_length,is_valid",
        [
            (1, 2, True),
            (2, 1, True),
        ],
    )
    def test_from_data(self, packet_info, data_length, is_valid):
        """ """
        mock = Mock()
        mock.packet_info = packet_info
        mock.data_length = data_length
        knx_hid_report_header = KNXHIDReportHeader.from_data(mock)
        assert knx_hid_report_header.report_id == 0x01
        assert knx_hid_report_header.packet_info == packet_info
        assert knx_hid_report_header.data_length == data_length
        assert knx_hid_report_header.is_valid == is_valid

    @pytest.mark.parametrize(
        "data,sequence_number,packet_type,data_length,is_valid",
        [
            (
                b"\x01\x13\x10",
                SequenceNumber.FIRST_PACKET,
                PacketType.START_AND_END,
                16,
                True,
            ),
            (
                b"\x00\x13\x10",
                SequenceNumber.FIRST_PACKET,
                PacketType.START_AND_END,
                16,
                False,
            ),
            (
                b"\x01\x23\x10",
                SequenceNumber.SECOND_PACKET,
                PacketType.START_AND_END,
                16,
                True,
            ),
            (
                b"\x01\x16\x20",
                SequenceNumber.FIRST_PACKET,
                PacketType.PARTIAL_AND_END,
                32,
                True,
            ),
            (
                b"\x01\x16\x3e",
                SequenceNumber.FIRST_PACKET,
                PacketType.PARTIAL_AND_END,
                62,
                False,
            ),
        ],
    )
    def test_from_knx(self, data, sequence_number, packet_type, data_length, is_valid):
        """3.4.1.1 HID report frame structure"""
        knx_hid_report_header = KNXHIDReportHeader.from_knx(data)
        assert knx_hid_report_header.report_id == data[0]
        assert knx_hid_report_header.packet_info.sequence_number == sequence_number
        assert knx_hid_report_header.packet_info.packet_type == packet_type
        assert knx_hid_report_header.data_length == data_length
        assert knx_hid_report_header.is_valid == is_valid

    @pytest.mark.parametrize(
        "data",
        [
            (b"\x01\x13\x10"),
            (b"\x01\x23\x10"),
            (b"\x01\x16\x20"),
        ],
    )
    def test_to_knx(self, data):
        """ """
        knx_hid_report_header = KNXHIDReportHeader.from_knx(data)
        knx_hid_report_header_knx = knx_hid_report_header.to_knx()
        assert knx_hid_report_header_knx == data
        assert knx_hid_report_header.is_valid

    @pytest.mark.parametrize(
        "data",
        [
            (b"\x00\x13\x10"),
            (b"\x01\x16\x3e"),
        ],
    )
    def test_to_knx_invalid(self, data):
        """ """
        knx_hid_report_header = KNXHIDReportHeader.from_knx(data)
        knx_hid_report_header_knx = knx_hid_report_header.to_knx()
        assert knx_hid_report_header_knx != data
        assert not knx_hid_report_header.is_valid


class TestKNXHIDReportBodyData:
    """ """


class TestKNXHIDReportBody:
    """ """


class TestKNXHIDFrameData:
    """ """


class TestKNXHIDFrame:
    """ """
