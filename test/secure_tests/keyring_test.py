"""Unit test for keyring reader and writer."""

import base64
from pathlib import Path
from xml.dom.minidom import parseString

import pytest

from xknx.exceptions.exception import InvalidSecureConfiguration
from xknx.secure.keyring import (
    InterfaceType,
    Keyring,
    XMLBackbone,
    XMLDevice,
    XMLGroupAddress,
    XMLInterface,
    save_keyring,
    sync_load_keyring,
    sync_save_keyring,
    verify_keyring_signature,
)
from xknx.telegram import GroupAddress, IndividualAddress


class TestKeyRing:
    """Test class for keyring."""

    keyring_test_file = Path(__file__).parent / "resources/keyring.knxkeys"
    testcase_file: str = Path(__file__).parent / "resources/testcase.knxkeys"
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

    def test_load_keyring_test(self) -> None:
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

    def test_load_testcase_file(self) -> None:
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

    def test_load_special_chars_file(self) -> None:
        """Test load keyring from knxkeys file."""
        keyring = sync_load_keyring(self.special_chars_file, "test")
        TestKeyRing.assert_interface(keyring, "tunnel_2", IndividualAddress("1.0.2"))
        TestKeyRing.assert_interface(keyring, "tunnel_3", IndividualAddress("1.0.3"))
        TestKeyRing.assert_interface(keyring, "tunnel_4", IndividualAddress("1.0.4"))
        TestKeyRing.assert_interface(keyring, "tunnel_5", IndividualAddress("1.0.5"))
        TestKeyRing.assert_interface(keyring, "tunnel_6", IndividualAddress("1.0.6"))
        assert keyring.backbone is None

    def test_load_data_secure_ip(self) -> None:
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

    def test_load_data_secure_usb(self) -> None:
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

    def test_verify_signature(self) -> None:
        """Test signature verification."""
        assert verify_keyring_signature(self.keyring_test_file, "pwd")
        assert verify_keyring_signature(self.testcase_file, "password")
        assert verify_keyring_signature(self.special_chars_file, "test")

    def test_invalid_signature(self) -> None:
        """Test invalid signature throws error."""
        with pytest.raises(InvalidSecureConfiguration):
            sync_load_keyring(self.testcase_file, "wrong_password")

    def test_raises_error(self) -> None:
        """Test raises error if password is wrong."""
        with pytest.raises(InvalidSecureConfiguration):
            sync_load_keyring(
                self.testcase_file, "wrong_password", validate_signature=False
            )

    def test_keyring_get_methods_full(self) -> None:
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

    def test_keyring_get_methods_one_interface(self) -> None:
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

    def test_keyring_metadata(self) -> None:
        """Test keyring metadata parsing."""
        keyring = sync_load_keyring(self.data_secure_ip, "test")
        assert keyring.project_name == "DataSecure_only"
        assert keyring.created_by == "ETS 5.7.7 (Build 1428)"
        assert keyring.created == "2023-02-06T21:17:09"
        assert keyring.xmlns == "http://knx.org/xml/keyring/1"


RESOURCES = Path(__file__).parent / "resources"
KEYRING_FILES = [
    ("keyring.knxkeys", "pwd"),
    ("testcase.knxkeys", "password"),
    ("special_chars_secure_tunnel.knxkeys", "test"),
    ("DataSecure_only_one_interface.knxkeys", "test"),
    ("DataSecure_usb.knxkeys", "test"),
    ("SecureTest.knxkeys", "test"),
]


