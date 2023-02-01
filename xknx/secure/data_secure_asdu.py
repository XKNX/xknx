"""Class for Data Secure Application layer service data units (ASDUs)."""
from __future__ import annotations

from enum import IntEnum

from xknx.exceptions import DataSecureError
from xknx.telegram.tpci import TPCI

from .security_primitives import (
    calculate_message_authentication_code_cbc,
    decrypt_ctr,
    encrypt_data_ctr,
)

# Secure APCI is 0x03F1 - in block_0 it is used split into 2 octets
_APCI_SEC_HIGH = 0x03
_APCI_SEC_LOW = 0xF1
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
        + bytes(
            (
                0,
                frame_flags & B0_AT_FIELD_FLAGS_MASK,
                (tpci_int << 2) + _APCI_SEC_HIGH,
                _APCI_SEC_LOW,
                0,
                payload_length,
            )
        )
    )


def counter_0(
    sequence_number: bytes,
    address_fields_raw: bytes,
) -> bytes:
    """Return Block Counter 0 for KNX Data Secure."""
    return sequence_number + address_fields_raw + b"\x00\x00\x00\x00\x01\x00"


class SecurityAlgorithmIdentifier(IntEnum):
    """Enum representing the used security algorithm."""

    CCM_AUTHENTICATION = 0b000
    CCM_ENCRYPTION = 0b001


class SecurityALService(IntEnum):
    """Enum representing the used security application layer service."""

    S_A_DATA = 0b000
    S_A_SYNC_REQ = 0b001
    S_A_SYNC_RES = 0b011


class SecurityControlField:
    """Class for KNX Data Secure Security Control Field (SCF)."""

    def __init__(
        self,
        tool_access: bool,
        algorithm: SecurityAlgorithmIdentifier,
        system_broadcast: bool,
        service: SecurityALService,
    ) -> None:
        """Initialize SecurityControlField class."""
        self.tool_access = tool_access
        self.algorithm = algorithm
        self.system_broadcast = system_broadcast
        self.service = service

    @staticmethod
    def from_knx(raw: int) -> SecurityControlField:
        """Parse/deserialize from KNX raw data."""
        tool_access = bool(raw & 0b10000000)
        sai = SecurityAlgorithmIdentifier(raw >> 4 & 0b111)
        system_broadcast = bool(raw & 0b1000)
        s_al_service = SecurityALService(raw & 0b111)

        return SecurityControlField(
            tool_access=tool_access,
            algorithm=sai,
            system_broadcast=system_broadcast,
            service=s_al_service,
        )

    def to_knx(self) -> bytes:
        """Serialize to KNX raw data."""
        raw = 0
        raw |= self.tool_access << 7
        raw |= self.algorithm << 4
        raw |= self.system_broadcast << 3
        raw |= self.service
        return raw.to_bytes(1, "big")

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f"<SecurityControlField tool_access={self.tool_access} "
            f"algorithm={self.algorithm.name} "
            f"system_broadcast={self.system_broadcast} "
            f"service={self.service.name} />"
        )


class SecureData:
    """Class for KNX Data Secure ASDU for S-A_Data-service."""

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

    def __len__(self) -> int:
        """Return length of KNX Data Secure ASDU."""
        return 10 + len(self.secured_apdu)  # 10 = 6 bytes sequence number + 4 bytes MAC

    @staticmethod
    def init_from_plain_apdu(
        key: bytes,
        apdu: bytes,
        scf: SecurityControlField,
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
            raise DataSecureError(f"Unknown secure algorithm {scf.algorithm}")

        return SecureData(
            sequence_number_bytes=sequence_number_bytes,
            secured_apdu=secured_apdu,
            message_authentication_code=mac,  # only 4 bytes are used
        )

    def to_knx(self) -> bytes:
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
        scf: SecurityControlField,
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
                raise DataSecureError("Data Secure MAC verification failed")
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
                raise DataSecureError("Data Secure MAC verification failed.")
            return self.secured_apdu

        raise DataSecureError(f"Unknown secure algorithm {scf.algorithm}")

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<SecureData "
            f"sequence_number={int.from_bytes(self.sequence_number_bytes, 'big')} "
            f'secured_apdu="{self.secured_apdu.hex()}" '
            f'message_authentication_code="{self.message_authentication_code.hex()}" />'
        )
