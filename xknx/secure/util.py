"""Utilities for KNX Secure."""
from cryptography.hazmat.primitives import hashes


def bytes_xor(a: bytes, b: bytes) -> bytes:  # pylint: disable=invalid-name
    """XOR two bytes values."""
    return (int.from_bytes(a, "big") ^ int.from_bytes(b, "big")).to_bytes(len(a), "big")


def byte_pad(data: bytes, block_size: int) -> bytes:
    """Padd data with 0x00 until its length is a multiple of block_size."""
    padding = bytes(block_size - (len(data) % block_size))
    return data + padding


def sha256_hash(data: bytes) -> bytes:
    """Calculate SHA256 hash of data."""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()
