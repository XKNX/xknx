"""Unit test for keyring reader."""
import os

from xknx.secure import Keyring, load_key_ring
from xknx.secure.keyring import XMLDevice, XMLInterface, verify_keyring_signature


class TestKeyRing:
    """Test class for keyring."""

    keyring_test_file = os.path.join(
        os.path.dirname(__file__), "resources/keyring.knxkeys"
    )

    testcase_file = os.path.join(
        os.path.dirname(__file__), "resources/testcase.knxkeys"
    )

    def test_load_keyring(self):
        """Test load keyring from knxkeys file."""
        keyring: Keyring = load_key_ring(self.keyring_test_file, "pwd")
        TestKeyRing.assert_interface(keyring, "user2", "5")
        TestKeyRing.assert_interface(keyring, "user1", "1")
        TestKeyRing.assert_interface(keyring, "user4", "2")
        TestKeyRing.assert_interface(keyring, "@zvI1G&_", "3")

    def test_load_keyring_real(self):
        """Test load keyring from knxkeys file."""
        keyring: Keyring = load_key_ring(self.testcase_file, "password")
        TestKeyRing.assert_interface(keyring, "user1", "3")
        TestKeyRing.assert_interface(keyring, "user2", "4")
        TestKeyRing.assert_interface(keyring, "user3", "5")
        TestKeyRing.assert_interface(keyring, "user4", "6")

        interface: XMLInterface = keyring.interfaces[0]
        device: XMLDevice = keyring.get_device_by_interface(interface)
        assert device is not None
        assert device.decrypted_authentication == "authenticationcode"

    def test_verify_signature(self):
        """Test signature verification."""
        assert verify_keyring_signature(self.keyring_test_file, "pwd")
        assert verify_keyring_signature(self.testcase_file, "password")

    @staticmethod
    def assert_interface(keyring: Keyring, password: str, user: str) -> None:
        """Verify password for given user."""
        for interface in keyring.interfaces:
            if interface.user_id == user:
                assert interface.decrypted_password == password
