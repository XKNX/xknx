"""
KNX USB transfer frames and the HID reports carrying them.

A KNX USB transfer frame (transfer protocol header and body) is split into up to
five HID reports of 64 octets: report id, packet info (sequence number and packet
type), data length and up to 61 data octets. The transfer protocol header is only
in the first report.
KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.4.1
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

from xknx.exceptions import CouldNotParseUSBFrame

from .const import (
    HID_REPORT_HEADER_LENGTH,
    HID_REPORT_LENGTH,
    MAX_REPORT_DATA_LENGTH,
    MAX_SEQUENCE_NUMBER,
    PROTOCOL_VERSION,
    REPORT_ID,
    TRANSFER_HEADER_LENGTH,
    DeviceFeature,
    DeviceFeatureService,
    PacketType,
    ProtocolID,
)

logger = logging.getLogger("xknx.log")

_PACKET_TYPES = frozenset(PacketType)


@dataclass(slots=True)
class USBTransferFrame:
    """
    KNX USB transfer frame.

    `service` is the EMI ID for a KNX tunnel frame and the device feature
    service for a bus access server feature frame (header octet 6).
    """

    protocol: ProtocolID | int
    service: int
    body: bytes
    manufacturer_code: int = 0x0000

    def header(self) -> bytes:
        """Encode the KNX USB transfer protocol header."""
        return bytes(
            (
                PROTOCOL_VERSION,
                TRANSFER_HEADER_LENGTH,
                *len(self.body).to_bytes(2, "big"),
                self.protocol,
                self.service,
                *self.manufacturer_code.to_bytes(2, "big"),
            )
        )

    def to_reports(self) -> list[bytes]:
        """Split the frame into HID reports of 64 octets, unused octets set to 00h."""
        data = self.header() + self.body
        chunks = [
            data[start : start + MAX_REPORT_DATA_LENGTH]
            for start in range(0, len(data), MAX_REPORT_DATA_LENGTH)
        ]
        if len(chunks) > MAX_SEQUENCE_NUMBER:
            raise ValueError(
                f"KNX USB transfer frame too long for {MAX_SEQUENCE_NUMBER} HID reports: {len(data)} octets"
            )
        reports: list[bytes] = []
        for index, chunk in enumerate(chunks):
            first = index == 0
            last = index == len(chunks) - 1
            if first and last:
                packet_type = PacketType.START_AND_END
            elif first:
                packet_type = PacketType.START_AND_PARTIAL
            elif last:
                packet_type = PacketType.PARTIAL_AND_END
            else:
                packet_type = PacketType.PARTIAL
            packet_info = ((index + 1) << 4) | packet_type
            report = bytes((REPORT_ID, packet_info, len(chunk))) + chunk
            reports.append(report.ljust(HID_REPORT_LENGTH, b"\x00"))
        return reports

    @classmethod
    def from_data(cls, data: bytes) -> USBTransferFrame:
        """Parse a frame from the reassembled data of its HID reports."""
        if len(data) < TRANSFER_HEADER_LENGTH:
            raise CouldNotParseUSBFrame(
                f"KNX USB transfer frame too short: {data.hex()}"
            )
        if data[0] != PROTOCOL_VERSION:
            raise CouldNotParseUSBFrame(
                f"Unsupported KNX USB transfer protocol version {data[0]}"
            )
        if data[1] != TRANSFER_HEADER_LENGTH:
            # KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.4.1.3.2
            raise CouldNotParseUSBFrame(
                f"Invalid KNX USB transfer header length {data[1]}"
            )
        body_length = int.from_bytes(data[2:4], "big")
        body = data[TRANSFER_HEADER_LENGTH:]
        if len(body) < body_length:
            raise CouldNotParseUSBFrame(
                f"KNX USB transfer body shorter than {body_length} octets: {data.hex()}"
            )
        try:
            protocol: ProtocolID | int = ProtocolID(data[4])
        except ValueError:
            protocol = data[4]
        return cls(
            protocol=protocol,
            service=data[5],
            manufacturer_code=int.from_bytes(data[6:8], "big"),
            body=body[:body_length],
        )

    @property
    def feature(self) -> DeviceFeature | int | None:
        """Feature identifier of a bus access server feature frame."""
        if self.protocol != ProtocolID.BUS_ACCESS_SERVER_FEATURE or not self.body:
            return None
        try:
            return DeviceFeature(self.body[0])
        except ValueError:
            return self.body[0]

    @property
    def feature_data(self) -> bytes:
        """Data of a bus access server feature frame."""
        return self.body[1:]


def device_feature_frame(
    service: DeviceFeatureService,
    feature: DeviceFeature,
    data: bytes = b"",
) -> USBTransferFrame:
    """Create a bus access server feature frame - KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.2."""
    return USBTransferFrame(
        protocol=ProtocolID.BUS_ACCESS_SERVER_FEATURE,
        service=service,
        body=bytes((feature,)) + data,
    )


class ReportAssembler:
    """
    Reassemble KNX USB transfer frames from incoming HID reports.

    A report with an unexpected sequence number is ignored together with the
    frame it belongs to; a new start packet discards an unfinished frame.
    KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.4.1.2.2
    """

    __slots__ = ("_data", "_expected_length", "_next_sequence")

    def __init__(self) -> None:
        """Initialize ReportAssembler."""
        self._data = bytearray()
        self._expected_length: int | None = None
        self._next_sequence = 1

    def _reset(self) -> None:
        self._data.clear()
        self._expected_length = None
        self._next_sequence = 1

    def feed(self, report: bytes) -> USBTransferFrame | None:
        """Process one HID report. Return a frame when it is complete."""
        if len(report) < HID_REPORT_HEADER_LENGTH or report[0] != REPORT_ID:
            logger.debug("Ignoring HID report: %s", report.hex())
            return None
        sequence = report[1] >> 4
        packet_type = report[1] & 0x0F
        length = min(report[2], MAX_REPORT_DATA_LENGTH)
        data = report[HID_REPORT_HEADER_LENGTH : HID_REPORT_HEADER_LENGTH + length]
        if packet_type not in _PACKET_TYPES:
            logger.debug("Ignoring HID report with packet type %s", packet_type)
            self._reset()
            return None
        start = packet_type in (PacketType.START_AND_END, PacketType.START_AND_PARTIAL)
        end = packet_type in (PacketType.START_AND_END, PacketType.PARTIAL_AND_END)

        if start:
            # a start packet has sequence number 1, also a single one; sequence
            # number 0 is not allowed
            if sequence != 1:
                logger.debug("Ignoring start packet with sequence %s", sequence)
                self._reset()
                return None
            if self._expected_length is not None:
                logger.debug("Discarding unfinished KNX USB transfer frame")
            self._reset()
            if len(data) < TRANSFER_HEADER_LENGTH:
                logger.debug(
                    "Ignoring HID start packet without header: %s", report.hex()
                )
                return None
            self._expected_length = TRANSFER_HEADER_LENGTH + int.from_bytes(
                data[2:4], "big"
            )
        elif self._expected_length is None or sequence != self._next_sequence:
            logger.debug(
                "Ignoring HID report with unexpected sequence %s: %s",
                sequence,
                report.hex(),
            )
            self._reset()
            return None

        self._data += data
        self._next_sequence = sequence + 1
        if not end and len(self._data) < self._expected_length:
            return None
        frame_data = bytes(self._data)
        self._reset()
        return USBTransferFrame.from_data(frame_data)
