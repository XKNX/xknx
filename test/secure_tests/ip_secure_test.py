"""Unit test for IP Secure primitives."""

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from xknx.secure.security_primitives import (
    calculate_message_authentication_code_cbc,
    decrypt_ctr,
    derive_device_authentication_password,
    derive_user_password,
    encrypt_data_ctr,
    generate_ecdh_key_pair,
)


class TestIPSecure:
    """Test class for IP Secure primitives."""

    def test_calculate_message_authentication_code_cbc(self) -> None:
        """Test calculate message authentication code CBC."""
        # SessionResponse from example in KNX specification AN159v06
        assert calculate_message_authentication_code_cbc(
            key=derive_device_authentication_password("trustme"),
            additional_data=bytes.fromhex(
                "06 10 09 52 00 38 00 01 b7 52 be 24 64 59 26 0f"
                "6b 0c 48 01 fb d5 a6 75 99 f8 3b 40 57 b3 ef 1e"
                "79 e4 69 ac 17 23 4e 15"
            ),
        ) == bytes.fromhex("da 3d c6 af 79 89 6a a6 ee 75 73 d6 99 50 c2 83")
        # RoutingIndication from example in KNX specification AN159v06
        assert calculate_message_authentication_code_cbc(
            key=bytes.fromhex("00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f"),
            additional_data=bytes.fromhex("06 10 09 50 00 37 00 00"),
            payload=bytes.fromhex("06 10 05 30 00 11 29 00 bc d0 11 59 0a de 01 00 81"),
            block_0=bytes.fromhex("c0 c1 c2 c3 c4 c5 00 fa 12 34 56 78 af fe 00 11"),
        ) == bytes.fromhex("bd 0a 29 4b 95 25 54 b2 35 39 20 4c 22 71 d2 6b")

    def test_encrypt_data_ctr(self) -> None:
        """Test encrypt data with AES-CTR."""
        # RoutingIndication from example in KNX specification AN159v06
        key = bytes.fromhex("00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f")
        counter_0 = bytes.fromhex("c0 c1 c2 c3 c4 c5 00 fa 12 34 56 78 af fe ff 00")
        mac_cbc = bytes.fromhex("bd 0a 29 4b 95 25 54 b2 35 39 20 4c 22 71 d2 6b")
        payload = bytes.fromhex("06 10 05 30 00 11 29 00 bc d0 11 59 0a de 01 00 81")
        encrypted_data, mac = encrypt_data_ctr(
            key=key, counter_0=counter_0, mac_cbc=mac_cbc, payload=payload
        )
        assert encrypted_data == bytes.fromhex(
            "b7 ee 7e 8a 1c 2f 7b ba be c7 75 fd 6e 10 d0 bc 4b"
        )
        assert mac == bytes.fromhex("72 12 a0 3a aa e4 9d a8 56 89 77 4c 1d 2b 4d a4")

    def test_decrypt_ctr(self) -> None:
        """Test decrypt data with AES-CTR."""
        # RoutingIndication from example in KNX specification AN159v06
        key = bytes.fromhex("00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f")
        counter_0 = bytes.fromhex("c0 c1 c2 c3 c4 c5 00 fa 12 34 56 78 af fe ff 00")
        mac = bytes.fromhex("72 12 a0 3a aa e4 9d a8 56 89 77 4c 1d 2b 4d a4")
        payload = bytes.fromhex("b7 ee 7e 8a 1c 2f 7b ba be c7 75 fd 6e 10 d0 bc 4b")
        decrypted_data, mac_tr = decrypt_ctr(
            key=key,
            counter_0=counter_0,
            mac=mac,
            payload=payload,
        )
        assert decrypted_data == bytes.fromhex(
            "06 10 05 30 00 11 29 00 bc d0 11 59 0a de 01 00 81"
        )
        assert mac_tr == bytes.fromhex(
            "bd 0a 29 4b 95 25 54 b2 35 39 20 4c 22 71 d2 6b"
        )

    def test_derive_device_authentication_password(self) -> None:
        """Test derive device authentication password."""
        assert derive_device_authentication_password("trustme") == bytes.fromhex(
            "e1 58 e4 01 20 47 bd 6c c4 1a af bc 5c 04 c1 fc"
        )

    def test_derive_user_password(self) -> None:
        """Test derive user password."""
        assert derive_user_password("secret") == bytes.fromhex(
            "03 fc ed b6 66 60 25 1e c8 1a 1a 71 69 01 69 6a"
        )

    def test_generate_ecdh_key_pair(self) -> None:
        """Test generate ECDH key pair."""
        private_key, public_key_bytes = generate_ecdh_key_pair()
        assert isinstance(private_key, X25519PrivateKey)
        assert isinstance(public_key_bytes, bytes)
        assert len(public_key_bytes) == 32
        private_key_2, public_key_bytes_2 = generate_ecdh_key_pair()
        assert private_key != private_key_2
        assert public_key_bytes != public_key_bytes_2
