import struct
from typing import Optional

from loguru import logger

from knx_hid_datatypes import PacketType, ProtocolID, SequenceNumber, EMIID


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
    def from_bytes(cls, data: bytes):
        """ """
        obj = cls()
        obj._init(data)
        return obj

    def to_knx(self) -> bytes:
        """ """
        if self._sequence_number and self._packet_type:
            return struct.pack("<B", (self._sequence_number.value << 4) | self._packet_type.value)
        else:
            return bytes()

    @property
    def sequence_number(self) -> Optional[SequenceNumber]:
        """ """
        return self._sequence_number

    @property
    def packet_type(self) -> Optional[PacketType]:
        """ """
        return self._packet_type

    def _init(self, data: bytes):
        """ """
        if len(data) != 1:
            logger.error(f"received {len(data)} bytes, expected one byte")
            return
        self._sequence_number = SequenceNumber(data[0] >> 4)
        self._packet_type = PacketType(data[0] & 0x0F)


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
    """

    def __init__(self) -> None:
        self._report_id = 0x01
        self._packet_info = None
        self._data_length = 0
        self._valid = False

    @classmethod
    def from_bytes(cls, data: bytes):
        """ """
        obj = cls()
        obj._init(data)
        return obj

    def to_knx(self) -> bytes:
        """ """
        if self._valid:
            return struct.pack("<B1sB", self._report_id, self._packet_info.to_knx(), self._data_length)
        else:
            return bytes()

    @property
    def report_id(self) -> int:
        """ """
        return self._report_id

    @report_id.setter
    def report_id(self, value: int):
        """ """
        if value != 0x01:
            logger.warning("the Report ID value shall have the fixed value 01h (3.4.1.2.1 Report ID)")
        self._report_id = value

    @property
    def packet_info(self) -> Optional[PacketInfo]:
        """
        returns an object containing information about the sequence number (3.4.1.2.2 Sequence number)
        and packet type (start/partial/end packet) (3.4.1.2.3 Packet type)
        """
        return self._packet_info

    @property
    def data_length(self) -> int:
        """ """
        return self._data_length

    @property
    def is_valid(self) -> bool:
        """ """
        return self._valid

    def _init(self, data: bytes):
        """ """
        if len(data) != 3:
            logger.error(f"KNX HID Report Header: received {len(data)} bytes, but expected 3")
            return
        self._report_id = data[0]
        self._packet_info = PacketInfo.from_bytes(data[1:2])
        self._data_length = data[2]
        if self._report_id == 0x01:
            self._valid = True


class KNXUSBTransferProtocolHeader:
    """
    The KNX USB Transfer Protocol Header shall only be located in the start packet.
    (3.4.1.3 Data (KNX HID report body))

    Parameters
    ----------
    protocol_version: (1 octet)
        The protocol version information shall state the revision of the KNX USB
        Transfer Protocol that the following frame (from header length field on)
        is subject to. The only valid protocol version at this time is ‘0’.
    header_length: (1 octet)
        The Header Length shall be the number of octets of the KNX USB Transfer
        Protocol Header.
        Version ‘0’ of the protocol shall always use header length = 8.
        If the value of the Header Length field in the KNX USB Transfer protocol
        header is not 8, the receiver shall reject the entire HID Report.
    body_length: (2 octets)
        The Body Length shall be the number of octets of the KNX USB Transfer Protocol
        Body. Typically this is the length of the EMI frame (EMI1/2 or cEMI) with
        EMI Message Code included. For a KNX Frame with APDU-length = 255 (e.g. extended frame
        format on TP1), the length of the KNX USB Transfer Protocol Body can be
        greater than 255. Therefore two octets are needed for the length information.
    protocol_id: (1 octet)
        It is required that an interface device connecting a PC with a field bus
        via an USB link can not only transfer KNX frames but also other protocols.
        For this purpose, the field Protocol ID (octet 5) in the header shall be
        used as the main protocol separator.
        The information whether a frame is a request, a response or an indication
        shall be given by the contents of the field EMI Message Code. This is the
        1st octet in the KNX USB Transfer Protocol Body.
    emi_id: (1 octet)
        For a KNX Tunnel, the 6th octet within the KNX USB Transfer Protocol Header
        shall be an identifier representing the EMI format used in the KNX USB
        Transfer Protocol Body.
    manufacturer_code: (2 octets)
        In protocol version ‘0’, this field shall always be present.
        Value ‘0000h’ shall be used for transmission of frames that fully comply
        with the standardised field bus protocol, indicated with Protocol ID octet.
        In case of a KNX Link Layer Tunnel, this field shall be set to ‘0000h’.
        If not fully complying with the standard indicated in the Protocol ID field,
        then the manufacturer code field of the KNX USB Transfer Protocol Header
        (7th & 8th octet) shall filled in with the manufacturer’s KNX member ID.
        Example: an own manufacturer specific application layer is used on top
        of standardised lower layers.
    """

    def __init__(self) -> None:
        self._protocol_version = 0x00
        self._header_length = 0x00
        self._body_length = 0x0000
        self._protocol_id = 0x00
        self._emi_id = None
        self._manufacturer_code = 0x0000
        self._expected_byte_count = 8
        self._valid = False

    @classmethod
    def from_bytes(cls, data: bytes):
        """ """
        obj = cls()
        obj._init(data)
        return obj

    def to_knx(self) -> bytes:
        """ """
        if self._valid:
            return struct.pack("<BBHBBH", self._protocol_version, self._header_length, self._body_length,
                               self._protocol_id.value, self._emi_id.value, self._manufacturer_code)
        return bytes()

    @property
    def protocol_version(self) -> int:
        """ """
        return self._protocol_version

    @property
    def header_length(self) -> int:
        """ """
        return self._header_length

    @property
    def body_length(self) -> int:
        """ """
        return self._body_length

    @property
    def protocol_id(self) -> int:
        """ """
        return self._protocol_id

    @property
    def emi_id(self) -> Optional[EMIID]:
        """ """
        return self._emi_id

    @property
    def manufacturer_code(self) -> int:
        """ """
        return self._manufacturer_code

    @property
    def is_valid(self) -> bool:
        """ """
        return self._valid

    def _init(self, data: bytes):
        """ """
        if len(data) != self._expected_byte_count:
            logger.error(f"received {len(data)} bytes, expected {self._expected_byte_count}")
            return
        (
            self._protocol_version,
            self._header_length,
            self._body_length,
            self._protocol_id,
            self._emi_id,
            self._manufacturer_code,
        ) = struct.unpack("<BBHBBH", data)
        self._protocol_id = ProtocolID(self._protocol_id)
        self._emi_id = EMIID(self._emi_id)
        self._valid = True


class KNXUSBTransferProtocolBody:
    """
    Represents the body part of `3.4.1.3 Data (KNX HID report body)` of the KNX specification
    Header data is only present in the first frame.

    Parameters
    ----------
    emi_message_code: (1 octet)
    data: (max. 52 octets (first frame) / 61 octets)
    """

    def __init__(self):
        self._emi_message_code = None
        self._data = None
        self._valid = False
        self._max_bytes = 53
        self._max_bytes_partial = 61

    @classmethod
    def from_bytes(cls, data: bytes):
        """ """
        obj = cls()
        obj._init(data)
        return obj

    def to_knx(self, partial: bool) -> bytes:
        """ """
        if self._valid:
            data_length = self._max_bytes_partial if partial else self._max_bytes
            data_length -= 1  # subtract the EMI message code
            data = self._data.ljust(data_length, b'\x00')
            return struct.pack(f"<B{len(data)}s", self._emi_message_code, data)
        return bytes()

    @property
    def emi_message_code(self):
        """ """
        return self._emi_message_code

    @property
    def data(self) -> Optional[bytes]:
        """ """
        return self._data

    @property
    def is_valid(self) -> bool:
        """ """
        return self._valid

    def _init(self, data: bytes) -> None:
        """ """
        if len(data) not in [self._max_bytes, self._max_bytes_partial]:
            logger.error(
                f"received {len(data)} bytes, expected {self._max_bytes} bytes for start packets, or {self._max_bytes_partial} bytes for partial packets")
            return
        self._emi_message_code = data[0]
        self._data = data[1:]
        self._valid = True


class KNXHIDReportBody:
    """ Represents `3.4.1.3 Data (KNX HID report body)` of the KNX specification """

    def __init__(self):
        self._max_size = 61  # HID frame has max. size of 64 - 3 octets for the header
        self._data_raw = None
        self._header = None
        self._body = None
        self._is_valid = False
        self._partial = False

    @classmethod
    def from_bytes(cls, data: bytes, partial: bool = False):
        """ Takes the report body data bytes and create a `KNXHIDReportBody` object """
        obj = cls()
        obj._init(data, partial)
        return obj

    def to_knx(self) -> bytes:
        """ Converts the data in the object to its byte representation, ready to be sent over USB. """
        if self._header and self._body:
            return self._header.to_knx() + self._body.to_knx(self._partial)
        else:
            return bytes()

    @property
    def knx_usb_transfer_protocol_header(self) -> Optional[KNXUSBTransferProtocolHeader]:
        """
        Contains the header part as described in `3.4.1.3 Data (KNX HID report body)`
        of the KNX specification
        """
        return self._header

    @property
    def knx_usb_transfer_protocol_body(self) -> Optional[KNXUSBTransferProtocolBody]:
        """
        Contains the body part as described in `3.4.1.3 Data (KNX HID report body)`
        of the KNX specification
        """
        return self._body

    @property
    def is_valid(self) -> bool:
        """ Returns true if all fields could be parsed successfully """
        return self._is_valid

    def _init(self, data: bytes, partial: bool) -> None:
        """ """
        if len(data) != self._max_size:
            logger.error(
                f"only received {len(data)} bytes, expected {self._max_size}. (Unused bytes in the last HID report frame shall be filled with 00h (3.4.1.2.2 Sequence number))"
            )
            return
        self._data_raw = data
        self._partial = partial
        if self._partial:
            self._body = KNXUSBTransferProtocolBody.from_bytes(data)
            self._is_valid = self._body.is_valid
        else:
            self._header = KNXUSBTransferProtocolHeader.from_bytes(data[:8])  # only in the start packet has a header
            self._body = KNXUSBTransferProtocolBody.from_bytes(data[8:])
            self._is_valid = self._header.is_valid and self._body.is_valid


class KNXHIDFrame:
    """ Represents `3.4.1.1 HID report frame structure` of the KNX specification """

    def __init__(self) -> None:
        self._body = None
        self._data_raw = bytes()
        self._expected_byte_count = 64
        self._header = None
        self._is_valid = False
        self._partial = False

    @classmethod
    def from_bytes(cls, data: bytes, partial: bool = False):
        """ Takes USB HID data and creates a `KNXHIDFrame` object. """
        obj = cls()
        obj._init(data, partial)
        return obj

    def to_knx(self) -> bytes:
        """ Converts the data in the object to its byte representation, ready to be sent over USB. """
        return self._header.to_knx() + self._body.to_knx()

    @property
    def is_valid(self) -> bool:
        """
        Returns true if all fields were parsed successfully and seem to
        be plausible
        """
        return self._is_valid

    @property
    def report_header(self) -> Optional[KNXHIDReportHeader]:
        """
        Contains the information as described in `3.4.1.2 KNX HID report header`
        of the KNX specification

        Fields
          - Report ID
          - Sequence number
          - Packet type
          - Data length
        """
        return self._header

    @property
    def report_body(self) -> Optional[KNXHIDReportBody]:
        """
        Contains the information as described in `3.4.1.3 Data (KNX HID report body)`
        of the KNX specification

        Fields
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

    def _init(self, data: bytes, partial: bool):
        """ """
        if len(data) < self._expected_byte_count:
            logger.warning(
                f"only received {len(data)} bytes, expected {self._expected_byte_count}. (Unused bytes in the last HID report frame shall be filled with 00h (3.4.1.2.2 Sequence number))"
            )
        self._data_raw = data
        self._partial = partial
        self._header = KNXHIDReportHeader.from_bytes(self._data_raw[:3])
        self._body = KNXHIDReportBody.from_bytes(self._data_raw[3:], partial=partial)
        self._is_valid = self._header.is_valid and self._body.is_valid
