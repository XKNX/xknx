"""
The cEMI Transport Layer of a KNX USB interface: local access to its own device.

With PID_COMM_MODE set to "cEMI Transport Layer" (06h) the cEMI server holds a transport
layer connection to the application layer of the device it is part of, and takes only
T_Data_Individual and T_Data_Connected messages - KNX v01.04.02 - External Message
Interface 03.06.03 - §4.1.6, §4.2.2.4.2.2. A tool uses it to download into a KNX device
through the device's own USB port - KNX v01.03.04 - Basic and System Components -
Couplers 09.03 - §3.5.4.2.

xknx's management talks to devices with L_Data telegrams and a transport layer of its
own. `TransportLayerMapping` turns these into cEMI Transport Layer messages and back:

* T_Data_Connected and T_Data_Individual go to the device with their APDU.
* T_Connect, T_Disconnect and T_ACK/T_NAK stay local: the cEMI server connects when the
  communication mode is set (§3.5.4.2.2), and sequencing is not applicable on USB
  (§3.5.4.2.4). Each T_Data_Connected is acknowledged locally, as the server confirms
  it after the USB transfer (§3.5.4.2.3).
* Every request gets its L_Data.con locally, for the same reason.
* What the device sends is passed on as L_Data.ind from the device, a T_Data_Connected
  with the sequence numbers xknx's transport layer expects.
"""

from __future__ import annotations

from typing import Final

from xknx.cemi import CEMIMessageCode
from xknx.exceptions import CommunicationError
from xknx.telegram import IndividualAddress

# cEMI Transport Layer message codes - KNX v01.04.02 - External Message Interface 03.06.03 -
# §4.1.6.4.4, §4.1.6.4.5, §4.1.6.5.4, §4.1.6.5.5
T_DATA_CONNECTED_REQ: Final = 0x41
T_DATA_INDIVIDUAL_REQ: Final = 0x4A
T_DATA_CONNECTED_IND: Final = 0x89
T_DATA_INDIVIDUAL_IND: Final = 0x94
# the reserved field in front of L: the cEMI L_Data frame's control fields and addresses
# (§4.1.6.1)
_RESERVED: Final = bytes(6)
# The server may end the connection 25 s after the client's last message (KNX v01.03.04 -
# Basic and System Components - Couplers 09.03 - §3.5.4.2.5); the client keeps it alive.
KEEP_ALIVE_INTERVAL: Final = 20.0

# control field 1 of a received frame: standard frame, not repeated, broadcast, low
# priority; extended frames for an APDU longer than a standard frame takes
_CONTROL_1_STANDARD: Final = 0xBC
_CONTROL_1_EXTENDED: Final = 0x3C
_STANDARD_FRAME_MAX_LENGTH: Final = 15
# control field 2: individual destination, hop count 6
_CONTROL_2: Final = 0x60
# control field 1, bit 0: the confirmation's error flag
_CONFIRM_ERROR: Final = 0x01
# control field 2, bit 7: group destination
_GROUP_DESTINATION: Final = 0x80

# TPCI in the first TPDU octet - KNX v01.02.03 - Transport Layer 03.03.04 - §2
_SEQUENCE_MASK: Final = 0x3C
_NUMBERED: Final = 0x40
_CONTROL: Final = 0x80
_T_CONNECT: Final = 0x80
_T_DISCONNECT: Final = 0x81
_T_ACK: Final = 0xC2


