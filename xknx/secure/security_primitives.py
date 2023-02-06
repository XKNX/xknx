"""Encryption and Decryption functions for KNX Secure."""
from __future__ import annotations

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .util import byte_pad


def calculate_message_authentication_code_cbc(
    key: bytes,
    additional_data: bytes,
    payload: bytes = b"",
    block_0: bytes = bytes(16),
) -> bytes:
    """Calculate the message authentication code (MAC) for a message with AES-CBC."""
    blocks = (
        block_0 + len(additional_data).to_bytes(2, "big") + additional_data + payload
    )
    y_cipher = Cipher(algorithms.AES(key), modes.CBC(bytes(16)))
    y_encryptor = y_cipher.encryptor()
    y_blocks = (
        y_encryptor.update(byte_pad(blocks, block_size=16)) + y_encryptor.finalize()
    )
    # only calculate, no ctr encryption
    return y_blocks[-16:]


def decrypt_ctr(
    key: bytes,
    counter_0: bytes,
    mac: bytes,
    payload: bytes = b"",
) -> tuple[bytes, bytes]:
    """
    Decrypt data from SecureWrapper.

    MAC will be decoded first with counter 0.
    Returns a tuple of (KNX/IP frame bytes, MAC TR for verification).
    """
    cipher = Cipher(algorithms.AES(key), modes.CTR(counter_0))
    decryptor = cipher.decryptor()
    mac_tr = decryptor.update(mac)  # MAC is encrypted with counter 0
    decrypted_data = decryptor.update(payload) + decryptor.finalize()

    return (decrypted_data, mac_tr)


def encrypt_data_ctr(
    key: bytes,
    counter_0: bytes,
    mac_cbc: bytes,
    payload: bytes = b"",
) -> tuple[bytes, bytes]:
    """
    Encrypt data with AES-CTR.

    Payload is expected a full Plain KNX/IP frame with header.
    MAC shall be encrypted with counter 0, KNXnet/IP frame with incremented counters.
    Returns a tuple of encrypted data (if there is any) and encrypted MAC.
    """
    s_cipher = Cipher(algorithms.AES(key), modes.CTR(counter_0))
    s_encryptor = s_cipher.encryptor()
    mac = s_encryptor.update(mac_cbc)
    encrypted_data = s_encryptor.update(payload) + s_encryptor.finalize()
    return (encrypted_data, mac)


def derive_device_authentication_password(device_authentication_password: str) -> bytes:
    """Derive device authentication password."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=16,
        salt=b"device-authentication-code.1.secure.ip.knx.org",
        iterations=65536,
    )
    return kdf.derive(device_authentication_password.encode("latin-1"))


def derive_user_password(password_string: str) -> bytes:
    """Derive user password."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=16,
        salt=b"user-password.1.secure.ip.knx.org",
        iterations=65536,
    )
    return kdf.derive(password_string.encode("latin-1"))


def generate_ecdh_key_pair() -> tuple[X25519PrivateKey, bytes]:
    """
    Generate an ECDH key pair.

    Return the private key and the raw bytes of the public key.
    """
    private_key = X25519PrivateKey.generate()
    public_key_raw = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return private_key, public_key_raw
