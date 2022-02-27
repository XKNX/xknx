"""Utilities for KNX Secure."""
from cryptography.hazmat.primitives import hashes


def sha256_hash(data: bytes) -> bytes:
    """Calculate SHA256 hash of data."""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()
