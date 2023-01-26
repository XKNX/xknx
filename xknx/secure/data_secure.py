"""Module for KNX Data Secure."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from xknx.cemi import CEMIFrame
from xknx.exceptions import DataSecureException
from xknx.telegram.address import GroupAddress, IndividualAddress
from xknx.telegram.apci import APCI, SecureAPDU
from xknx.telegram.apci_data_secure import (
    SecurityAlgorithmIdentifier,
    SecurityALService,
    SecurityControlFiled,
)
from xknx.telegram.tpci import TPCI

# TODO: move to other module
from .ip_secure import (
    calculate_message_authentication_code_cbc,
    decrypt_ctr,
    encrypt_data_ctr,
)

APCI_SEC = 0x03F1
# only Address Type (IA / GA) and Extended Frame format are used
B0_AT_FIELD_FLAGS_MASK = 0b10001111


def block_0(
    sequence_number: bytes,
    address_fields_raw: bytes,
    frame_flags: int,
    tpci_int: int,
    payload_length: int,
) -> bytes:
    """Return Block 0 for KNX Data Secure."""
    return (
        sequence_number
        + address_fields_raw
        + b"\x00"
        + (frame_flags & B0_AT_FIELD_FLAGS_MASK).to_bytes(1, "big")
        + ((tpci_int << 10) + APCI_SEC).to_bytes(2, "big")  # TODO: refactor this?
        + b"\x00"
        + payload_length.to_bytes(1, "big")
    )


def counter_0(
    sequence_number: bytes,
    address_fields_raw: bytes,
) -> bytes:
    """Return Block Counter 0 for KNX Data Secure."""
    return sequence_number + address_fields_raw + b"\x00\x00\x00\x00\x01\x00"


class DataSecure:
    """Calss for KNX Data Secure handling."""

    def __init__(
        self,
        sequence_number_sending: int,
        group_key_table: dict[GroupAddress, bytes],
        individual_address_table: dict[IndividualAddress, int],
    ):
        """Initialize DataSecure class."""
        # one sequence_number_sending shall be used for point-to-point and group communication
        self.group_key_table = group_key_table
        self._sequence_number_sending = sequence_number_sending  # TODO: see 2.3.5.13
        self._sequence_number_tool_access = 0  # TODO: how to handle this?
        # holds the last valid sequence number for each individual address
        # use sequence_number from keyfile as initial value or 0 from senders for all GAs ?
        self._individual_address_table = individual_address_table

    def get_sequence_number(self, tool: bool = False) -> bytes:
        """Increment sequence number. Return byte representation of current sequence number."""
        if tool:
            _seq_nr = self._sequence_number_tool_access
            self._sequence_number_tool_access += 1
        else:
            _seq_nr = self._sequence_number_sending
            self._sequence_number_sending += 1
        next_sn = _seq_nr.to_bytes(6, "big")
        # TODO: maybe convert to context manager and only increment if no DataSecureException is raised
        return next_sn

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
            # don't increment sequence number if exception is raised while decrypting
            raise
        self._individual_address_table[source_address] = received_sequence_number

    def received_cemi(self, cemi: CEMIFrame) -> CEMIFrame:
        """Handle received CEMI frame."""
        if isinstance(cemi.payload, SecureAPDU):
            return self._received_secure_cemi(cemi, cemi.payload)
        # check if received plain frame shall be passed to upper layers or dropped
        # plain group communication frame
        if isinstance(cemi.dst_addr, GroupAddress):
            if cemi.dst_addr in self.group_key_table:
                raise DataSecureException(
                    f"Discarding frame with plain APDU for secure group address: {cemi}"
                )
            return cemi

        # plain point-to-point frame
        #   no point to point key table is implemented at the moment as ETS can't even configure this
        #   only way to communicate point-to-point with data secure currently is with tool key
        #   - which we don't have.
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

        # secure group communication frame
        if isinstance(cemi.dst_addr, GroupAddress):
            if not (key := self.group_key_table.get(cemi.dst_addr)):
                raise DataSecureException(
                    f"No key found for group address {cemi.dst_addr} from {cemi.src_addr}"
                )
        # secure point-to-point frame
        else:
            # TODO: maybe possible to implement this over tool key
            raise DataSecureException(
                f"Secure Point-to-Point communication not supported {cemi}"
            )

        secure_data = SecureData.from_knx(s_apdu.secured_data)
        with self.check_sequence_number(
            source_address=cemi.src_addr,
            received_sequence_number=int.from_bytes(
                secure_data.sequence_number_bytes, "big"
            ),
        ):
            _address_fields_raw = cemi.src_addr.to_knx() + cemi.dst_addr.to_knx()
            plain_apdu_raw = secure_data.get_plain_apdu(
                key=key,
                scf=s_apdu.scf,
                address_fields_raw=_address_fields_raw,
                frame_flags=cemi.flags,
                tpci=cemi.tpci,
            )
        decrypted_payload = APCI.from_knx(plain_apdu_raw)
        cemi.payload = decrypted_payload
        return cemi


class SecureData:
    """Class for KNX Data Secure data."""

    def __init__(
        self,
        sequence_number_bytes: bytes,
        secured_apdu: bytes,
        message_authentication_code: bytes,
    ) -> None:
        """Initialize SecureData class."""
        self.sequence_number_bytes = sequence_number_bytes
        self.secured_apdu = secured_apdu
        self.message_authentication_code = message_authentication_code

    @staticmethod
    def init_from_plain_apdu(
        key: bytes,
        apdu: bytes,
        scf: SecurityControlFiled,
        sequence_number: int,
        address_fields_raw: bytes,
        frame_flags: int,
        tpci: TPCI,
    ) -> SecureData:
        """Serialize to KNX raw data."""
        sequence_number_bytes = sequence_number.to_bytes(6, "big")

        if scf.algorithm == SecurityAlgorithmIdentifier.CCM_AUTHENTICATION:
            mac = calculate_message_authentication_code_cbc(
                key=key,
                additional_data=scf.to_knx() + apdu,
                block_0=block_0(
                    sequence_number=sequence_number_bytes,
                    address_fields_raw=address_fields_raw,
                    frame_flags=frame_flags,
                    tpci_int=tpci.to_knx(),
                    payload_length=0,
                ),
            )[:4]
            secured_apdu = apdu
        elif scf.algorithm == SecurityAlgorithmIdentifier.CCM_ENCRYPTION:
            mac_cbc = calculate_message_authentication_code_cbc(
                key=key,
                additional_data=scf.to_knx(),
                payload=apdu,
                block_0=block_0(
                    sequence_number=sequence_number_bytes,
                    address_fields_raw=address_fields_raw,
                    frame_flags=frame_flags,
                    tpci_int=tpci.to_knx(),
                    payload_length=len(apdu),
                ),
            )[:4]
            secured_apdu, mac = encrypt_data_ctr(
                key=key,
                counter_0=counter_0(
                    sequence_number=sequence_number_bytes,
                    address_fields_raw=address_fields_raw,
                ),
                mac_cbc=mac_cbc,
                payload=apdu,
            )
        else:
            raise DataSecureException(f"Unknown secure algorithm {scf.algorithm}")

        return SecureData(
            sequence_number_bytes=sequence_number_bytes,
            secured_apdu=secured_apdu,
            message_authentication_code=mac,  # only 4 bytes are used
        )

    def to_knx(self, algorithm: SecurityAlgorithmIdentifier) -> bytes:
        """Serialize to KNX raw data."""
        return (
            self.sequence_number_bytes
            + self.secured_apdu
            + self.message_authentication_code
        )

    @staticmethod
    def from_knx(raw: bytes) -> SecureData:
        """Parse/deserialize from KNX raw data."""
        return SecureData(
            sequence_number_bytes=raw[:6],
            secured_apdu=raw[6:-4],
            message_authentication_code=raw[-4:],
        )

    def get_plain_apdu(
        self,
        key: bytes,
        scf: SecurityControlFiled,
        address_fields_raw: bytes,
        frame_flags: int,
        tpci: TPCI,
    ) -> bytes:
        """
        Get plain APDU as raw bytes. Decrypted or verified depending on algorithm.

        Sequence number and sender individual address shall already be checked against
        Security Individual Address Table before calling this method.
        """
        if scf.algorithm == SecurityAlgorithmIdentifier.CCM_ENCRYPTION:
            dec_payload, mac_tr = decrypt_ctr(
                key=key,
                counter_0=counter_0(
                    sequence_number=self.sequence_number_bytes,
                    address_fields_raw=address_fields_raw,
                ),
                mac=self.message_authentication_code,
                payload=self.secured_apdu,
            )
            mac_cbc = calculate_message_authentication_code_cbc(
                key=key,
                additional_data=scf.to_knx(),
                payload=dec_payload,
                block_0=block_0(
                    sequence_number=self.sequence_number_bytes,
                    address_fields_raw=address_fields_raw,
                    frame_flags=frame_flags,
                    tpci_int=tpci.to_knx(),
                    payload_length=len(dec_payload),
                ),
            )[:4]
            if mac_cbc != mac_tr:
                raise DataSecureException("Data Secure MAC verification failed")
            return dec_payload

        if scf.algorithm == SecurityAlgorithmIdentifier.CCM_AUTHENTICATION:
            mac = calculate_message_authentication_code_cbc(
                key=key,
                additional_data=scf.to_knx() + self.secured_apdu,
                block_0=block_0(
                    sequence_number=self.sequence_number_bytes,
                    address_fields_raw=address_fields_raw,
                    frame_flags=frame_flags,
                    tpci_int=tpci.to_knx(),
                    payload_length=0,
                ),
            )[:4]
            if mac != self.message_authentication_code:
                raise DataSecureException(
                    "Message authentication code verification failed."
                )
            return self.secured_apdu

        raise DataSecureException(f"Unknown secure algorithm {scf.algorithm}")
