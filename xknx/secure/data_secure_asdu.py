"""Class for Data Secure Application layer service data units (ASDUs)."""

from __future__ import annotations

from enum import IntEnum

from xknx.cemi.flags import CEMIAddressType, CEMIFrameFormat
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
# Length of the Sequence Number, KNX Serial Number, Challenge and Random fields.
_SEQUENCE_NUMBER_LENGTH = 6
_MAC_LENGTH = 4


def block_0(
    sequence_number: bytes,
    address_fields_raw: bytes,
    address_type: CEMIAddressType,
    frame_format: CEMIFrameFormat,
    tpci_int: int,
    payload_length: int,
) -> bytes:
    """Return Block 0 for KNX Data Secure."""
    # Of the two control field octets only Ctrl2 is protected, and only as
    # `A000EEEEb` - A the Address Type, EEEEb the Extended Frame Format if
    # L_Data_Extended frames are used and 0000b otherwise. Priority, repeat flag,
    # hop count and the Frame Type stay unprotected and may change on the way -
    # KNX v02.01.01 - Application Layer 03.03.07 - §5.1.3.2 Figure 100 and NOTE 16.
    # `tpci_int` is the TPCI octet as sent (`TPCI.to_knx()`): its upper 6 bits are the
    # TPCI and its lower 2 bits carry the upper 2 bits of the Secure APCI, e.g. 43h for
    # a T_Data_Connected with sequence number 0 -
    # KNX v02.01.01 - Application Layer 03.03.07 - Annex C.1.3.
    return (
        sequence_number
        + address_fields_raw
        + bytes(
            (
                0,
                address_type.to_knx() | frame_format,
                tpci_int | _APCI_SEC_HIGH,
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


def _encrypt(
    key: bytes,
    nonce: bytes,
    additional_data: bytes,
    payload: bytes,
    address_fields_raw: bytes,
    address_type: CEMIAddressType,
    frame_format: CEMIFrameFormat,
    tpci: TPCI,
) -> tuple[bytes, bytes]:
    """
    Secure `payload` with authentication and confidentiality; return (cipher, MAC).

    `nonce` takes the place of the Sequence Number in B0 and Ctr0 -
    KNX v02.01.01 - Application Layer 03.03.07 - §5.1.3.5.
    """
    mac_cbc = calculate_message_authentication_code_cbc(
        key=key,
        additional_data=additional_data,
        payload=payload,
        block_0=block_0(
            sequence_number=nonce,
            address_fields_raw=address_fields_raw,
            address_type=address_type,
            frame_format=frame_format,
            tpci_int=tpci.to_knx(),
            payload_length=len(payload),
        ),
    )[:_MAC_LENGTH]
    return encrypt_data_ctr(
        key=key,
        counter_0=counter_0(
            sequence_number=nonce, address_fields_raw=address_fields_raw
        ),
        mac_cbc=mac_cbc,
        payload=payload,
    )


def _decrypt(
    key: bytes,
    nonce: bytes,
    additional_data: bytes,
    cipher: bytes,
    mac: bytes,
    address_fields_raw: bytes,
    address_type: CEMIAddressType,
    frame_format: CEMIFrameFormat,
    tpci: TPCI,
) -> bytes:
    """Decrypt `cipher` and verify its MAC (see `_encrypt`)."""
    plain, mac_tr = decrypt_ctr(
        key=key,
        counter_0=counter_0(
            sequence_number=nonce, address_fields_raw=address_fields_raw
        ),
        mac=mac,
        payload=cipher,
    )
    mac_cbc = calculate_message_authentication_code_cbc(
        key=key,
        additional_data=additional_data,
        payload=plain,
        block_0=block_0(
            sequence_number=nonce,
            address_fields_raw=address_fields_raw,
            address_type=address_type,
            frame_format=frame_format,
            tpci_int=tpci.to_knx(),
            payload_length=len(plain),
        ),
    )[:_MAC_LENGTH]
    if mac_cbc != mac_tr:
        raise DataSecureError("Data Secure MAC verification failed")
    return plain


class SecurityAlgorithmIdentifier(IntEnum):
    """Enum representing the used security algorithm."""

    CCM_AUTHENTICATION = 0b000
    CCM_ENCRYPTION = 0b001


class SecurityALService(IntEnum):
    """Enum representing the used security application layer service."""

    # KNX v02.01.01 - Application Layer 03.03.07 - §5.1.1 Table 5
    S_A_DATA = 0b000
    S_A_SYNC_REQ = 0b010
    S_A_SYNC_RES = 0b011


class SecurityControlField:
    """Class for KNX Data Secure Security Control Field (SCF)."""

    __slots__ = ("algorithm", "service", "system_broadcast", "tool_access")

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

    __slots__ = ("message_authentication_code", "secured_apdu", "sequence_number_bytes")

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
        apdu: bytes | bytearray,
        scf: SecurityControlField,
        sequence_number: int,
        address_fields_raw: bytes,
        address_type: CEMIAddressType,
        frame_format: CEMIFrameFormat,
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
                    address_type=address_type,
                    frame_format=frame_format,
                    tpci_int=tpci.to_knx(),
                    payload_length=0,
                ),
            )[:4]
            secured_apdu = bytes(apdu)
        elif scf.algorithm == SecurityAlgorithmIdentifier.CCM_ENCRYPTION:
            mac_cbc = calculate_message_authentication_code_cbc(
                key=key,
                additional_data=scf.to_knx(),
                payload=apdu,
                block_0=block_0(
                    sequence_number=sequence_number_bytes,
                    address_fields_raw=address_fields_raw,
                    address_type=address_type,
                    frame_format=frame_format,
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
        address_type: CEMIAddressType,
        frame_format: CEMIFrameFormat,
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
                    address_type=address_type,
                    frame_format=frame_format,
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
                    address_type=address_type,
                    frame_format=frame_format,
                    tpci_int=tpci.to_knx(),
                    payload_length=0,
                ),
            )[:4]
            if mac != self.message_authentication_code:
                raise DataSecureError("Data Secure MAC verification failed.")
            return self.secured_apdu

        raise DataSecureError(f"Unknown secure algorithm {scf.algorithm}")

    @staticmethod
    def init_sync_request(
        key: bytes,
        scf: SecurityControlField,
        sequence_number: int,
        serial_number: bytes,
        challenge: bytes,
        address_fields_raw: bytes,
        address_type: CEMIAddressType,
        frame_format: CEMIFrameFormat,
        tpci: TPCI,
    ) -> SecureData:
        """
        Build the Secure Data of an S-A_Sync_Req-PDU.

        SeqNr_local | KNX Serial Number (plain) | Challenge (encrypted) | MAC, with
        A = SCF | KNX Serial Number and P = Challenge -
        KNX v02.01.01 - Application Layer 03.03.07 - §5.3.2 Figure 109.
        """
        if len(serial_number) != _SEQUENCE_NUMBER_LENGTH:
            raise DataSecureError(f"Invalid KNX Serial Number: {serial_number.hex()}")
        if len(challenge) != _SEQUENCE_NUMBER_LENGTH:
            raise DataSecureError(f"Invalid challenge: {challenge.hex()}")
        sequence_number_bytes = sequence_number.to_bytes(_SEQUENCE_NUMBER_LENGTH, "big")
        cipher, mac = _encrypt(
            key=key,
            nonce=sequence_number_bytes,
            additional_data=scf.to_knx() + serial_number,
            payload=challenge,
            address_fields_raw=address_fields_raw,
            address_type=address_type,
            frame_format=frame_format,
            tpci=tpci,
        )
        return SecureData(
            sequence_number_bytes=sequence_number_bytes,
            secured_apdu=serial_number + cipher,
            message_authentication_code=mac,
        )

    def get_sync_request_challenge(
        self,
        key: bytes,
        scf: SecurityControlField,
        address_fields_raw: bytes,
        address_type: CEMIAddressType,
        frame_format: CEMIFrameFormat,
        tpci: TPCI,
    ) -> tuple[bytes, bytes]:
        """Verify an S-A_Sync_Req-PDU; return its (KNX Serial Number, Challenge)."""
        if len(self.secured_apdu) != 2 * _SEQUENCE_NUMBER_LENGTH:
            raise DataSecureError("Invalid length of S-A_Sync_Req-PDU")
        serial_number = self.secured_apdu[:_SEQUENCE_NUMBER_LENGTH]
        challenge = _decrypt(
            key=key,
            nonce=self.sequence_number_bytes,
            additional_data=scf.to_knx() + serial_number,
            cipher=self.secured_apdu[_SEQUENCE_NUMBER_LENGTH:],
            mac=self.message_authentication_code,
            address_fields_raw=address_fields_raw,
            address_type=address_type,
            frame_format=frame_format,
            tpci=tpci,
        )
        return serial_number, challenge

    @staticmethod
    def init_sync_response(
        key: bytes,
        scf: SecurityControlField,
        challenge: bytes,
        random: bytes,
        sequence_number_remote: int,
        sequence_number_local: int,
        address_fields_raw: bytes,
        address_type: CEMIAddressType,
        frame_format: CEMIFrameFormat,
        tpci: TPCI,
    ) -> SecureData:
        """
        Build the Secure Data of an S-A_Sync_Res-PDU.

        Challenge XOR Random (plain) | SeqNr_remote | SeqNr_local (encrypted) | MAC, with
        A = SCF, P = SeqNr_remote | SeqNr_local and Random in place of the Sequence Number
        in B0 and Ctr0 - KNX v02.01.01 - Application Layer 03.03.07 - §5.3.2 Figure 110.
        """
        cipher, mac = _encrypt(
            key=key,
            nonce=random,
            additional_data=scf.to_knx(),
            payload=sequence_number_remote.to_bytes(_SEQUENCE_NUMBER_LENGTH, "big")
            + sequence_number_local.to_bytes(_SEQUENCE_NUMBER_LENGTH, "big"),
            address_fields_raw=address_fields_raw,
            address_type=address_type,
            frame_format=frame_format,
            tpci=tpci,
        )
        return SecureData(
            sequence_number_bytes=bytes(
                a ^ b for a, b in zip(challenge, random, strict=True)
            ),
            secured_apdu=cipher,
            message_authentication_code=mac,
        )

    def get_sync_response_sequence_numbers(
        self,
        key: bytes,
        scf: SecurityControlField,
        challenge: bytes,
        address_fields_raw: bytes,
        address_type: CEMIAddressType,
        frame_format: CEMIFrameFormat,
        tpci: TPCI,
    ) -> tuple[int, int]:
        """
        Verify an S-A_Sync_Res-PDU answering `challenge`; return (SeqNr_remote, SeqNr_local).

        Random is recovered from the field Challenge XOR Random with the own Challenge -
        KNX v02.01.01 - Application Layer 03.03.07 - §5.3.2.
        """
        if len(self.secured_apdu) != 2 * _SEQUENCE_NUMBER_LENGTH:
            raise DataSecureError("Invalid length of S-A_Sync_Res-PDU")
        random = bytes(
            a ^ b for a, b in zip(self.sequence_number_bytes, challenge, strict=True)
        )
        plain = _decrypt(
            key=key,
            nonce=random,
            additional_data=scf.to_knx(),
            cipher=self.secured_apdu,
            mac=self.message_authentication_code,
            address_fields_raw=address_fields_raw,
            address_type=address_type,
            frame_format=frame_format,
            tpci=tpci,
        )
        return (
            int.from_bytes(plain[:_SEQUENCE_NUMBER_LENGTH], "big"),
            int.from_bytes(plain[_SEQUENCE_NUMBER_LENGTH:], "big"),
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<SecureData "
            f"sequence_number={int.from_bytes(self.sequence_number_bytes, 'big')} "
            f'secured_apdu="{self.secured_apdu.hex()}" '
            f'message_authentication_code="{self.message_authentication_code.hex()}" />'
        )
