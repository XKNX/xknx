"""Unit test for keyring reader."""
import os

import pytest

from xknx.exceptions.exception import InvalidSecureConfiguration, InvalidSignature
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
        TestKeyRing.assert_interface(keyring, "user4", 2)
        TestKeyRing.assert_interface(keyring, "@zvI1G&_", 3)
        TestKeyRing.assert_interface(keyring, "ZvDY-:g#", 4)
        TestKeyRing.assert_interface(keyring, "user2", 5)

    def test_load_keyring_real(self):
        """Test load keyring from knxkeys file."""
        keyring: Keyring = load_key_ring(self.testcase_file, "password")
        TestKeyRing.assert_interface(keyring, "user1", 3)
        TestKeyRing.assert_interface(keyring, "user2", 4)
        TestKeyRing.assert_interface(keyring, "user3", 5)
        TestKeyRing.assert_interface(keyring, "user4", 6)
        assert keyring.devices[0].decrypted_management_password == "commissioning"

        interface: XMLInterface = keyring.interfaces[0]
        device: XMLDevice = keyring.get_device_by_interface(interface)
        assert device is not None
        assert device.decrypted_authentication == "authenticationcode"

    def test_verify_signature(self):
        """Test signature verification."""
        assert verify_keyring_signature(self.keyring_test_file, "pwd")
        assert verify_keyring_signature(self.testcase_file, "password")

    def test_invalid_signature(self):
        """Test invalid signature throws error."""
        with pytest.raises(InvalidSignature):
            load_key_ring(self.testcase_file, "wrong_password")

    def test_raises_error(self):
        """Test raises error if password is wrong."""
        with pytest.raises(InvalidSecureConfiguration):
            load_key_ring(
                self.testcase_file, "wrong_password", validate_signature=False
            )

    @staticmethod
    def assert_interface(keyring: Keyring, password: str, user: int) -> None:
        """Verify password for given user."""
        matched = False
        if interface := keyring.get_interface_by_user_id(user):
            matched = True
            assert interface.decrypted_password == password

        assert matched
