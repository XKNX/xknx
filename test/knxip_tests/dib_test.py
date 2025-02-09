"""Unit test for KNX/IP DIB objects."""

import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import (
    DIB,
    DIBDeviceInformation,
    DIBGeneric,
    DIBSecuredServiceFamilies,
    DIBServiceFamily,
    DIBSuppSVCFamilies,
    DIBTunnelingInfo,
    DIBTypeCode,
    KNXMedium,
)
from xknx.telegram import IndividualAddress


class TestKNXIPDIB:
    """Test class for KNX/IP DIB objects."""

    def test_dib_base(self) -> None:
        """Test parsing and streaming KNX/IP DIB packet."""
        raw = bytes(
            (0x0C, 0x02, 0x02, 0x01, 0x03, 0x02, 0x04, 0x01, 0x05, 0x01, 0x07, 0x01)
        )
        dib = DIBGeneric()
        assert dib.from_knx(raw) == 12
        assert dib.dtc == DIBTypeCode.SUPP_SVC_FAMILIES
        assert dib.to_knx() == raw
        assert dib.calculated_length() == 12

    def test_dib_wrong_input(self) -> None:
        """Test parsing of wrong KNX/IP DIB packet."""
        raw = (0x08, 0x01, 0xC0, 0xA8, 0x2A)
        with pytest.raises(CouldNotParseKNXIP):
            DIBGeneric().from_knx(raw)

    def test_device_info(self) -> None:
        """Test parsing of device info."""
        raw = bytes.fromhex(
            "36 01 02 00 11 00 23 42 13 37 13 37 13 37 E0 00"
            "17 0C 00 01 02 03 04 05 47 69 72 61 20 4B 4E 58"
            "2F 49 50 2D 52 6F 75 74 65 72 00 00 00 00 00 00"
            "00 00 00 00 00 00"
        )

        dib = DIB.determine_dib(raw)
        assert isinstance(dib, DIBDeviceInformation)
        assert dib.from_knx(raw) == DIBDeviceInformation.LENGTH
        assert dib.knx_medium == KNXMedium.TP1
        assert dib.programming_mode is False
        assert dib.individual_address == IndividualAddress("1.1.0")
        assert dib.name == "Gira KNX/IP-Router"
        assert dib.mac_address == "00:01:02:03:04:05"
        assert dib.multicast_address == "224.0.23.12"
        assert dib.serial_number == "13:37:13:37:13:37"
        assert dib.project_number == 564
        assert dib.installation_number == 2
        assert dib.to_knx() == raw

    def test_dib_sup_svc_families_router(self) -> None:
        """Test parsing of svc families."""
        raw = bytes(
            (0x0C, 0x02, 0x02, 0x01, 0x03, 0x02, 0x04, 0x01, 0x05, 0x01, 0x07, 0x01)
        )

        dib = DIB.determine_dib(raw)
        assert isinstance(dib, DIBSuppSVCFamilies)
        assert dib.from_knx(raw) == 12

        assert dib.families == [
            DIBSuppSVCFamilies.Family(DIBServiceFamily.CORE, 1),
            DIBSuppSVCFamilies.Family(DIBServiceFamily.DEVICE_MANAGEMENT, 2),
            DIBSuppSVCFamilies.Family(DIBServiceFamily.TUNNELING, 1),
            DIBSuppSVCFamilies.Family(DIBServiceFamily.ROUTING, 1),
            DIBSuppSVCFamilies.Family(
                DIBServiceFamily.REMOTE_CONFIGURATION_DIAGNOSIS, 1
            ),
        ]

        assert dib.to_knx() == raw

        assert dib.supports(DIBServiceFamily.CORE)
        assert dib.supports(DIBServiceFamily.DEVICE_MANAGEMENT)
        assert dib.supports(DIBServiceFamily.DEVICE_MANAGEMENT, version=2)
        assert dib.supports(DIBServiceFamily.TUNNELING)
        assert not dib.supports(DIBServiceFamily.TUNNELING, version=2)
        assert dib.supports(DIBServiceFamily.ROUTING, version=1)

        assert dib.version(DIBServiceFamily.CORE) == 1
        assert dib.version(DIBServiceFamily.DEVICE_MANAGEMENT) == 2
        assert dib.version(DIBServiceFamily.TUNNELING) == 1
        assert dib.version(DIBServiceFamily.ROUTING) == 1

    def test_dib_sup_svc_families_interface(self) -> None:
        """Test parsing of svc families."""
        raw = bytes((0x0A, 0x02, 0x02, 0x02, 0x03, 0x02, 0x04, 0x02, 0x07, 0x01))

        dib = DIB.determine_dib(raw)
        assert isinstance(dib, DIBSuppSVCFamilies)
        assert dib.from_knx(raw) == 10

        assert dib.families == [
            DIBSuppSVCFamilies.Family(DIBServiceFamily.CORE, 2),
            DIBSuppSVCFamilies.Family(DIBServiceFamily.DEVICE_MANAGEMENT, 2),
            DIBSuppSVCFamilies.Family(DIBServiceFamily.TUNNELING, 2),
            DIBSuppSVCFamilies.Family(
                DIBServiceFamily.REMOTE_CONFIGURATION_DIAGNOSIS, 1
            ),
        ]

        assert dib.to_knx() == raw

        assert dib.supports(DIBServiceFamily.TUNNELING)
        assert dib.supports(DIBServiceFamily.TUNNELING, version=2)
        assert not dib.supports(DIBServiceFamily.ROUTING)
        assert not dib.supports(DIBServiceFamily.ROUTING, version=2)

        assert dib.version(DIBServiceFamily.CORE) == 2
        assert dib.version(DIBServiceFamily.DEVICE_MANAGEMENT) == 2
        assert dib.version(DIBServiceFamily.TUNNELING) == 2
        assert dib.version(DIBServiceFamily.ROUTING) is None

    def test_dib_secured_service_families(self) -> None:
        """Test parsing of secured service families."""
        raw = bytes((0x08, 0x06, 0x03, 0x01, 0x04, 0x01, 0x05, 0x01))

        dib = DIB.determine_dib(raw)
        assert isinstance(dib, DIBSecuredServiceFamilies)
        assert dib.from_knx(raw) == 8

        assert dib.families == [
            DIBSuppSVCFamilies.Family(DIBServiceFamily.DEVICE_MANAGEMENT, 1),
            DIBSuppSVCFamilies.Family(DIBServiceFamily.TUNNELING, 1),
            DIBSuppSVCFamilies.Family(DIBServiceFamily.ROUTING, 1),
        ]

        assert dib.to_knx() == raw

        assert dib.supports(DIBServiceFamily.TUNNELING)
        assert dib.supports(DIBServiceFamily.TUNNELING, version=1)
        assert dib.supports(DIBServiceFamily.ROUTING)
        assert not dib.supports(DIBServiceFamily.ROUTING, version=2)
        assert dib.supports(DIBServiceFamily.DEVICE_MANAGEMENT)

    def test_dib_tunneling_info(self) -> None:
        """Test parsing of tunneling info."""
        raw = (
            b"\x24\x07\x00\xf8\x40\x01\x00\x05\x40\x02\x00\x05\x40\x03\x00\x05"
            b"\x40\x04\x00\x05\x40\x05\x00\x05\x40\x06\x00\x05\x40\x07\x00\x05"
            b"\x40\x08\x00\x06"
        )

        dib = DIB.determine_dib(raw)
        assert isinstance(dib, DIBTunnelingInfo)
        assert dib.from_knx(raw) == 36

        assert dib.max_apdu_length == 248

        assert len(dib.slots) == 8
        for address in ["4.0.1", "4.0.2", "4.0.3", "4.0.4", "4.0.5", "4.0.6", "4.0.7"]:
            assert dib.slots[IndividualAddress(address)].usable
            assert not dib.slots[IndividualAddress(address)].authorized
            assert dib.slots[IndividualAddress(address)].free
        assert dib.slots[IndividualAddress("4.0.8")].usable
        assert dib.slots[IndividualAddress("4.0.8")].authorized
        assert not dib.slots[IndividualAddress("4.0.8")].free

        assert dib.to_knx() == raw