def assert_keyrings_equal(keyring: Keyring, expected: Keyring) -> None:
    """Assert that two keyrings hold the same metadata and decrypted attributes."""
    assert keyring.project_name == expected.project_name
    assert keyring.created_by == expected.created_by
    assert keyring.created == expected.created
    assert keyring.xmlns == "http://knx.org/xml/keyring/1"

    if expected.backbone is None:
        assert keyring.backbone is None
    else:
        assert keyring.backbone is not None
        assert keyring.backbone.multicast_address == expected.backbone.multicast_address
        assert keyring.backbone.latency == expected.backbone.latency
        assert keyring.backbone.decrypted_key == expected.backbone.decrypted_key

    assert len(keyring.interfaces) == len(expected.interfaces)
    for interface, expected_interface in zip(
        keyring.interfaces, expected.interfaces, strict=True
    ):
        assert interface.type is expected_interface.type
        assert interface.individual_address == expected_interface.individual_address
        assert interface.host == expected_interface.host
        assert interface.user_id == expected_interface.user_id
        assert interface.decrypted_password == expected_interface.decrypted_password
        assert (
            interface.decrypted_authentication
            == expected_interface.decrypted_authentication
        )
        assert list(interface.group_addresses.items()) == list(
            expected_interface.group_addresses.items()
        )

    assert [
        (group_address.address, group_address.decrypted_key)
        for group_address in keyring.group_addresses
    ] == [
        (group_address.address, group_address.decrypted_key)
        for group_address in expected.group_addresses
    ]

    assert len(keyring.devices) == len(expected.devices)
    for device, expected_device in zip(keyring.devices, expected.devices, strict=True):
        assert device.individual_address == expected_device.individual_address
        assert device.decrypted_tool_key == expected_device.decrypted_tool_key
        assert (
            device.decrypted_management_password
            == expected_device.decrypted_management_password
        )
        assert (
            device.decrypted_authentication == expected_device.decrypted_authentication
        )
        assert device.sequence_number == expected_device.sequence_number
        assert device.serial_number == expected_device.serial_number


