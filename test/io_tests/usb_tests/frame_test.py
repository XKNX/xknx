"""Tests for KNX USB transfer frames and HID reports."""

import pytest

from xknx.exceptions import CouldNotParseUSBFrame
from xknx.io.usb.const import (
    EMIID,
    DeviceFeature,
    DeviceFeatureService,
    ProtocolID,
)
from xknx.io.usb.frame import ReportAssembler, USBTransferFrame, device_feature_frame


def _report(hex_data: str) -> bytes:
    return bytes.fromhex(hex_data).ljust(64, b"\x00")


class TestUSBTransferFrame:
    """Test encoding and decoding of KNX USB transfer frames."""

    def test_device_feature_get(self) -> None:
        """Test a Device Feature Get as sent to a real interface."""
        frame = device_feature_frame(
            DeviceFeatureService.GET, DeviceFeature.SUPPORTED_EMI_TYPE
        )
        assert frame.to_reports() == [_report("011309000800010f01000001")]

    def test_device_feature_response(self) -> None:
        """Test the Device Feature Response of a real interface."""
        assembler = ReportAssembler()
        frame = assembler.feed(_report("01130b000800030f0200000100040000"))
        assert frame == USBTransferFrame(
            protocol=ProtocolID.BUS_ACCESS_SERVER_FEATURE,
            service=DeviceFeatureService.RESPONSE,
            body=bytes.fromhex("010004"),
        )
        assert frame.feature is DeviceFeature.SUPPORTED_EMI_TYPE
        assert frame.feature_data == bytes.fromhex("0004")

    def test_tunnelled_cemi(self) -> None:
        """Test an L_Data.ind received from a real interface."""
        assembler = ReportAssembler()
        frame = assembler.feed(
            _report("0113150008000d010300002900bce0102f0012030080346a")
        )
        assert frame is not None
        assert frame.protocol is ProtocolID.KNX_TUNNEL
        assert frame.service == EMIID.CEMI
        assert frame.body == bytes.fromhex("2900bce0102f0012030080346a")
        assert frame.feature is None
        # and back
        assert frame.to_reports() == [
            _report("0113150008000d010300002900bce0102f0012030080346a")
        ]

    @pytest.mark.parametrize(
        ("body_length", "packet_infos"),
        [
            (53, [0x13]),
            (54, [0x15, 0x26]),
            (114, [0x15, 0x26]),
            (115, [0x15, 0x24, 0x36]),
            (297, [0x15, 0x24, 0x34, 0x44, 0x56]),
        ],
    )
    def test_split_and_reassemble(
        self, body_length: int, packet_infos: list[int]
    ) -> None:
        """Test long frames across several HID reports."""
        body = bytes(index % 256 for index in range(body_length))
        frame = USBTransferFrame(
            protocol=ProtocolID.KNX_TUNNEL, service=EMIID.CEMI, body=body
        )
        reports = frame.to_reports()
        assert [report[1] for report in reports] == packet_infos
        assert all(len(report) == 64 for report in reports)
        # the header is only in the first report
        assert reports[0][3:11] == bytes(
            (0, 8, *body_length.to_bytes(2, "big"), 1, 3, 0, 0)
        )
        assembler = ReportAssembler()
        results = [assembler.feed(report) for report in reports]
        assert results[:-1] == [None] * (len(reports) - 1)
        assert results[-1] == frame

    def test_too_long(self) -> None:
        """Test a frame that doesn't fit into 5 reports."""
        frame = USBTransferFrame(
            protocol=ProtocolID.KNX_TUNNEL, service=EMIID.CEMI, body=bytes(298)
        )
        with pytest.raises(ValueError):
            frame.to_reports()

    def test_manufacturer_code_and_unknown_protocol(self) -> None:
        """Test the header fields are kept."""
        frame = USBTransferFrame(
            protocol=0x42, service=0x07, body=b"\x01", manufacturer_code=0x00C5
        )
        parsed = ReportAssembler().feed(frame.to_reports()[0])
        assert parsed == frame
        assert parsed.protocol == 0x42

    @pytest.mark.parametrize(
        "data",
        [
            "0008000001",  # too short
            "010800010f010000 01",  # protocol version 1
            "000700010f010000 01",  # header length 7
            "000800020f010000 01",  # body shorter than its length
        ],
    )
    def test_invalid_header(self, data: str) -> None:
        """Test invalid transfer protocol headers are rejected."""
        with pytest.raises(CouldNotParseUSBFrame):
            USBTransferFrame.from_data(bytes.fromhex(data.replace(" ", "")))


