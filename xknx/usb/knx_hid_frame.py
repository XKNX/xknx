from __future__ import annotations

import logging
import struct

from .knx_hid_datatypes import EMIID, PacketType, ProtocolID, SequenceNumber
from .knx_hid_transfer import (
    KNXUSBTransferProtocolBody,
    KNXUSBTransferProtocolBodyData,
    KNXUSBTransferProtocolHeader,
    KNXUSBTransferProtocolHeaderData,
)

logger = logging.getLogger("xknx.log")
knx_logger = logging.getLogger("xknx.knx")
usb_logger = logging.getLogger("xknx.usb")


class PacketInfoData:
    """Container for `PacketInfo` initialization data"""

    def __init__(
        self, sequence_number: SequenceNumber, packet_type: PacketType
    ) -> None:
        self.sequence_number = SequenceNumber(sequence_number)
        self.packet_type = packet_type


class PacketInfo:
    """
    Represents part of a KNX header

    If the length of a KNX frame to be passed through USB exceeds the maximal
    length of the KNX HID Report Body, this is 61 octets, the KNX frame shall
    be transmitted in multiple HID reports.
      - Unused bytes in the last HID report frame shall be filled with 00h.
      - The first HID report frame shall have sequence number 1. Also if
        a single HID report is sufficient for the transmission of the KNX frame,
        this single HID report shall have sequence number 1. The use of sequence
        number 0 is not allowed. The sequence number shall be incremented for
        each next HID report that is used for the transmission of a KNX frame.

    | Sequence Number Value | Description                 |
    |:----------------------|:----------------------------|
    | 0h                    | reserved; shall not be used |
    | 1h                    | 1st packet (start packet)   |
    | 2h                    | 2nd packet                  |
    | 3h                    | 3rd packet                  |
    | 4h                    | 4th packet                  |
    | 5h                    | 5th packet                  |
    | other values          | reserved; not used          |

    Parameters
    ----------
    sequence_number: int (½ octet (high nibble))
    packet_type: int (½ octet (low nibble))
    """

    def __init__(self):
        self._sequence_number = None
        self._packet_type = None

    @classmethod
    def from_data(cls, data: PacketInfoData):
        """ """
        obj = cls()
        obj._sequence_number = data.sequence_number
        obj._packet_type = data.packet_type
        return obj

    @classmethod
    def from_knx(cls, data: bytes):
        """Takes the report body data bytes and create a `PacketInfo` object"""
        obj = cls()
        obj._init(data)
        return obj

    def to_knx(self) -> bytes:
        """Converts the data in the object to its byte representation, ready to be sent over USB."""
        if self._sequence_number and self._packet_type:
            return struct.pack(
                "<B", (self._sequence_number.value << 4) | self._packet_type.value
            )
        else:
            return b""

    @property
    def sequence_number(self) -> SequenceNumber | None:
        """3.4.1.2.2 Sequence number
        If the length of a KNX frame to be passed through USB exceeds the maximal
        length of the KNX HID Report Body, this is 61 octets, the KNX frame
        shall be transmitted in multiple HID reports.
        - Unused bytes in the last HID report frame shall be filled with 00h.
        - The first HID report frame shall have sequence number 1.
          Also if a single HID report is sufficient for the transmission of the KNX frame,
          this single HID report shall have sequence number 1.
          The use of sequence number 0 is not allowed.
          The sequence number shall be incremented for each next HID report that
          is used for the transmission of a KNX frame.
        """
        return self._sequence_number

    @property
    def packet_type(self) -> PacketType | None:
        """3.4.1.2.3 Packet type
        The packet type bit-set as specified in clause 3.4.1.1 shall be used in
        HID Reports as specified in Figure 15.

        | Packet Type Value | Description                                     |
        |:----------------- |:----------------------------------------------- |
        | 0h                | reserved / not allowed                          |
        | 3h (0011b)        | start & end packet (1st and last packet in one) |
        | 4h (0100b)        | partial packet (not start & not end packet)     |
        | 5h (0101b)        | start & partial packet                          |
        | 6h (0110b)        | partial & end packet                            |
        | all other values  | reserved; not allowed                           |
        """
        return self._packet_type

    def _init(self, data: bytes):
        """ """
        if len(data) != 1:
            logger.error(f"received {len(data)} bytes, expected one byte")
            return
        try:
            self._sequence_number = SequenceNumber(data[0] >> 4)
            self._packet_type = PacketType(data[0] & 0x0F)
        except ValueError as ex:
            logger.error(str(ex))


class KNXHIDReportHeaderData:
    """Container for `KNXHIDReportHeader` initialization data"""

    def __init__(self, packet_info: PacketInfo, data_length: int) -> None:
        self.packet_info = packet_info
        self.data_length = data_length


