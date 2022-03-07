"""Unit test for keyring reader."""
import os

from xknx.secure import Keyring, load_key_ring
from xknx.secure.keyring import verify_keyring_signature


class TestKeyRing:
    """Test class for keyring."""

    keyring_test_file = os.path.join(
        os.path.dirname(__file__), "resources/keyring.knxkeys"
    )

    def test_load_keyring(self):
        """Test string representation of climate object."""
        keyring: Keyring = load_key_ring(self.keyring_test_file, "pwd")
        TestKeyRing.assert_interface(keyring, "user2", "5")
        TestKeyRing.assert_interface(keyring, "user1", "1")
        TestKeyRing.assert_interface(keyring, "user4", "2")
        TestKeyRing.assert_interface(keyring, "@zvI1G&_", "3")

    def test_verify_signature(self):
        """Test signature verification."""
        assert verify_keyring_signature(self.keyring_test_file, "pwd")

    @staticmethod
    def assert_interface(keyring: Keyring, password: str, user: str) -> None:
        """Verify password for given user."""
        for interface in keyring.interfaces:
            if interface.user_id == user:
                assert interface.decrypted_password == password
