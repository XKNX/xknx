"""Tests for the shared memory procedure helpers."""

import binascii

from xknx.management.procedures.device._memory import (
    _CRC16_CCITT_KNX_INIT,
    memory_extended_write_crc,
)


def test_crc16_ccitt_check_value() -> None:
    """
    Test the CRC16-CCITT variant matches KNX's own check value.

    KNX v01.10.01 - Resources 03.05.01 - §4.2.27.1.2: "The correct
    CRC16-CCITT of the string '123456789' is E5CCh".
    """
    assert binascii.crc_hqx(b"123456789", _CRC16_CCITT_KNX_INIT) == 0xE5CC


def test_memory_extended_write_crc() -> None:
    """
    Test the CRC covers count + 24 bit address + data, big-endian.

    BB45h was computed with calimero-core's ManagementClientImpl.crc16Ccitt()
    algorithm over 03 100000 010203.
    """
    assert memory_extended_write_crc(0x100000, b"\x01\x02\x03") == b"\xbb\x45"
