"""Cryptographical calculations of KNX specification example frames."""
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def bytes_xor(a: bytes, b: bytes) -> bytes:  # pylint: disable=invalid-name
    """XOR two bytes values."""
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


def calculate_message_authentication_code_cbc(
    key: bytes,
    additional_data: bytes,
    payload: bytes = b"",
    block_0: bytes = bytes(16),
    # counter_0: bytes = bytes(16),
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
    # s_cipher = Cipher(algorithms.AES(key), modes.CTR(counter_0))
    # s_encryptor = s_cipher.encryptor()
    # return s_encryptor.update(y_blocks[-16:]) + s_encryptor.finalize()


def encrypt_data_ctr(
    key: bytes,
    mac_cbc: bytes,
    payload: bytes = b"",
    counter_0: bytes = bytes(16),
) -> bytes:
    """
    Encrypt data with AES-CTR.

    Payload is optional; expected plain KNX/IP frame bytes.
    MAC shall be encrypted with counter 0, KNXnet/IP frame with incremented counters.
    Encrypted MAC is appended to the end of encrypted payload data (if there is any).
    """
    s_cipher = Cipher(algorithms.AES(key), modes.CTR(counter_0))
    s_encryptor = s_cipher.encryptor()
    mac = s_encryptor.update(mac_cbc)
    data = s_encryptor.update(payload) + s_encryptor.finalize()
    return data + mac


def decrypt_ctr(
    session_key: bytes,
    payload: bytes,
    counter_0: bytes = bytes(16),
) -> bytes:
    """
    Decrypt data from SecureWrapper.

    MAC is expected to be the last 16 octets of the payload. This will be sliced and
    decoded first with counter 0.
    Returns a tuple of (KNX/IP frame bytes, MAC TR for verification).
    """
    cipher = Cipher(algorithms.AES(session_key), modes.CTR(counter_0))
    decryptor = cipher.decryptor()
    mac_tr = decryptor.update(payload[-16:])  # MAC is encrypted with counter 0
    decrypted_data = decryptor.update(payload[:-16]) + decryptor.finalize()

    return (decrypted_data, mac_tr)


def calculate_wrapper(
    session_key: bytes,
    encapsulated_frame: bytes,
    secure_session_id: bytes = bytes.fromhex("00 01"),
    sequence_number: bytes = bytes.fromhex("00 00 00 00 00 00"),
    serial_number: bytes = bytes.fromhex("00 fa 12 34 56 78"),
    message_tag: bytes = bytes.fromhex("af fe"),
) -> bytes:
    """Calculate the payload and mac for a secure wrapper."""
    print("# SecureWrapper")

    total_length = (
        6  # KNX/IP Header
        + len(secure_session_id)
        + len(sequence_number)
        + len(serial_number)
        + len(message_tag)
        + len(encapsulated_frame)
        + 16  # MAC
    )
    wrapper_header = bytes.fromhex("06 10 09 50") + total_length.to_bytes(2, "big")

    a_data = wrapper_header + secure_session_id
    p_data = encapsulated_frame
    q_payload_length = len(p_data).to_bytes(2, "big")

    b_0_secure_wrapper = (
        sequence_number + serial_number + message_tag + q_payload_length
    )
    ctr_0_secure_wrapper = (
        sequence_number + serial_number + message_tag + bytes.fromhex("ff") + bytes(1)
    )  # last octet is the counter to increment by 1 each step

    mac_cbc = calculate_message_authentication_code_cbc(
        session_key,
        additional_data=a_data,
        payload=p_data,
        block_0=b_0_secure_wrapper,
    )
    encrypted_data = encrypt_data_ctr(
        session_key,
        mac_cbc=mac_cbc,
        payload=p_data,
        counter_0=ctr_0_secure_wrapper,
    )

    # encrypted data
    # ctr_1_secure_wrapper = (int.from_bytes(ctr_0_secure_wrapper, "big") + 1).to_bytes(
    #     16, "big"
    # )
    # cipher = Cipher(algorithms.AES(session_key), modes.CTR(ctr_1_secure_wrapper))
    # encryptor = cipher.encryptor()
    # enc_frame = encryptor.update(p_data) + encryptor.finalize()

    print(f"encrypted_data: {encrypted_data[16:].hex()}")

    dec_frame, mac_tr = decrypt_ctr(
        session_key,
        payload=encrypted_data,
        counter_0=ctr_0_secure_wrapper,
    )
    assert dec_frame == p_data
    assert mac_tr == mac_cbc  # verification of MAC

    return encrypted_data


def main():
    """Recalculate KNX specification example frames."""
    ################
    # SessionRequest
    ################
    print("# SessionRequest")
    client_private_key = X25519PrivateKey.from_private_bytes(
        bytes.fromhex(
            "b8 fa bd 62 66 5d 8b 9e 8a 9d 8b 1f 4b ca 42 c8 c2 78 9a 61 10 f5 0e 9d d7 85 b3 ed e8 83 f3 78"
        )
    )
    client_public_key_raw = client_private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )  # append to SessionRequest (15-46)
    print(f"Public key: {client_public_key_raw.hex()}")

    #################
    # SessionResponse
    #################
    print("# SessionResponse")
    peer_public_key = X25519PublicKey.from_public_bytes(
        bytes.fromhex(
            "bd f0 99 90 99 23 14 3e f0 a5 de 0b 3b e3 68 7b c5 bd 3c f5 f9 e6 f9 01 69 9c d8 70 ec 1f f8 24"
        )
    )
    pub_keys_xor = bytes_xor(
        client_public_key_raw,
        peer_public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ),
    )

    peer_device_authentication_password = "trustme"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=16,
        salt=b"device-authentication-code.1.secure.ip.knx.org",
        iterations=65536,
    )
    # TODO: is encoding "latin-1" correct? (also used for device names in DIBs)
    peer_device_authentication_code = kdf.derive(
        peer_device_authentication_password.encode("latin-1")
    )
    assert peer_device_authentication_code == bytes.fromhex(
        "e1 58 e4 01 20 47 bd 6c c4 1a af bc 5c 04 c1 fc"
    )

    _a_data = bytes.fromhex(
        "06 10 09 52 00 38 00 01 b7 52 be 24 64 59 26 0f 6b 0c 48 01 fb d5 a6 75 99 f8 3b 40 57 b3 ef 1e 79 e4 69 ac 17 23 4e 15"
    )
    ctr_0_session_response = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00"
    )
    message_authentication_code_cbc = calculate_message_authentication_code_cbc(
        peer_device_authentication_code,
        additional_data=_a_data[:8]
        + pub_keys_xor,  # knx_ip_header + secure_session_id + bytes_xor(client_pub_key, server_pub_key)
    )
    message_authentication_code = encrypt_data_ctr(
        peer_device_authentication_code,
        mac_cbc=message_authentication_code_cbc,
        counter_0=ctr_0_session_response,
    )
    assert message_authentication_code == bytes.fromhex(
        "a9 22 50 5a aa 43 61 63 57 0b d5 49 4c 2d f2 a3"
    )

    ecdh_shared_secret = client_private_key.exchange(peer_public_key)
    print(f"ECDH shared secret: {ecdh_shared_secret.hex()}")

    session_key = sha256_hash(ecdh_shared_secret)[:16]
    print(f"Session key: {session_key.hex()}")

    _, mac_tr = decrypt_ctr(
        peer_device_authentication_code,
        payload=message_authentication_code,
        counter_0=ctr_0_session_response,
    )
    assert mac_tr == message_authentication_code_cbc  # verification of MAC

    #####################
    # SessionAuthenticate
    #####################
    #   shall be wrapped in SecureWrapper
    print("# SessionAuthenticate")

    password_string = "secret"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=16,
        salt=b"user-password.1.secure.ip.knx.org",
        iterations=65536,
    )
    password_hash = kdf.derive(password_string.encode("latin-1"))
    print(f"Password hash: {password_hash.hex(' ')}")
    assert password_hash == bytes.fromhex(
        "03 fc ed b6 66 60 25 1e c8 1a 1a 71 69 01 69 6a"
    )

    authenticate_wrapper = bytes.fromhex(
        "06 10 09 50 00 3e 00 01 00 00 00 00 00 00 00 fa 12 34 56 78 af fe"
        "79 15 a4 f3 6e 6e 42 08"
        "d2 8b 4a 20 7d 8f 35 c0"
        "d1 38 c2 6a 7b 5e 71 69"
        "52 db a8 e7 e4 bd 80 bd"
        "7d 86 8a 3a e7 87 49 de"
    )
    session_authenticate = bytes.fromhex(
        "06 10 09 53 00 18 00 01"
        "1f 1d 59 ea 9f 12 a1 52 e5 d9 72 7f 08 46 2c de"  # MAC
    )
    mac_cbc_authenticate = calculate_message_authentication_code_cbc(
        password_hash,
        additional_data=session_authenticate[:8] + pub_keys_xor,
        block_0=bytes(16),
    )
    ctr_0_session_authenticate = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00"
    )
    assert (
        encrypt_data_ctr(
            password_hash,
            mac_cbc=mac_cbc_authenticate,
            counter_0=ctr_0_session_authenticate,
        )
        == session_authenticate[8:]
    )
    assert (
        calculate_wrapper(
            session_key,
            encapsulated_frame=session_authenticate,
            secure_session_id=authenticate_wrapper[6:8],
            sequence_number=authenticate_wrapper[8:14],
            serial_number=authenticate_wrapper[14:20],
            message_tag=authenticate_wrapper[20:22],
        )
        == authenticate_wrapper[22:]
    )
    # verify MAC
    _, mac_tr = decrypt_ctr(
        password_hash,
        payload=session_authenticate[8:],
        counter_0=ctr_0_session_authenticate,
    )
    assert mac_tr == mac_cbc_authenticate

    ###############
    # SessionStatus
    ###############
    #   shall be wrapped in SecureWrapper
    print("# SessionStatus")

    status_wrapper = bytes.fromhex(
        "06 10 09 50 00 2e 00 01 00 00 00 00 00 00 00 fa aa aa aa aa af fe"
        "26 15 6d b5 c7 49 88 8f"
        "a3 73 c3 e0 b4 bd e4 49"
        "7c 39 5e 4b 1c 2f 46 a1"
    )
    session_status = bytes.fromhex("06 10 09 54 00 08 00 00")
    assert (
        calculate_wrapper(
            session_key,
            encapsulated_frame=session_status,
            secure_session_id=status_wrapper[6:8],
            sequence_number=status_wrapper[8:14],
            serial_number=status_wrapper[14:20],
            message_tag=status_wrapper[20:22],
        )
        == status_wrapper[22:]
    )


if __name__ == "__main__":
    main()
