"""
Factory Default Setup Key (FDSK) of a KNX Data Secure device, as printed on the device.

The FDSK is the Tool Key of a device in its delivery state; it "may be printed on the
device's wrapping or on a paper note that is shipped with the device" -
KNX v01.10.01 - Resources 03.05.01 - §6.1.1.

The printed code - also called device certificate - has 36 characters, written in six
groups of six separated by "-". It is the base32 text (RFC 4648, without padding) of
the device's KNX Serial Number (6 octets), the FDSK (16 octets) and a 4 bit CRC over
both (polynomial x^4 + x + 1) in the upper half of a last octet. The KNX Standard
documents don't specify this encoding.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from typing import Final

from xknx.exceptions import InvalidSecureConfiguration

_CODE_LENGTH: Final = 36
_GROUP_LENGTH: Final = 6
_SERIAL_NUMBER_LENGTH: Final = 6
_KEY_LENGTH: Final = 16
# CRC-4 with polynomial x^4 + x + 1, processed a nibble at a time
_CRC4_TABLE: Final = (
    0x0, 0x3, 0x6, 0x5, 0xC, 0xF, 0xA, 0x9, 0xB, 0x8, 0xD, 0xE, 0x7, 0x4, 0x1, 0x2,
)  # fmt: skip
# base32 has no 0, 1 and 8 - read them as the letters they are mistaken for
_MISTYPED: Final = str.maketrans({"0": "O", "1": "L", "8": "B"})


def _crc4(data: bytes) -> int:
    """Return the CRC-4 of `data`."""
    crc = 0
    for octet in data:
        crc = _CRC4_TABLE[crc ^ (octet >> 4)]
        crc = _CRC4_TABLE[crc ^ (octet & 0x0F)]
    return crc


@dataclass(frozen=True, slots=True)
class FactoryDefaultSetupKey:
    """The KNX Serial Number and the FDSK of a device."""

    serial_number: bytes
    key: bytes

    def __post_init__(self) -> None:
        """Validate the lengths."""
        if len(self.serial_number) != _SERIAL_NUMBER_LENGTH:
            raise InvalidSecureConfiguration(
                f"A KNX Serial Number has {_SERIAL_NUMBER_LENGTH} octets, "
                f"got {len(self.serial_number)}"
            )
        if len(self.key) != _KEY_LENGTH:
            raise InvalidSecureConfiguration(
                f"An FDSK has {_KEY_LENGTH} octets, got {len(self.key)}"
            )

    @classmethod
    def from_code(cls, code: str) -> FactoryDefaultSetupKey:
        """
        Parse the code printed on a device.

        Separators and white space are ignored, letters may be lower case, and the
        digits 0, 1 and 8 are read as the letters O, L and B. Raise
        `InvalidSecureConfiguration` for a code of the wrong length or with a wrong CRC.
        """
        text = "".join(char for char in code.upper() if char.isalnum()).translate(
            _MISTYPED
        )
        if len(text) != _CODE_LENGTH:
            raise InvalidSecureConfiguration(
                f"An FDSK code has {_CODE_LENGTH} characters, got {len(text)}"
            )
        try:
            # 36 characters carry 180 bits: 22 octets, the CRC nibble and 4 zero bits
            data = base64.b32decode(text + "AAAA")
        except binascii.Error as exc:
            raise InvalidSecureConfiguration(f"Invalid FDSK code: {exc}") from exc
        serial_number = data[:_SERIAL_NUMBER_LENGTH]
        key = data[_SERIAL_NUMBER_LENGTH : _SERIAL_NUMBER_LENGTH + _KEY_LENGTH]
        if _crc4(serial_number + key) != data[22] >> 4:
            raise InvalidSecureConfiguration("Invalid FDSK code: CRC mismatch")
        return cls(serial_number=serial_number, key=key)

    def to_code(self) -> str:
        """Return the code as printed on a device."""
        data = (
            self.serial_number
            + self.key
            + bytes((_crc4(self.serial_number + self.key) << 4,))
        )
        text = base64.b32encode(data).decode("ascii")[:_CODE_LENGTH]
        return "-".join(
            text[i : i + _GROUP_LENGTH] for i in range(0, _CODE_LENGTH, _GROUP_LENGTH)
        )
