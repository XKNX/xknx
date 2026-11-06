"""Module for KNX Data Secure."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from copy import copy
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import secrets
import time

from xknx.cemi import CEMILData
from xknx.exceptions import DataSecureError
from xknx.telegram.address import GroupAddress, IndividualAddress
from xknx.telegram.apci import APCI, SecureAPDU

from .data_secure_asdu import (
    SecureData,
    SecurityAlgorithmIdentifier,
    SecurityALService,
    SecurityControlField,
)
from .keyring import Keyring

_LOGGER = logging.getLogger("xknx.data_secure")

# Same timedelta in milliseconds as used in Falcon used for initial sequence_number_sending
_SEQUENCE_NUMBER_INIT_TIMESTAMP = datetime.fromisoformat(
    "2018-01-05T00:00:00Z"
).timestamp()
_SEQUENCE_NUMBER_MAX = 0xFFFFFFFFFFFF  # 48 bit max value
_SERIAL_NUMBER_NONE = bytes(6)

# Security Control Fields with the Tool Access flag set: the Tool Key protects the frame -
# KNX v02.01.01 - Application Layer 03.03.07 - §5.2.1.2 Figure 107.
_TOOL_ACCESS_DATA_SCF = SecurityControlField(
    algorithm=SecurityAlgorithmIdentifier.CCM_ENCRYPTION,
    service=SecurityALService.S_A_DATA,
    system_broadcast=False,
    tool_access=True,
)
_TOOL_ACCESS_SYNC_REQ_SCF = SecurityControlField(
    algorithm=SecurityAlgorithmIdentifier.CCM_ENCRYPTION,
    service=SecurityALService.S_A_SYNC_REQ,
    system_broadcast=False,
    tool_access=True,
)


def _initial_sequence_number() -> int:
    """Return an initial sequence number for sending Data Secure Telegrams."""
    return int((time.time() - _SEQUENCE_NUMBER_INIT_TIMESTAMP) * 1000)


@dataclass(slots=True)
class _SyncRequest:
    """A pending S-A_Sync_Req-PDU to a device, secured with its Tool Key."""

    sequence_number: int
    serial_number: bytes
    challenge: bytes


def is_data_secure(cemi_data: CEMILData) -> bool:
    """Return True if the payload frame is DataSecure encrypted / authenticated."""
    return isinstance(cemi_data.payload, SecureAPDU)


class DataSecure:
    """Class for KNX Data Secure handling."""

    __slots__ = (
        "_group_key_table",
        "_individual_address_table",
        "_sequence_number_sending",
        "_sync_requests",
        "_tool_access_last_valid",
        "_tool_key_table",
    )

    def __init__(
        self,
        *,
        group_key_table: dict[GroupAddress, bytes],
        individual_address_table: dict[IndividualAddress, int],
        last_sequence_number_sending: int | None = None,
        tool_key_table: dict[IndividualAddress, bytes] | None = None,
    ) -> None:
        """
        Initialize DataSecure class.

        `tool_key_table` holds the Tool Key (or, for a device in its delivery state, the
        FDSK) of devices to communicate with point-to-point using Tool Access.
        """
        self._group_key_table = group_key_table
        self._individual_address_table = individual_address_table
        self._tool_key_table: dict[IndividualAddress, bytes] = {}
        # Last valid Sequence Number of each device in Tool Access, known after S-A_Sync.
        self._tool_access_last_valid: dict[IndividualAddress, int] = {}
        self._sync_requests: dict[IndividualAddress, _SyncRequest] = {}
        for address, key in (tool_key_table or {}).items():
            self.set_tool_key(address, key)
        self._sequence_number_sending = (
            last_sequence_number_sending or _initial_sequence_number()
        )
        # Holds the last valid sequence number for each individual address.
        # Use sequence_number from keyfile as initial value or 0 from senders for all IAs ?

        if not 0 < self._sequence_number_sending <= _SEQUENCE_NUMBER_MAX:
            _local_time_info = (
                f" Local time not set properly? {datetime.now(UTC).isoformat()}"
                if not last_sequence_number_sending
                else ""
            )
            raise DataSecureError(
                f"Initial sequence number out of range: {self._sequence_number_sending}"
                f"{_local_time_info}"
            )
        _LOGGER.info(
            "Data Secure initialized for %s group addresses from %s individual addresses.",
            len(self._group_key_table),
            len(self._individual_address_table),
        )
        _LOGGER.debug(
            "Data Secure initial sequence number: %s, groups: %s, senders: %s",
            self._sequence_number_sending,
            [str(ga) for ga in self._group_key_table],
            [str(ia) for ia in self._individual_address_table],
        )

    @staticmethod
    def init_from_keyring(keyring: Keyring) -> DataSecure | None:
        """
        Initialize DataSecure from Keyring.

        Return None if no Data Secure information is found in the Keyring.
        """
        ga_key_table = keyring.get_data_secure_group_keys()
        ia_seq_table = keyring.get_data_secure_senders()
        # TODO: persist local individual_address_table and update from that file on start
        #       to have more fresh initial sequence numbers
        if not ga_key_table:
            return None
        return DataSecure(
            group_key_table=ga_key_table,
            individual_address_table=ia_seq_table,
        )

    def set_tool_key(self, address: IndividualAddress, key: bytes) -> None:
        """
        Communicate with `address` point-to-point using Tool Access with `key`.

        `key` is the device's Tool Key, or its FDSK while it is in its delivery state.
        A known Sequence Number of the device is kept only if the key is unchanged.
        """
        if len(key) != 16:
            raise DataSecureError(f"Invalid Tool Key length for {address}: {len(key)}")
        if self._tool_key_table.get(address) != key:
            self._tool_access_last_valid.pop(address, None)
            self._sync_requests.pop(address, None)
        self._tool_key_table[address] = bytes(key)

    def remove_tool_key(self, address: IndividualAddress) -> None:
        """Stop using Tool Access for `address`."""
        self._tool_key_table.pop(address, None)
        self._tool_access_last_valid.pop(address, None)
        self._sync_requests.pop(address, None)

    def tool_access_synchronized(self, address: IndividualAddress) -> bool:
        """Return whether the Sequence Number of `address` in Tool Access is known."""
        return address in self._tool_access_last_valid

    def sync_request(
        self,
        address: IndividualAddress,
        serial_number: bytes | None = None,
    ) -> SecureAPDU:
        """
        Prepare an S-A_Sync_Req-PDU to `address`, secured with its Tool Key.

        Send the returned APDU to `address` point-to-point; it is completed (encrypted
        and authenticated) when it passes `outgoing_cemi`, since the MAC covers the
        frame's address and TPCI fields. The response updates the Sequence Numbers in
        `received_cemi`. `serial_number` is the assumed KNX Serial Number of the device
        or None for 0 - KNX v02.01.01 - Application Layer 03.03.07 - §5.3.2.
        """
        if address not in self._tool_key_table:
            raise DataSecureError(f"No Tool Key for {address}")
        request = _SyncRequest(
            # SeqNr_local is the current Sequence Number Sending; sending the request does
            # not alter it - KNX v02.01.01 - Application Layer 03.03.07 - §5.3.2 NOTE 38.
            sequence_number=self._sequence_number_sending,
            serial_number=serial_number or _SERIAL_NUMBER_NONE,
            challenge=secrets.token_bytes(6),
        )
        self._sync_requests[address] = request
        return SecureAPDU(
            scf=_TOOL_ACCESS_SYNC_REQ_SCF,
            secured_data=SecureData(
                sequence_number_bytes=request.sequence_number.to_bytes(6, "big"),
                secured_apdu=request.serial_number + request.challenge,
                message_authentication_code=bytes(4),
            ),
        )

    def get_sequence_number(self) -> int:
        """Return current sequence number sending and increment local stored value."""
        seq_nr = self._sequence_number_sending
        if seq_nr > _SEQUENCE_NUMBER_MAX:
            raise DataSecureError(
                "Sequence number sending overflow. You have reached the end of KNX Data Secure. "
                "Reset your devices individual address tables and re-initialize XKNX.",
                log_level=logging.ERROR,
            )
        self._sequence_number_sending += 1
        return seq_nr

    @contextmanager
    def check_sequence_number(
        self, source_address: IndividualAddress, received_sequence_number: int
    ) -> Iterator[None]:
        """
        Check the last valid sequence number for incoming frames from `source_address`.

        Update the Security Individual Address Table if no further exception is raised.
        Raise `DataSecureError` if sequence number is invalid or sender is not known.
        """
        try:
            last_valid_sequence_number = self._individual_address_table[source_address]
        except KeyError:
            raise DataSecureError(
                f"Source address not found in Security Individual Address Table: {source_address}",
                log_level=logging.INFO,
            ) from None
        if not received_sequence_number > last_valid_sequence_number:
            # TODO: implement and increment Security Failure Log counter (not when equal)
            raise DataSecureError(
                f"Sequence number too low for {source_address}: "
                f"{received_sequence_number} received, {last_valid_sequence_number} last valid",
                log_level=logging.WARNING,
            )

        yield
        # Don't increment sequence number if exception is raised while decrypting (yield)
        self._individual_address_table[source_address] = received_sequence_number

    def received_cemi(self, cemi_data: CEMILData) -> CEMILData:
        """Handle received CEMI frame."""
        # Data Secure frame
        if isinstance(cemi_data.payload, SecureAPDU):
            return self._received_secure_cemi(cemi_data, cemi_data.payload)
        # Plain group communication frame
        if isinstance(cemi_data.dst_addr, GroupAddress):
            if cemi_data.dst_addr in self._group_key_table:
                raise DataSecureError(
                    f"Discarding frame with plain APDU for secure group address: {cemi_data}",
                    log_level=logging.WARNING,
                )
            return cemi_data
        # Plain point-to-point frame
        #   No point to point key table is implemented at the moment as ETS can't even configure this
        #   only way to communicate point-to-point with data secure currently is with tool key
        return cemi_data

    def _received_secure_cemi(
        self, cemi_data: CEMILData, s_apdu: SecureAPDU
    ) -> CEMILData:
        """Handle received secured CEMI frame."""
        if (
            s_apdu.scf.tool_access
            and not s_apdu.scf.system_broadcast
            and isinstance(cemi_data.src_addr, IndividualAddress)
            and isinstance(cemi_data.dst_addr, IndividualAddress)
            and (key := self._tool_key_table.get(cemi_data.src_addr))
        ):
            return self._received_tool_access_cemi(cemi_data, s_apdu, key)
        if s_apdu.scf.service is not SecurityALService.S_A_DATA:
            raise DataSecureError(
                f"Only SecurityALService.S_A_DATA supported {cemi_data}",
                log_level=logging.DEBUG,
            )
        if s_apdu.scf.system_broadcast or s_apdu.scf.tool_access:
            raise DataSecureError(
                f"System broadcast and tool access not supported {cemi_data}",
                log_level=logging.DEBUG,
            )

        # Secure group communication frame
        if isinstance(cemi_data.dst_addr, GroupAddress):
            if not (key := self._group_key_table.get(cemi_data.dst_addr)):
                raise DataSecureError(
                    f"No key found for group address {cemi_data.dst_addr} from {cemi_data.src_addr}",
                    log_level=logging.INFO,
                )
        # Secure point-to-point frame
        else:
            # TODO: maybe possible to implement this over tool key
            raise DataSecureError(
                f"Secure Point-to-Point communication not supported {cemi_data}",
                log_level=logging.DEBUG,
            )

        with self.check_sequence_number(
            source_address=cemi_data.src_addr,
            received_sequence_number=int.from_bytes(
                s_apdu.secured_data.sequence_number_bytes, "big"
            ),
        ):
            _address_fields_raw = (
                cemi_data.src_addr.to_knx() + cemi_data.dst_addr.to_knx()
            )
            plain_apdu_raw = s_apdu.secured_data.get_plain_apdu(
                key=key,
                scf=s_apdu.scf,
                address_fields_raw=_address_fields_raw,
                address_type=cemi_data.address_type,
                frame_format=cemi_data.flags.frame_format,
                tpci=cemi_data.tpci,
            )
        decrypted_payload = APCI.from_knx(plain_apdu_raw)
        _LOGGER.debug("Unpacked APDU %s from %s", decrypted_payload, s_apdu)

        plain_cemi_data = copy(cemi_data)
        plain_cemi_data.payload = decrypted_payload
        return plain_cemi_data

    def _received_tool_access_cemi(
        self, cemi_data: CEMILData, s_apdu: SecureAPDU, key: bytes
    ) -> CEMILData:
        """Handle a point-to-point frame from a device secured with its Tool Key."""
        address = cemi_data.src_addr
        assert isinstance(address, IndividualAddress)
        _address_fields_raw = cemi_data.src_addr.to_knx() + cemi_data.dst_addr.to_knx()
        if s_apdu.scf.service is SecurityALService.S_A_SYNC_RES:
            self._received_sync_response(
                address, cemi_data, s_apdu, key, _address_fields_raw
            )
            # Passed on as it is, so a pending request receives the response.
            return cemi_data
        if s_apdu.scf.service is not SecurityALService.S_A_DATA:
            raise DataSecureError(
                f"Unexpected Tool Access service from {address}: {s_apdu.scf}",
                log_level=logging.DEBUG,
            )
        if (last_valid := self._tool_access_last_valid.get(address)) is None:
            raise DataSecureError(
                f"Sequence Number of {address} in Tool Access not known - "
                "synchronize with S-A_Sync first",
                log_level=logging.INFO,
            )
        sequence_number = int.from_bytes(
            s_apdu.secured_data.sequence_number_bytes, "big"
        )
        if not sequence_number > last_valid:
            raise DataSecureError(
                f"Sequence number too low for {address}: "
                f"{sequence_number} received, {last_valid} last valid",
                log_level=logging.WARNING,
            )
        plain_apdu_raw = s_apdu.secured_data.get_plain_apdu(
            key=key,
            scf=s_apdu.scf,
            address_fields_raw=_address_fields_raw,
            address_type=cemi_data.address_type,
            frame_format=cemi_data.flags.frame_format,
            tpci=cemi_data.tpci,
        )
        self._tool_access_last_valid[address] = sequence_number
        plain_cemi_data = copy(cemi_data)
        plain_cemi_data.payload = APCI.from_knx(plain_apdu_raw)
        return plain_cemi_data

    def _received_sync_response(
        self,
        address: IndividualAddress,
        cemi_data: CEMILData,
        s_apdu: SecureAPDU,
        key: bytes,
        address_fields_raw: bytes,
    ) -> None:
        """
        Take over the Sequence Numbers of an S-A_Sync_Res-PDU.

        KNX v02.01.01 - Application Layer 03.03.07 - §5.3.2 and
        KNX v02.01.02 - Management Procedures 03.05.02 - §4.2.
        """
        if (request := self._sync_requests.get(address)) is None:
            # ignored if no S-A_Sync_Req-PDU was sent before
            raise DataSecureError(
                f"Unexpected S-A_Sync response from {address}",
                log_level=logging.DEBUG,
            )
        remote, local = s_apdu.secured_data.get_sync_response_sequence_numbers(
            key=key,
            scf=s_apdu.scf,
            challenge=request.challenge,
            address_fields_raw=address_fields_raw,
            address_type=cemi_data.address_type,
            frame_format=cemi_data.flags.frame_format,
            tpci=cemi_data.tpci,
        )
        if remote == 0 or local == 0:
            # both are next valid Sequence Numbers, which are never 0
            raise DataSecureError(
                f"Invalid Sequence Number in S-A_Sync response from {address}"
            )
        del self._sync_requests[address]
        # SeqNr_remote is the next Sequence Number of the device; keep the highest value.
        self._tool_access_last_valid[address] = max(
            remote - 1, self._tool_access_last_valid.get(address, 0)
        )
        # SeqNr_local is the next Sequence Number the device expects from us.
        self._sequence_number_sending = max(local, self._sequence_number_sending)
        _LOGGER.debug(
            "Tool Access synchronized with %s: sending %s, receiving from %s",
            address,
            local,
            remote,
        )

    def outgoing_cemi(self, cemi_data: CEMILData) -> CEMILData:
        """Handle outgoing CEMI frame. Pass through as plain frame or encrypt."""
        # Outgoing  group communication frame
        if isinstance(cemi_data.dst_addr, GroupAddress):
            if key := self._group_key_table.get(cemi_data.dst_addr):
                scf = SecurityControlField(
                    algorithm=SecurityAlgorithmIdentifier.CCM_ENCRYPTION,
                    service=SecurityALService.S_A_DATA,
                    system_broadcast=False,
                    tool_access=False,
                )
                return self._secure_data_cemi(key=key, scf=scf, cemi_data=cemi_data)
            return cemi_data
        # Outgoing point-to-point frame to a device with a Tool Key
        if (key := self._tool_key_table.get(cemi_data.dst_addr)) is not None:
            return self._tool_access_cemi(cemi_data.dst_addr, key, cemi_data)
        # Other point-to-point frames are sent plain.
        return cemi_data

    def _tool_access_cemi(
        self, address: IndividualAddress, key: bytes, cemi_data: CEMILData
    ) -> CEMILData:
        """Secure an outgoing point-to-point frame with the Tool Key of its destination."""
        payload = cemi_data.payload
        if payload is None:
            # transport layer control frames (T_Connect, T_Ack, ...) have no APDU
            return cemi_data
        if isinstance(payload, SecureAPDU):
            if payload.scf.service is SecurityALService.S_A_SYNC_REQ and (
                request := self._sync_requests.get(address)
            ):
                return self._sync_request_cemi(key, request, cemi_data)
            return cemi_data
        return self._secure_data_cemi(
            key=key, scf=_TOOL_ACCESS_DATA_SCF, cemi_data=cemi_data
        )

    @staticmethod
    def _sync_request_cemi(
        key: bytes, request: _SyncRequest, cemi_data: CEMILData
    ) -> CEMILData:
        """
        Complete the S-A_Sync_Req-PDU prepared by `sync_request` for this frame.

        The result only depends on the request and the frame, so a repetition of the
        frame by the transport layer is secured identically.
        """
        secured_data = SecureData.init_sync_request(
            key=key,
            scf=_TOOL_ACCESS_SYNC_REQ_SCF,
            sequence_number=request.sequence_number,
            serial_number=request.serial_number,
            challenge=request.challenge,
            address_fields_raw=cemi_data.src_addr.to_knx()
            + cemi_data.dst_addr.to_knx(),
            address_type=cemi_data.address_type,
            frame_format=cemi_data.flags.frame_format,
            tpci=cemi_data.tpci,
        )
        secure_cemi_data = copy(cemi_data)
        secure_cemi_data.payload = SecureAPDU(
            scf=_TOOL_ACCESS_SYNC_REQ_SCF, secured_data=secured_data
        )
        return secure_cemi_data

    def _secure_data_cemi(
        self,
        key: bytes,
        scf: SecurityControlField,
        cemi_data: CEMILData,
    ) -> CEMILData:
        """Wrap encrypted payload of a plain CEMILData in a SecureAPDU."""
        plain_apdu_raw: bytes | bytearray

        if cemi_data.payload is not None:
            plain_apdu_raw = cemi_data.payload.to_knx()
        else:
            # TODO: test if this is correct
            plain_apdu_raw = b""  # used in point-to-point eg. TConnect
        secure_asdu = SecureData.init_from_plain_apdu(
            key=key,
            apdu=plain_apdu_raw,
            scf=scf,
            sequence_number=self.get_sequence_number(),
            address_fields_raw=cemi_data.src_addr.to_knx()
            + cemi_data.dst_addr.to_knx(),
            address_type=cemi_data.address_type,
            frame_format=cemi_data.flags.frame_format,
            tpci=cemi_data.tpci,
        )
        secure_cemi_data = copy(cemi_data)
        secure_cemi_data.payload = SecureAPDU(scf=scf, secured_data=secure_asdu)
        _LOGGER.debug(
            "Secured APDU %s with %s", cemi_data.payload, secure_cemi_data.payload
        )
        return secure_cemi_data
