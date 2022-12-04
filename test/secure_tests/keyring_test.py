"""Unit test for keyring reader."""
import os

import pytest

from xknx.exceptions.exception import InvalidSecureConfiguration
from xknx.secure.keyring import (
    Keyring,
    XMLDevice,
    XMLInterface,
    _load_keyring,
    verify_keyring_signature,
)
from xknx.telegram import IndividualAddress


class TestKeyRing:
    """Test class for keyring."""

    keyring_test_file = os.path.join(
        os.path.dirname(__file__), "resources/keyring.knxkeys"
    )

    testcase_file = os.path.join(
        os.path.dirname(__file__), "resources/testcase.knxkeys"
    )

    @staticmethod
    def assert_interface(
        keyring: Keyring, password: str, ia: IndividualAddress
    ) -> None:
        """Verify password for given user."""
        matched = False
        if interface := keyring.get_tunnel_interface_by_individual_address(ia):
            matched = True
            assert interface.decrypted_password == password

        assert matched

    def test_load_keyring(self):
        """Test load keyring from knxkeys file."""
        keyring: Keyring = _load_keyring(self.keyring_test_file, "pwd")
        TestKeyRing.assert_interface(keyring, "user4", IndividualAddress("1.1.4"))
        TestKeyRing.assert_interface(keyring, "@zvI1G&_", IndividualAddress("1.1.6"))
        TestKeyRing.assert_interface(keyring, "ZvDY-:g#", IndividualAddress("1.1.7"))
        TestKeyRing.assert_interface(keyring, "user2", IndividualAddress("1.1.2"))
        assert keyring.backbone.multicast_address == "224.0.23.12"
        assert keyring.backbone.latency == 1000
        assert keyring.backbone.decrypted_key == bytes.fromhex(
            "96f034fccf510760cbd63da0f70d4a9d"
        )

    def test_load_keyring_real(self):
        """Test load keyring from knxkeys file."""
        keyring: Keyring = _load_keyring(self.testcase_file, "password")
        TestKeyRing.assert_interface(keyring, "user1", IndividualAddress("1.0.1"))
        TestKeyRing.assert_interface(keyring, "user2", IndividualAddress("1.0.11"))
        TestKeyRing.assert_interface(keyring, "user3", IndividualAddress("1.0.12"))
        TestKeyRing.assert_interface(keyring, "user4", IndividualAddress("1.0.13"))
        assert keyring.devices[0].decrypted_management_password == "commissioning"
        assert keyring.backbone.multicast_address == "224.0.23.12"
        assert keyring.backbone.latency == 1000
        assert keyring.backbone.decrypted_key == bytes.fromhex(
            "cf89fd0f18f4889783c7ef44ee1f5e14"
        )

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
        with pytest.raises(InvalidSecureConfiguration):
            _load_keyring(self.testcase_file, "wrong_password")

    def test_raises_error(self):
        """Test raises error if password is wrong."""
        with pytest.raises(InvalidSecureConfiguration):
            _load_keyring(
                self.testcase_file, "wrong_password", validate_signature=False
            )
