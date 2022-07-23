import logging
import struct
from typing import Optional

from xknx.knxip.knxip_enum import CEMIMessageCode

from .knx_hid_datatypes import ProtocolID, EMIID


usb_logger = logging.getLogger("xknx.log")


class KNXUSBTransferProtocolHeaderData:
    """ """
    def __init__(self, body_length: int, protocol_id: ProtocolID, emi_id: EMIID) -> None:
        self.body_length = body_length
        self.protocol_id = protocol_id
        self.emi_id = emi_id


class KNXUSBTransferProtocolBodyData:
    """ """
    def __init__(self, data: bytes, partial: bool) -> None:
        self.data = data
        self.partial = partial


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
        self._header_length = 0x08
        self._body_length = 0x0000
        self._protocol_id = 0x00
        self._emi_id = None
        self._manufacturer_code = 0x0000
        self._expected_byte_count = 8
        self._data_format = ">BBHBBH"
        self._valid = False

    @classmethod
    def from_data(cls, data: KNXUSBTransferProtocolHeaderData):
        """ """
        obj = cls()
        obj._body_length = data.body_length
        obj._protocol_id = data.protocol_id
        obj._emi_id = data.emi_id
        obj._valid = True
        return obj

    @classmethod
    def from_knx(cls, data: bytes):
        """ """
        obj = cls()
        obj._init(data)
        return obj

    def to_knx(self) -> bytes:
        """ """
        if self._valid:
            return struct.pack(self._data_format, self._protocol_version, self._header_length, self._body_length,
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
            usb_logger.error(f"received {len(data)} bytes, expected {self._expected_byte_count}")
            return
        (
            self._protocol_version,
            self._header_length,
            self._body_length,
            self._protocol_id,
            self._emi_id,
            self._manufacturer_code,
        ) = struct.unpack(self._data_format, data)
        try:
            self._protocol_id = ProtocolID(self._protocol_id)
            self._emi_id = EMIID(self._emi_id)
            self._valid = True
        except ValueError as e:
            usb_logger.error(str(e))


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
        self._data = None
        self._valid = False
        self._max_bytes = 53
        self._max_bytes_partial = 61

    @classmethod
    def from_data(cls, data: KNXUSBTransferProtocolBodyData):
        """ """
        obj = cls()
        if len(data.data) <= obj._max_bytes_partial and data.partial:
            obj._data = data.data
            obj._valid = True
        elif len(data.data) <= obj._max_bytes and not data.partial:
            obj._data = data.data
            obj._valid = True
        return obj

    @classmethod
    def from_knx(cls, data: bytes):
        """ """
        obj = cls()
        obj._init(data)
        return obj

    def to_knx(self, partial: bool) -> bytes:
        """ """
        if self._valid:
            data_length = self._max_bytes_partial if partial else self._max_bytes
            data = self._data.ljust(data_length, b'\x00')
            return struct.pack(f"<{len(data)}s", data)
        return bytes()

    @property
    def emi_message_code(self) -> Optional[CEMIMessageCode]:
        """ """
        if len(self._data) > 0:
            return CEMIMessageCode(self._data[0])
        return None

    @property
    def data(self) -> Optional[bytes]:
        """ """
        return self._data

    @property
    def length(self) -> int:
        """ Return the length of the `KNX USB Transfer Protocol Body` including the EMI message code """
        if self._data:
            return len(self._data)
        return 0

    @property
    def is_valid(self) -> bool:
        """ """
        return self._valid

    def _init(self, data: bytes) -> None:
        """ """
        if len(data) not in [self._max_bytes, self._max_bytes_partial]:
            usb_logger.error(
                f"received {len(data)} bytes, expected {self._max_bytes} bytes for start packets, or {self._max_bytes_partial} bytes for partial packets")
            return
        self._data = data
        self._valid = True
