"""Module for KNX Data Secure."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from copy import copy
from datetime import datetime, timezone
import logging
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
# py3.10 backwards compatibility - py3.11 "2018-01-05T00:00:00Z" is supported
_SEQUENCE_NUMBER_INIT_TIMESTAMP = datetime.fromisoformat(
    "2018-01-05T00:00:00+00:00"
).timestamp()


def _initial_sequence_number() -> int:
    """Return an initial sequence number for sending Data Secure Telegrams."""
    return int((time.time() - _SEQUENCE_NUMBER_INIT_TIMESTAMP) * 1000)


class DataSecure:
    """Class for KNX Data Secure handling."""

    def __init__(
        self,
        *,
        group_key_table: dict[GroupAddress, bytes],
        individual_address_table: dict[IndividualAddress, int],
        last_sequence_number_sending: int | None = None,
    ):
        """Initialize DataSecure class."""
        self._group_key_table = group_key_table
        self._individual_address_table = individual_address_table
        self._sequence_number_sending = (
            last_sequence_number_sending or _initial_sequence_number()
        )
        # Holds the last valid sequence number for each individual address.
        # Use sequence_number from keyfile as initial value or 0 from senders for all IAs ?

        if not 0 < self._sequence_number_sending < 0xFFFFFFFFFFFF:
            _local_time_info = (
                f" Local time not set properly? {datetime.now(timezone.utc).isoformat()}"
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

    def get_sequence_number(self) -> int:
        """Return current sequence number sending and increment local stored value."""
        seq_nr = self._sequence_number_sending
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
            )
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
        #   - which we don't have
        return cemi_data

    def _received_secure_cemi(
        self, cemi_data: CEMILData, s_apdu: SecureAPDU
    ) -> CEMILData:
        """Handle received secured CEMI frame."""
        if s_apdu.scf.service is not SecurityALService.S_A_DATA:
            raise DataSecureError(
                f"Only SecurityALService.S_A_DATA supported {cemi_data}",
                log_level=logging.DEBUG,
            )
        if s_apdu.scf.system_broadcast or s_apdu.scf.tool_access:
            # TODO: handle incoming responses with tool key of sending device
            # when we can send with tool key
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
                frame_flags=cemi_data.flags,
                tpci=cemi_data.tpci,
            )
        decrypted_payload = APCI.from_knx(plain_apdu_raw)
        _LOGGER.debug("Unpacked APDU %s from %s", decrypted_payload, s_apdu)

        plain_cemi_data = copy(cemi_data)
        plain_cemi_data.payload = decrypted_payload
        return plain_cemi_data

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
        # Outgoing secure point-to-point frames are sent plain.
        # Data Secure point-to-point is not supported.
        return cemi_data

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
            frame_flags=cemi_data.flags,
            tpci=cemi_data.tpci,
        )
        secure_cemi_data = copy(cemi_data)
        secure_cemi_data.payload = SecureAPDU(scf=scf, secured_data=secure_asdu)
        _LOGGER.debug(
            "Secured APDU %s with %s", cemi_data.payload, secure_cemi_data.payload
        )
        return secure_cemi_data
