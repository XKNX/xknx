"""Tests for the Factory Default Setup Key (FDSK) code printed on a device."""

import pytest

from xknx.exceptions import InvalidSecureConfiguration
from xknx.secure import FactoryDefaultSetupKey

SERIAL_NUMBER = bytes.fromhex("00fa12345678")
KEY = bytes(range(16))
CODE = "AD5BEN-CWPAAA-CAQDAQ-CQMBYI-BEFAWD-ANBYH6"


def test_to_code() -> None:
    """The code has six groups of six base32 characters."""
    assert (
        FactoryDefaultSetupKey(serial_number=SERIAL_NUMBER, key=KEY).to_code() == CODE
    )


@pytest.mark.parametrize(
    "code",
    [
        CODE,
        CODE.replace("-", ""),
        CODE.lower(),
        f"  {CODE.replace('-', ' ')} ",
        # 0, 1 and 8 are not in the base32 alphabet: read as O, L and B
        CODE.replace("B", "8"),
    ],
)
def test_from_code(code: str) -> None:
    """Separators, case and mistaken digits don't matter."""
    fdsk = FactoryDefaultSetupKey.from_code(code)
    assert fdsk.serial_number == SERIAL_NUMBER
    assert fdsk.key == KEY


def test_round_trip() -> None:
    """Every code created is read back."""
    for value in range(256):
        fdsk = FactoryDefaultSetupKey(
            serial_number=bytes((value,)) * 6, key=bytes((255 - value,)) * 16
        )
        assert FactoryDefaultSetupKey.from_code(fdsk.to_code()) == fdsk


@pytest.mark.parametrize(
    ("code", "message"),
    [
        (CODE[:-1], "36 characters"),
        (CODE + "A", "36 characters"),
        # one changed character of the key
        (CODE.replace("CAQDAQ", "CAQDAR"), "CRC mismatch"),
        (CODE.replace("A", "!", 1), "36 characters"),
        # not in the alphabet of the code (A-Z, 2-7)
        (CODE.replace("A", "9", 1), "Invalid FDSK code"),
        (CODE.replace("A", "Ä", 1), "Invalid FDSK code"),
    ],
)
def test_invalid_code(code: str, message: str) -> None:
    """A code of the wrong length, with a wrong character or CRC is rejected."""
    with pytest.raises(InvalidSecureConfiguration, match=message):
        FactoryDefaultSetupKey.from_code(code)


def test_invalid_lengths() -> None:
    """KNX Serial Number and FDSK have a fixed length."""
    with pytest.raises(InvalidSecureConfiguration):
        FactoryDefaultSetupKey(serial_number=bytes(5), key=KEY)
    with pytest.raises(InvalidSecureConfiguration):
        FactoryDefaultSetupKey(serial_number=SERIAL_NUMBER, key=bytes(15))
