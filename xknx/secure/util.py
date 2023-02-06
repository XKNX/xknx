"""Utilities for KNX Secure."""
from cryptography.hazmat.primitives import hashes


def bytes_xor(a: bytes, b: bytes) -> bytes:  # pylint: disable=invalid-name
    """
    XOR two bytes values.

    Different lengths raise ValueError.
    """
    if len(a) != len(b):
        raise ValueError("Length of a and b must be equal.")
    return (int.from_bytes(a, "big") ^ int.from_bytes(b, "big")).to_bytes(len(a), "big")


def byte_pad(data: bytes, block_size: int) -> bytes:
    """Pad data with 0x00 until its length is a multiple of block_size."""
    if remainder := len(data) % block_size:
        return data + bytes(block_size - remainder)
    return data


def sha256_hash(data: bytes) -> bytes:
    """Calculate SHA256 hash of data."""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()