class KNXHIDReportHeader:
    """
    Represents the header of a KNX HID report frame (3.4.1.2 KNX HID report header)

    Parameters
    ----------
    report_id: str or None (1 octet)
        The Report ID allows the HID Class host driver to distinguish incoming data, e.g. pointer from keyboard
        data, by examining this transfer prefix. The Report ID is a feature, which is supported and can be
        managed by the Host driver.
        (fixed to 0x01)
    packet_info: PacketInfo (1 octet)
    data_length: int (1 octet)
        The data length is the number of octets of the data field (KNX HID Report Body).
        This is the information following the data length field itself. The maximum value is 61.
    """

    def __init__(self) -> None:
        self._report_id = 0x01
        self._packet_info = None
        self._data_length = 0
        self._max_expected_data_length = 61
        self._valid = False

    @classmethod
    def from_data(cls, data: KNXHIDReportHeaderData):
        """ """
        obj = cls()
        obj._packet_info = data.packet_info
        obj._data_length = data.data_length
        if data.data_length <= obj._max_expected_data_length:
            obj._valid = True
        return obj

    @classmethod
    def from_knx(cls, data: bytes):
        """Takes the report body data bytes and create a `KNXHIDReportHeader` object"""
        obj = cls()
        obj._init(data)
        return obj

    def to_knx(self) -> bytes:
        """Converts the data in the object to its byte representation, ready to be sent over USB."""
        if self._valid:
            return struct.pack(
                "<B1sB", self._report_id, self._packet_info.to_knx(), self._data_length
            )
        else:
            return 3 * b"\x00"

    @property
    def report_id(self) -> int:
        """3.4.1.2.1 Report ID
        The Report ID allows the HID Class host driver to distinguish incoming data,
        e.g. pointer from keyboard data, by examining this transfer prefix.
        The Report ID is a feature, which is supported and can be managed by the Host driver.
        Further structures and features within the HID Report frames must be driven by "higher level" SW."""
        return self._report_id

    @property
    def packet_info(self) -> PacketInfo | None:
        """
        Returns an object containing information about the sequence number (3.4.1.2.2 Sequence number)
        and packet type (start/partial/end packet) (3.4.1.2.3 Packet type)
        """
        return self._packet_info

    @property
    def data_length(self) -> int:
        """3.4.1.2.4 Datalength
        The data length is the number of octets of the data field (KNX HID Report Body).
        This is the information following the data length field itself. The maximum value is 61."""
        return self._data_length

    @property
    def is_valid(self) -> bool:
        """Returns True if the information in the structure is valid"""
        return self._valid

    def _init(self, data: bytes):
        """Helper function to parse raw KNX data"""
        if len(data) > self._max_expected_data_length:
            logger.error(
                f"KNX HID Report Header: received {len(data)} bytes, but expected not more than {self._max_expected_data_length}"
            )
            return
        self._report_id = data[0]
        self._packet_info = PacketInfo.from_knx(data[1:2])
        self._data_length = data[2]
        if (
            self._report_id == 0x01
            and self._data_length <= self._max_expected_data_length
        ):
            if self._packet_info.packet_type and self._packet_info.sequence_number:
                self._valid = True


class KNXHIDReportBodyData:
    """Container for `KNXHIDReportBody` initialization data"""

    def __init__(
        self, protocol_id: ProtocolID, emi_id: EMIID, data: bytes, partial: bool
    ) -> None:
        self.protocol_id = protocol_id
        self.emi_id = emi_id
        self.data = data
        self.partial = partial


