"""Tests for secure util primitives."""

import pytest

from xknx.secure.util import byte_pad, bytes_xor, sha256_hash


@pytest.mark.parametrize(
    ("value_a", "value_b", "result"),
    [
        (
            "01010101",
            "10101010",
            "11111111",
        ),
        (
            "000011111111111111110000",
            "000000000000111111110000",
            "000011111111000000000000",
        ),
        (
            "000000000000000000000000000000001",
            "000011111111111111110000101010101",
            "000011111111111111110000101010100",
        ),
    ],
)
def test_byte_xor(
    value_a: tuple[str, str, str],
    value_b: tuple[str, str, str],
    result: tuple[str, str, str],
) -> None:
    """Test byte xor."""
    len_a = (len(value_a) + 7) // 8
    len_b = (len(value_b) + 7) // 8
    len_res = max(len_a, len_b)
    assert bytes_xor(
        int(value_a, 2).to_bytes(len_a, "big"),
        int(value_b, 2).to_bytes(len_b, "big"),
    ) == int(result, 2).to_bytes(len_res, "big")


def test_byte_xor_error() -> None:
    """Test byte xor error."""
    with pytest.raises(ValueError):
        bytes_xor(bytes([1]), bytes([0, 1]))


@pytest.mark.parametrize(
    ("block_size", "data", "result"),
    [
        (4, bytes([23]), bytes([23, 0, 0, 0])),
        (4, bytes([1, 23, 0, 0]), bytes([1, 23, 0, 0])),
        (16, bytes([123]), bytes([123, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])),
        (16, bytes(16), bytes(16)),
        (16, bytes(17), bytes(32)),
        (16, bytes(32), bytes(32)),
        (16, bytes(47), bytes(48)),
    ],
)
def test_byte_pad(block_size: int, data: bytes, result: bytes) -> None:
    """Test byte pad."""
    assert byte_pad(data=data, block_size=block_size) == result


def test_sha256_hash() -> None:
    """Test sha256 hash."""
    # Data from SessionResponse example in KNX specification AN159v06
    assert sha256_hash(
        bytes.fromhex(
            "d8 01 52 52 17 61 8f 0d a9 0a 4f f2 21 48 ae e0"
            "ff 4c 19 b4 30 e8 08 12 23 ff e9 9c 81 a9 8b 05"
        )
    ) == bytes.fromhex(
        "28 94 26 c2 91 25 35 ba 98 27 9a 4d 18 43 c4 87"
        "7f 6d 2d c3 7e 40 dc 4b eb fe 40 31 d4 73 3b 30"
    )