class TestKeyringWriter:
    """Test class for writing keyrings."""

    @pytest.mark.parametrize(("file_name", "password"), KEYRING_FILES)
    def test_round_trip_new_password(
        self, tmp_path: Path, file_name: str, password: str
    ) -> None:
        """Test writing a loaded keyring with a new password."""
        original = sync_load_keyring(RESOURCES / file_name, password)
        path = tmp_path / "saved.knxkeys"
        new_password = "new Passwörd"

        sync_save_keyring(original, path, new_password)

        assert verify_keyring_signature(path, new_password)
        assert not verify_keyring_signature(path, password)
        with pytest.raises(InvalidSecureConfiguration):
            sync_load_keyring(path, password)

        assert_keyrings_equal(sync_load_keyring(path, new_password), original)

    @pytest.mark.parametrize(("file_name", "password"), KEYRING_FILES)
    def test_round_trip_same_password(
        self, tmp_path: Path, file_name: str, password: str
    ) -> None:
        """Test writing a loaded keyring with its own password keeps the encrypted keys."""
        original = sync_load_keyring(RESOURCES / file_name, password)
        path = tmp_path / "saved.knxkeys"

        sync_save_keyring(original, path, password)
        saved = sync_load_keyring(path, password)

        assert_keyrings_equal(saved, original)
        # keys are encrypted without a random part - same password and `created` give the same result
        if original.backbone is not None:
            assert saved.backbone is not None
            assert saved.backbone.key == original.backbone.key
        assert [group_address.key for group_address in saved.group_addresses] == [
            group_address.key for group_address in original.group_addresses
        ]
        assert [device.tool_key for device in saved.devices] == [
            device.tool_key for device in original.devices
        ]

    @pytest.mark.parametrize(
        "file_name",
        ["DataSecure_only_one_interface.knxkeys", "DataSecure_usb.knxkeys"],
    )
    def test_same_signature(self, file_name: str) -> None:
        """Test a keyring without passwords is written with the signature of the original file."""
        original = sync_load_keyring(RESOURCES / file_name, "test")
        saved = Keyring()
        saved.parse_xml(
            parseString(original.to_xml("test")).getElementsByTagName("Keyring")[0]
        )
        assert saved.signature == original.signature

    async def test_save_keyring_from_scratch(self, tmp_path: Path) -> None:
        """Test writing a keyring built from scratch."""
        keyring = Keyring()
        keyring.project_name = "Project ÄÖÜ <&>"
        keyring.created_by = "xknx"
        keyring.created = "2026-10-16T12:34:56"

        keyring.backbone = XMLBackbone()
        keyring.backbone.multicast_address = "224.0.23.12"
        keyring.backbone.latency = 1000
        keyring.backbone.decrypted_key = bytes.fromhex(
            "000102030405060708090a0b0c0d0e0f"
        )

        tunnel = XMLInterface()
        tunnel.type = InterfaceType.TUNNELING
        tunnel.individual_address = IndividualAddress("1.0.11")
        tunnel.host = IndividualAddress("1.0.10")
        tunnel.user_id = 2
        tunnel.decrypted_password = "tunnel password äö"
        tunnel.decrypted_authentication = "authentication"
        tunnel.group_addresses = {
            GroupAddress("1/2/3"): [IndividualAddress("1.0.20")],
            GroupAddress("1/2/4"): [],
        }
        usb = XMLInterface()
        usb.type = InterfaceType.USB
        usb.individual_address = IndividualAddress("1.0.255")
        usb.group_addresses = {
            GroupAddress("1/2/3"): [
                IndividualAddress("1.0.11"),
                IndividualAddress("1.0.20"),
            ]
        }
        keyring.interfaces = [tunnel, usb]

        for address, key in (("1/2/3", "11" * 16), ("1/2/4", "22" * 16)):
            group_address = XMLGroupAddress()
            group_address.address = GroupAddress(address)
            group_address.decrypted_key = bytes.fromhex(key)
            keyring.group_addresses.append(group_address)

        ip_device = XMLDevice()
        ip_device.individual_address = IndividualAddress("1.0.10")
        ip_device.decrypted_tool_key = bytes.fromhex("33" * 16)
        ip_device.decrypted_management_password = "commissioning"
        ip_device.decrypted_authentication = "authentication"
        ip_device.sequence_number = 123456789
        ip_device.serial_number = bytes.fromhex("00fa12345678")
        tp_device = XMLDevice()
        tp_device.individual_address = IndividualAddress("1.0.20")
        tp_device.decrypted_tool_key = bytes.fromhex("44" * 16)
        keyring.devices = [ip_device, tp_device]

        path = tmp_path / "new.knxkeys"
        await save_keyring(keyring, path, "secret")

        assert verify_keyring_signature(path, "secret")
        loaded = sync_load_keyring(path, "secret")
        assert_keyrings_equal(loaded, keyring)
        assert loaded.get_data_secure_group_keys(
            receiver=IndividualAddress("1.0.11")
        ) == {
            GroupAddress("1/2/3"): bytes.fromhex("11" * 16),
            GroupAddress("1/2/4"): bytes.fromhex("22" * 16),
        }

        signature = base64.b64encode(loaded.signature).decode()
        content = path.read_text(encoding="utf-8")
        assert content.startswith(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<Keyring Project="Project ÄÖÜ &lt;&amp;&gt;" CreatedBy="xknx" '
            f'Created="2026-10-16T12:34:56" Signature="{signature}" '
            'xmlns="http://knx.org/xml/keyring/1">\n'
            '  <Backbone MulticastAddress="224.0.23.12" Latency="1000" Key="'
        )
        assert '<Group Address="2564" Senders=""/>' in content
        assert '<Interface IndividualAddress="1.0.255" Type="USB">' in content
        assert 'SequenceNumber="123456789" SerialNumber="00FA12345678"/>' in content
        assert '<Device IndividualAddress="1.0.20" ToolKey="' in content

    def test_to_xml_invalid_values(self) -> None:
        """Test values that can't be stored in a keyring raise."""
        keyring = sync_load_keyring(RESOURCES / "keyring.knxkeys", "pwd")
        keyring.interfaces[0].decrypted_password = "a" * 23
        keyring.to_xml("password")
        keyring.interfaces[0].decrypted_password = "a" * 24
        with pytest.raises(ValueError, match="Password"):
            keyring.to_xml("password")

        keyring = sync_load_keyring(RESOURCES / "keyring.knxkeys", "pwd")
        keyring.devices[0].decrypted_tool_key = bytes(15)
        with pytest.raises(ValueError, match="Key"):
            keyring.to_xml("password")

        keyring = sync_load_keyring(RESOURCES / "keyring.knxkeys", "pwd")
        keyring.group_addresses[0].decrypted_key = None
        with pytest.raises(ValueError, match="Group address"):
            keyring.to_xml("password")

        keyring = sync_load_keyring(RESOURCES / "keyring.knxkeys", "pwd")
        keyring.backbone.multicast_address = None
        with pytest.raises(ValueError, match="multicast"):
            keyring.to_xml("password")