class TransportLayerMapping:
    """Map the L_Data telegrams of xknx's management to the cEMI Transport Layer of a device."""

    __slots__ = ("_receive_sequence", "device_address")

    def __init__(self, device_address: IndividualAddress | None) -> None:
        """
        Initialize the mapping.

        `device_address` is the individual address of the interface's device; when it is
        unknown, the one the management connects to is taken.
        """
        self.device_address = device_address
        self._receive_sequence = 0

    def outgoing(self, raw_cemi: bytes) -> tuple[bytes | None, list[bytes]]:
        """
        Map a cEMI L_Data.req.

        Return the cEMI Transport Layer message to send (None: nothing to send) and the
        frames to pass on as received from the interface: the L_Data.con of the request,
        and for a T_Data_Connected the device's T_ACK.
        """
        if not raw_cemi or raw_cemi[0] != CEMIMessageCode.L_DATA_REQ.value:
            raise CommunicationError(
                "Only L_Data requests can be sent through the cEMI transport layer"
            )
        offset = 2 + raw_cemi[1]
        if len(raw_cemi) < offset + 8:
            raise CommunicationError(f"cEMI L_Data request too short: {raw_cemi.hex()}")
        if raw_cemi[offset + 1] & _GROUP_DESTINATION:
            raise CommunicationError(
                "Through the cEMI transport layer only the interface's own device can be "
                "reached: group telegrams can't be sent"
            )
        source = raw_cemi[offset + 2 : offset + 4]
        destination = IndividualAddress(
            int.from_bytes(raw_cemi[offset + 4 : offset + 6], "big")
        )
        length = raw_cemi[offset + 6]
        tpdu = raw_cemi[offset + 7 : offset + 8 + length]
        tpci = tpdu[0]
        if tpci == _T_CONNECT:
            if self.device_address is None:
                self.device_address = destination
            self._receive_sequence = 0
        self._check_destination(destination)
        confirmation = self._confirmation(raw_cemi, offset)
        if tpci & _CONTROL:
            # T_Connect, T_Disconnect, T_ACK, T_NAK: handled by the cEMI server itself
            return None, [confirmation]
        if tpci & _NUMBERED:
            ack = self._indication(
                bytes((_T_ACK | tpci & _SEQUENCE_MASK,)), destination.to_knx(), source
            )
            message = self._message(T_DATA_CONNECTED_REQ, length, tpdu)
            return message, [confirmation, ack]
        return self._message(T_DATA_INDIVIDUAL_REQ, length, tpdu), [confirmation]

    def incoming(self, raw: bytes, own_address: IndividualAddress) -> bytes | None:
        """
        Map a cEMI Transport Layer indication to an L_Data.ind from the device.

        None for any other message.
        """
        if not raw or raw[0] not in (T_DATA_CONNECTED_IND, T_DATA_INDIVIDUAL_IND):
            return None
        offset = 2 + raw[1]
        if len(raw) < offset + len(_RESERVED) + 2:
            return None
        length = raw[offset + len(_RESERVED)]
        apdu = raw[offset + len(_RESERVED) + 1 : offset + len(_RESERVED) + 2 + length]
        if len(apdu) != length + 1:
            return None
        if raw[0] == T_DATA_CONNECTED_IND:
            tpci = _NUMBERED | self._receive_sequence << 2
            self._receive_sequence = self._receive_sequence + 1 & 0x0F
        else:
            tpci = 0x00
        source = self.device_address or IndividualAddress(0)
        tpdu = bytes((tpci | apdu[0] & 0x03,)) + apdu[1:]
        return self._indication(tpdu, source.to_knx(), own_address.to_knx())

    def _check_destination(self, destination: IndividualAddress) -> None:
        """Refuse a telegram to another device than the interface's own."""
        if self.device_address is not None and destination != self.device_address:
            raise CommunicationError(
                "Through the cEMI transport layer only the interface's own device "
                f"{self.device_address} can be reached, not {destination}"
            )

    @staticmethod
    def _message(code: int, length: int, tpdu: bytes) -> bytes:
        """Return a cEMI Transport Layer message with the APDU of `tpdu` (§4.1.6.1)."""
        return (
            bytes((code, 0x00)) + _RESERVED + bytes((length, tpdu[0] & 0x03)) + tpdu[1:]
        )

    @staticmethod
    def _confirmation(raw_cemi: bytes, offset: int) -> bytes:
        """Return the positive L_Data.con of an L_Data.req."""
        control_1 = raw_cemi[offset] & ~_CONFIRM_ERROR
        return (
            bytes((CEMIMessageCode.L_DATA_CON.value,))
            + raw_cemi[1:offset]
            + bytes((control_1,))
            + raw_cemi[offset + 1 :]
        )

    @staticmethod
    def _indication(tpdu: bytes, source: bytes, destination: bytes) -> bytes:
        """Return an L_Data.ind with `tpdu` from `source` to `destination`."""
        length = len(tpdu) - 1
        control_1 = (
            _CONTROL_1_STANDARD
            if length <= _STANDARD_FRAME_MAX_LENGTH
            else _CONTROL_1_EXTENDED
        )
        return (
            bytes((CEMIMessageCode.L_DATA_IND.value, 0x00, control_1, _CONTROL_2))
            + source
            + destination
            + bytes((length,))
            + tpdu
        )
