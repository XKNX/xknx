"""Utilities for KNX Secure."""
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def sha256_hash(data: bytes) -> bytes:
    """Calculate SHA256 hash of data."""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()


def decrypt_aes128cbc(
    encrypted_data: bytes, key: bytes, initialization_vector: bytes
) -> bytes:
    """Decrypt data with AES 128 CBC."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(initialization_vector))
    decryptor = cipher.decryptor()  # type: ignore[no-untyped-call]
    return bytes(decryptor.update(encrypted_data) + decryptor.finalize())


def hash_keyring_password(password: bytes) -> bytes:
    """Hash a given keyring password."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=16,
        salt=b"1.keyring.ets.knx.org",
        iterations=65_536,
    )

    return kdf.derive(password)


def extract_password(data: bytes) -> str:
    """Extract the password."""
    if len(data) == 0:
        return ""

    length: int = data[len(data) - 1] & 0xFF
    res: bytes = data[8 : len(data) - length]
    return res.decode("utf-8")