class TestReportAssembler:
    """Test reassembling frames from HID reports."""

    def setup_method(self) -> None:
        """Set up a long frame."""
        # pylint: disable=attribute-defined-outside-init
        self.frame = USBTransferFrame(
            protocol=ProtocolID.KNX_TUNNEL, service=EMIID.CEMI, body=bytes(range(120))
        )
        self.reports = self.frame.to_reports()

    def test_other_report_id_ignored(self) -> None:
        """Test reports of another report id are ignored."""
        assembler = ReportAssembler()
        assert assembler.feed(b"\x02" + self.reports[0][1:]) is None
        assert assembler.feed(b"\x01\x13") is None

    def test_unexpected_sequence(self) -> None:
        """Test a report out of sequence drops the frame."""
        assembler = ReportAssembler()
        assert assembler.feed(self.reports[0]) is None
        assert assembler.feed(self.reports[2]) is None
        # the frame is gone - its remaining reports are ignored too
        assert assembler.feed(self.reports[1]) is None
        assert assembler.feed(self.reports[2]) is None
        # a new frame is received again
        for report in self.reports[:-1]:
            assert assembler.feed(report) is None
        assert assembler.feed(self.reports[-1]) == self.frame

    def test_continuation_without_start(self) -> None:
        """Test a partial packet without start packet is ignored."""
        assert ReportAssembler().feed(self.reports[1]) is None

    def test_start_with_wrong_sequence(self) -> None:
        """Test a start packet must have sequence number 1."""
        report = bytearray(self.reports[0])
        report[1] = 0x25
        assert ReportAssembler().feed(bytes(report)) is None

    def test_new_start_discards_unfinished_frame(self) -> None:
        """Test a start packet discards an unfinished frame."""
        single = USBTransferFrame(
            protocol=ProtocolID.KNX_TUNNEL, service=EMIID.CEMI, body=b"\x29\x00"
        )
        assembler = ReportAssembler()
        assert assembler.feed(self.reports[0]) is None
        assert assembler.feed(single.to_reports()[0]) == single

    def test_sequence_zero_single_packet(self) -> None:
        """Test a single packet with sequence number 0 is ignored: 0 is not allowed."""
        assert ReportAssembler().feed(_report("010309000800010f01000001")) is None
        frame = ReportAssembler().feed(_report("011309000800010f01000001"))
        assert frame is not None
        assert frame.feature is DeviceFeature.SUPPORTED_EMI_TYPE

    def test_invalid_header_message(self) -> None:
        """Test the description of a frame that can't be parsed."""
        with pytest.raises(CouldNotParseUSBFrame) as err:
            USBTransferFrame.from_data(bytes.fromhex("0008"))
        assert str(err.value) == (
            '<CouldNotParseUSBFrame description="KNX USB transfer frame too short: 0008" />'
        )

    def test_invalid_packet_type(self) -> None:
        """Test reports with a reserved packet type are ignored."""
        report = bytearray(self.frame.to_reports()[0])
        report[1] = 0x17
        assert ReportAssembler().feed(bytes(report)) is None

    def test_start_without_header(self) -> None:
        """Test a start packet too short for a header is ignored."""
        assert ReportAssembler().feed(_report("0113030008")) is None

    def test_unknown_feature(self) -> None:
        """Test an unknown feature identifier is kept as int."""
        frame = USBTransferFrame(
            protocol=ProtocolID.BUS_ACCESS_SERVER_FEATURE, service=2, body=b"\x99"
        )
        assert frame.feature == 0x99
