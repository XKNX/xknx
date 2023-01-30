"""Module for KNX Data Secure."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from copy import copy
from datetime import datetime, timezone
import time

from xknx.cemi import CEMIFrame
from xknx.exceptions import DataSecureException
from xknx.telegram.address import GroupAddress, IndividualAddress
from xknx.telegram.apci import APCI, SecureAPDU

from .data_secure_asdu import (
    SecureData,
    SecurityAlgorithmIdentifier,
    SecurityALService,
    SecurityControlField,
)

# Same timedelta in milliseconds as used in Falcon used for initial sequence_number_sending
# py3.10 backwards compatibility - py3.11 "2018-01-05T00:00:00Z" is supported
_SEQUENCE_NUMBER_INIT_TIMESTAMP = datetime.fromisoformat(
    "2018-01-05T00:00:00+00:00"
).timestamp()


def _initial_sequence_number() -> int:
    """Return an initial sequence number for sending Data Secure Telegrams."""
    return int((time.time() - _SEQUENCE_NUMBER_INIT_TIMESTAMP) * 1000)


class DataSecure:
    """Calss for KNX Data Secure handling."""

    def __init__(
        self,
        *,
        group_key_table: dict[GroupAddress, bytes],
        individual_address_table: dict[IndividualAddress, int],
        last_sequence_number_sending: int | None = None,
    ):
        """Initialize DataSecure class."""
        self.group_key_table = group_key_table
        self._sequence_number_sending = (
            last_sequence_number_sending or _initial_sequence_number()
        )
        # Holds the last valid sequence number for each individual address.
        # Use sequence_number from keyfile as initial value or 0 from senders for all IAs ?
        self._individual_address_table = individual_address_table

        if not 0 < self._sequence_number_sending < 0xFFFFFFFFFFFF:
            _local_time_info = f" Local time not set properly? {datetime.now(timezone.utc).isoformat()}"
            raise DataSecureException(
                f"Initial sequence number out of range: {self._sequence_number_sending}"
                f"{_local_time_info if not last_sequence_number_sending else ''}"
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
        Raise `DataSecureException` if sequence number is invalid or sender is not known.
        """
        try:
            last_valid_sequence_number = self._individual_address_table[source_address]
        except KeyError:
            raise DataSecureException(
                f"Source address not found in Security Individual Address Table: {source_address}"
            )
        if last_valid_sequence_number <= received_sequence_number:
            # TODO: implement and increment Security Failure Log counter (not when equal)
            raise DataSecureException(
                f"Sequence number too low for {source_address}: "
                f"{received_sequence_number} received, {last_valid_sequence_number} last valid"
            )
        try:
            yield
        except DataSecureException:
            # Don't increment sequence number if exception is raised while decrypting
            raise
        self._individual_address_table[source_address] = received_sequence_number

    def received_cemi(self, cemi: CEMIFrame) -> CEMIFrame:
        """Handle received CEMI frame."""
        # Data Secure frame
        if isinstance(cemi.payload, SecureAPDU):
            return self._received_secure_cemi(cemi, cemi.payload)
        # Plain group communication frame
        if isinstance(cemi.dst_addr, GroupAddress):
            if cemi.dst_addr in self.group_key_table:
                raise DataSecureException(
                    f"Discarding frame with plain APDU for secure group address: {cemi}"
                )
            return cemi
        # Plain point-to-point frame
        #   No point to point key table is implemented at the moment as ETS can't even configure this
        #   only way to communicate point-to-point with data secure currently is with tool key
        #   - which we don't have
        return cemi

    def _received_secure_cemi(self, cemi: CEMIFrame, s_apdu: SecureAPDU) -> CEMIFrame:
        """Handle received secured CEMI frame."""
        if s_apdu.scf.service is not SecurityALService.S_A_DATA:
            raise DataSecureException(
                f"Only SecurityALService.S_A_DATA supported {cemi}"
            )
        if s_apdu.scf.system_broadcast or s_apdu.scf.tool_access:
            # TODO: handle incoming responses with tool key of sending device
            # when we can send with tool key
            raise DataSecureException(
                f"System broadcast and tool access not supported {cemi}"
            )

        # Secure group communication frame
        if isinstance(cemi.dst_addr, GroupAddress):
            if not (key := self.group_key_table.get(cemi.dst_addr)):
                raise DataSecureException(
                    f"No key found for group address {cemi.dst_addr} from {cemi.src_addr}"
                )
        # Secure point-to-point frame
        else:
            # TODO: maybe possible to implement this over tool key
            raise DataSecureException(
                f"Secure Point-to-Point communication not supported {cemi}"
            )

        with self.check_sequence_number(
            source_address=cemi.src_addr,
            received_sequence_number=int.from_bytes(
                s_apdu.secured_data.sequence_number_bytes, "big"
            ),
        ):
            _address_fields_raw = cemi.src_addr.to_knx() + cemi.dst_addr.to_knx()
            plain_apdu_raw = s_apdu.secured_data.get_plain_apdu(
                key=key,
                scf=s_apdu.scf,
                address_fields_raw=_address_fields_raw,
                frame_flags=cemi.flags,
                tpci=cemi.tpci,
            )
        decrypted_payload = APCI.from_knx(plain_apdu_raw)
        plain_cemi = copy(cemi)
        plain_cemi.payload = decrypted_payload
        return plain_cemi

    def outgoing_cemi(self, cemi: CEMIFrame) -> CEMIFrame:
        """Handle outgoing CEMI frame. Pass through as plain frame or encrypt."""
        # Outgoing  group communication frame
        if isinstance(cemi.dst_addr, GroupAddress):
            if key := self.group_key_table.get(cemi.dst_addr):
                scf = SecurityControlField(
                    algorithm=SecurityAlgorithmIdentifier.CCM_ENCRYPTION,
                    service=SecurityALService.S_A_DATA,
                    system_broadcast=False,
                    tool_access=False,
                )
                return self._secure_data_cemi(key=key, scf=scf, cemi=cemi)
            return cemi
        # Outgoing secure point-to-point frames are sent plain.
        # Data Secure point-to-point is not supported.
        return cemi

    def _secure_data_cemi(
        self,
        key: bytes,
        scf: SecurityControlField,
        cemi: CEMIFrame,
    ) -> CEMIFrame:
        """Wrap encrypted payload of a plain CEMIFrame in a SecureAPDU."""
        plain_apdu_raw: bytes | bytearray
        if cemi.payload is not None:
            plain_apdu_raw = cemi.payload.to_knx()
        else:
            # TODO: test if this is correct
            plain_apdu_raw = b""  # used ein point-to-point eg. TConnect
        secure_asdu = SecureData.init_from_plain_apdu(
            key=key,
            apdu=plain_apdu_raw,
            scf=scf,
            sequence_number=self.get_sequence_number(),
            address_fields_raw=cemi.src_addr.to_knx() + cemi.dst_addr.to_knx(),
            frame_flags=cemi.flags,
            tpci=cemi.tpci,
        )
        secure_cemi = copy(cemi)
        secure_cemi.payload = SecureAPDU(scf=scf, secured_data=secure_asdu)
        return secure_cemi