class KNXHIDReportBody:
    """3.4.1.3 Data (KNX HID report body)
    The data field (KNX HID Report Body) consists of the KNX USB Transfer Header
    and the KNX USB Transfer Body (example for an L_Data_Request in cEMI format)"""

    def __init__(self):
        self._max_size = 61  # HID frame has max. size of 64 - 3 octets for the header
        self._header: KNXUSBTransferProtocolHeader | None = None
        self._body: KNXUSBTransferProtocolBody | None = None
        self._is_valid = False
        self._partial = False

    @classmethod
    def from_data(cls, data: KNXHIDReportBodyData):
        """ """
        obj = cls()
        obj._partial = data.partial
        obj._body = KNXUSBTransferProtocolBody.from_data(
            KNXUSBTransferProtocolBodyData(data.data, data.partial)
        )
        if data.partial:
            obj._is_valid = obj._body.is_valid
        else:
            obj._header = KNXUSBTransferProtocolHeader.from_data(
                KNXUSBTransferProtocolHeaderData(
                    obj._body.length, data.protocol_id, data.emi_id
                )
            )
            obj._is_valid = obj._header.is_valid and obj._body.is_valid
        return obj

    @classmethod
    def from_knx(cls, data: bytes, partial: bool = False):
        """Takes the report body data bytes and create a `KNXHIDReportBody` object"""
        obj = cls()
        obj._init(data, partial)
        return obj

    def to_knx(self) -> bytes:
        """Converts the data in the object to its byte representation, ready to be sent over USB."""
        if self._header and self._body:
            return self._header.to_knx() + self._body.to_knx(self._partial)
        else:
            return 61 * b"\x00"

    @property
    def transfer_protocol_header(self) -> KNXUSBTransferProtocolHeader | None:
        """3.4.1.3 Data (KNX HID report body)
        Contains the header part `KNX USB Transfer Protocol Header (only in start packet!)`."""
        return self._header

    @property
    def transfer_protocol_body(self) -> KNXUSBTransferProtocolBody | None:
        """3.4.1.3 Data (KNX HID report body)
        Contains the body part `KNX USB Transfer Protocol Body`."""
        return self._body

    @property
    def data_length(self) -> int:
        """3.4.1.2.4 Datalength
        The data length is the number of octets of the data field (KNX HID Report Body).
        This is the information following the data length field itself. The maximum value is 61."""
        if self._header and self._body:
            return (
                self.transfer_protocol_header.header_length
                + self.transfer_protocol_header.body_length
            )
        if (
            self._partial and self._body
        ):  # the whole `KNX HID Report Body` contains payload
            return (
                self._body.length
            )  # in partial message there is no `transfer_protocol_body`
        return 0

    @property
    def is_valid(self) -> bool:
        """Returns true if all fields could be parsed successfully"""
        return self._is_valid

    def _init(self, data: bytes, partial: bool) -> None:
        """Helper function to parse raw KNX data"""
        if len(data) != self._max_size:
            logger.error(
                f"only received {len(data)} bytes, expected {self._max_size}. (Unused bytes in the last HID report frame shall be filled with 00h (3.4.1.2.2 Sequence number))"
            )
            return
        self._partial = partial
        if self._partial:
            self._body = KNXUSBTransferProtocolBody.from_knx(data)
            self._is_valid = self._body.is_valid
        else:
            self._header = KNXUSBTransferProtocolHeader.from_knx(
                data[:8]
            )  # only the start packet has a header
            self._body = KNXUSBTransferProtocolBody.from_knx(data[8:])
            self._is_valid = self._header.is_valid and self._body.is_valid


class KNXHIDFrameData:
    """Holds the data necessary to initialize a `KNXHIDFrame` object"""

    def __init__(
        self, packet_info: PacketInfo, hid_report_body_data: KNXHIDReportBodyData
    ) -> None:
        self.packet_info = packet_info
        self.hid_report_body_data = hid_report_body_data


class KNXHIDFrame:
    """3.4.1.1 HID report frame structure
    see `09_03 Basic and System Components - Couplers v01.03.03 AS.pdf`
    """

    def __init__(self) -> None:
        self._body: KNXHIDReportBody | None = None
        self._expected_byte_count = 64
        self._header: KNXHIDReportHeader | None = None
        self._is_valid = False
        self._partial = False

    @classmethod
    def from_data(cls, data: KNXHIDFrameData):
        """ """
        obj = cls()
        obj._body = KNXHIDReportBody.from_data(data.hid_report_body_data)
        obj._header = KNXHIDReportHeader.from_data(
            KNXHIDReportHeaderData(data.packet_info, obj._body.data_length)
        )
        obj._partial = data.hid_report_body_data is None
        if data.hid_report_body_data.partial:
            obj._is_valid = obj._body.is_valid
        else:
            obj._is_valid = obj._header.is_valid and obj._body.is_valid
        return obj

    @classmethod
    def from_knx(cls, data: bytes):
        """Takes USB HID data and creates a `KNXHIDFrame` object."""
        obj = cls()
        obj._init(data)
        return obj

    def to_knx(self) -> bytes:
        """Converts the data in the object to its byte representation, ready to be sent over USB."""
        return self._header.to_knx() + self._body.to_knx()

    @property
    def is_valid(self) -> bool:
        """Returns true if all fields were parsed successfully."""
        return self._is_valid

    @property
    def report_header(self) -> KNXHIDReportHeader | None:
        """3.4.1.2 KNX HID report header

        Fields
        ------
          - Report ID
          - Sequence number
          - Packet type
          - Data length
        """
        return self._header

    @property
    def report_body(self) -> KNXHIDReportBody | None:
        """3.4.1.3 Data (KNX HID report body)

        Fields
        ------
          - Protocol version
          - Header length
          - Body length
          - Protocol ID
          - EMI ID
          - Manufacturer code
          - EMI message code
          - Data (cEMI/EMI1/EMI2)
        """
        return self._body

    def _init(self, data: bytes):
        """Helper function to parse raw KNX data"""
        if len(data) < self._expected_byte_count:
            logger.warning(
                f"only received {len(data)} bytes, expected {self._expected_byte_count}. (Unused bytes in the last HID report frame shall be filled with 00h (3.4.1.2.2 Sequence number))"
            )
        self._header = KNXHIDReportHeader.from_knx(data[:3])
        self._body = KNXHIDReportBody.from_knx(
            data[3:],
            partial=self._header.packet_info.sequence_number
            != SequenceNumber.FIRST_PACKET,
        )
        self._is_valid = self._header.is_valid and self._body.is_valid
