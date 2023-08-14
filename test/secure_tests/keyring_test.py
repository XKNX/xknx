"""Unit test for keyring reader."""
import os
from pathlib import Path

import pytest

from xknx.exceptions.exception import InvalidSecureConfiguration
from xknx.secure.keyring import (
    InterfaceType,
    Keyring,
    XMLDevice,
    XMLInterface,
    sync_load_keyring,
    verify_keyring_signature,
)
from xknx.telegram import GroupAddress, IndividualAddress


class TestKeyRing:
    """Test class for keyring."""

    keyring_test_file = Path(__file__).parent / "resources/keyring.knxkeys"
    testcase_file: str = os.path.join(
        os.path.dirname(__file__), "resources/testcase.knxkeys"
    )
    special_chars_file = (
        Path(__file__).parent / "resources/special_chars_secure_tunnel.knxkeys"
    )
    data_secure_ip = (
        Path(__file__).parent / "resources/DataSecure_only_one_interface.knxkeys"
    )
    data_secure_usb = Path(__file__).parent / "resources/DataSecure_usb.knxkeys"

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

    def test_load_keyring_test(self):
        """Test load keyring from knxkeys file."""
        keyring = sync_load_keyring(self.keyring_test_file, "pwd")
        TestKeyRing.assert_interface(keyring, "user4", IndividualAddress("1.1.4"))
        TestKeyRing.assert_interface(keyring, "@zvI1G&_", IndividualAddress("1.1.6"))
        TestKeyRing.assert_interface(keyring, "ZvDY-:g#", IndividualAddress("1.1.7"))
        TestKeyRing.assert_interface(keyring, "user2", IndividualAddress("1.1.2"))
        assert keyring.backbone.multicast_address == "224.0.23.12"
        assert keyring.backbone.latency == 1000
        assert keyring.backbone.decrypted_key == bytes.fromhex(
            "96f034fccf510760cbd63da0f70d4a9d"
        )

    def test_load_testcase_file(self):
        """Test load keyring from knxkeys file."""
        keyring = sync_load_keyring(self.testcase_file, "password")
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

    def test_load_special_chars_file(self):
        """Test load keyring from knxkeys file."""
        keyring = sync_load_keyring(self.special_chars_file, "test")
        TestKeyRing.assert_interface(keyring, "tunnel_2", IndividualAddress("1.0.2"))
        TestKeyRing.assert_interface(keyring, "tunnel_3", IndividualAddress("1.0.3"))
        TestKeyRing.assert_interface(keyring, "tunnel_4", IndividualAddress("1.0.4"))
        TestKeyRing.assert_interface(keyring, "tunnel_5", IndividualAddress("1.0.5"))
        TestKeyRing.assert_interface(keyring, "tunnel_6", IndividualAddress("1.0.6"))
        assert keyring.backbone is None

    def test_load_data_secure_ip(self):
        """Test load keyring from knxkeys file."""
        keyring = sync_load_keyring(self.data_secure_ip, "test")
        assert len(keyring.interfaces) == 1
        tunnel = keyring.interfaces[0]
        assert tunnel is not None
        assert tunnel.password is None
        assert tunnel.decrypted_password is None
        assert tunnel.user_id is None
        assert tunnel.type is InterfaceType.TUNNELING
        assert len(tunnel.group_addresses) == 3
        assert tunnel.group_addresses[GroupAddress("0/0/1")] == [
            IndividualAddress("1.0.1"),
            IndividualAddress("1.0.2"),
        ]
        assert tunnel.group_addresses[GroupAddress("0/0/3")] == [
            IndividualAddress("1.0.1"),
            IndividualAddress("1.0.2"),
        ]
        assert tunnel.group_addresses[GroupAddress("31/7/255")] == []
        assert keyring.backbone is None

    def test_load_data_secure_usb(self):
        """Test load keyring from knxkeys file."""
        keyring = sync_load_keyring(self.data_secure_usb, "test")
        assert len(keyring.interfaces) == 1
        interface = keyring.interfaces[0]
        assert interface is not None
        assert interface.password is None
        assert interface.decrypted_password is None
        assert interface.user_id is None
        assert interface.host is None
        assert interface.type is InterfaceType.USB
        assert len(interface.group_addresses) == 1
        assert interface.group_addresses[GroupAddress("31/7/255")] == [
            IndividualAddress("1.0.4")
        ]
        assert keyring.backbone is None

    def test_verify_signature(self):
        """Test signature verification."""
        assert verify_keyring_signature(self.keyring_test_file, "pwd")
        assert verify_keyring_signature(self.testcase_file, "password")
        assert verify_keyring_signature(self.special_chars_file, "test")

    def test_invalid_signature(self):
        """Test invalid signature throws error."""
        with pytest.raises(InvalidSecureConfiguration):
            sync_load_keyring(self.testcase_file, "wrong_password")

    def test_raises_error(self):
        """Test raises error if password is wrong."""
        with pytest.raises(InvalidSecureConfiguration):
            sync_load_keyring(
                self.testcase_file, "wrong_password", validate_signature=False
            )

    def test_keyring_get_methods_full(self):
        """Test keyring get_* methods for full project export."""
        keyring = sync_load_keyring(self.keyring_test_file, "pwd")
        test_interfaces = keyring.get_tunnel_interfaces_by_host(
            host=IndividualAddress("1.1.10")
        )
        assert len(test_interfaces) == 1
        test_interface = test_interfaces[0]

        test_device = keyring.get_device_by_interface(interface=test_interface)
        assert test_device.individual_address == IndividualAddress("1.1.10")

        test_host = keyring.get_tunnel_host_by_interface(
            tunnelling_slot=IndividualAddress("1.1.8")
        )
        assert test_host == IndividualAddress("1.1.0")

        test_host = keyring.get_tunnel_host_by_interface(
            tunnelling_slot=IndividualAddress("1.1.10")
        )
        assert test_host is None

        test_interface = keyring.get_tunnel_interface_by_host_and_user_id(
            host=IndividualAddress("1.1.0"), user_id=4
        )
        assert test_interface.individual_address == IndividualAddress("1.1.7")

        test_interface = keyring.get_tunnel_interface_by_individual_address(
            tunnelling_slot=IndividualAddress("1.1.8")
        )
        assert test_interface.user_id == 8

        test_interface = keyring.get_tunnel_interface_by_individual_address(
            tunnelling_slot=IndividualAddress("1.1.20")
        )
        assert test_interface.user_id is None
        assert test_interface.host == IndividualAddress("1.1.10")
        # this doesn't check for `type`, but there are no other than TUNNELLING interfaces in this keyring
        test_interface = keyring.get_interface_by_individual_address(
            individual_address=IndividualAddress("1.1.20")
        )
        assert test_interface.host == IndividualAddress("1.1.10")

        full_ga_key_table = keyring.get_data_secure_group_keys()
        assert len(full_ga_key_table) == 1

        individual_ga_key_table = keyring.get_data_secure_group_keys(
            receiver=IndividualAddress("1.1.7")
        )
        assert len(individual_ga_key_table) == 0

        ia_seq_nums = keyring.get_data_secure_senders()
        assert len(ia_seq_nums) == 5

    def test_keyring_get_methods_one_interface(self):
        """Test keyring get_* methods for partial export."""
        keyring = sync_load_keyring(self.data_secure_ip, "test")

        full_ga_key_table = keyring.get_data_secure_group_keys()
        assert len(full_ga_key_table) == 3

        individual_ga_key_table = keyring.get_data_secure_group_keys(
            receiver=IndividualAddress("1.0.4")
        )
        assert len(individual_ga_key_table) == 3

        ia_seq_nums = keyring.get_data_secure_senders()
        assert ia_seq_nums == {
            IndividualAddress("1.0.1"): 0,
            IndividualAddress("1.0.2"): 0,
        }

    def test_keyring_metadata(self):
        """Test keyring metadata parsing."""
        keyring = sync_load_keyring(self.data_secure_ip, "test")
        assert keyring.project_name == "DataSecure_only"
        assert keyring.created_by == "ETS 5.7.7 (Build 1428)"
        assert keyring.created == "2023-02-06T21:17:09"
        assert keyring.xmlns == "http://knx.org/xml/keyring/1"
