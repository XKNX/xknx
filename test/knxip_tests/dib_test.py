"""Unit test for KNX/IP DIB objects."""
import unittest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import (
    DIB, DIBDeviceInformation, DIBGeneric, DIBServiceFamily,
    DIBSuppSVCFamilies, DIBTypeCode, KNXMedium)
from xknx.telegram import PhysicalAddress


class Test_KNXIP_DIB(unittest.TestCase):
    """Test class for KNX/IP DIB objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_dib_base(self):
        """Test parsing and streaming KNX/IP DIB packet."""
        raw = ((0x0c, 0x02, 0x02, 0x01, 0x03, 0x02, 0x04, 0x01,
                0x05, 0x01, 0x07, 0x01))
        dib = DIBGeneric()
        self.assertEqual(dib.from_knx(raw), 12)
        self.assertEqual(dib.dtc, DIBTypeCode.SUPP_SVC_FAMILIES)
        self.assertEqual(dib.to_knx(), list(raw))
        self.assertEqual(dib.calculated_length(), 12)

    def test_dib_wrong_input(self):
        """Test parsing of wrong KNX/IP DIB packet."""
        raw = ((0x08, 0x01, 0xc0, 0xa8, 0x2a))
        with self.assertRaises(CouldNotParseKNXIP):
            DIBGeneric().from_knx(raw)

    def test_device_info(self):
        """Test parsing of device info."""
        raw = ((0x36, 0x01, 0x02, 0x00, 0x11, 0x00, 0x23, 0x42,
                0x13, 0x37, 0x13, 0x37, 0x13, 0x37, 0xE0, 0x00,
                0x17, 0x0c, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05,
                0x47, 0x69, 0x72, 0x61, 0x20, 0x4b, 0x4e, 0x58,
                0x2f, 0x49, 0x50, 0x2d, 0x52, 0x6f, 0x75, 0x74,
                0x65, 0x72, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00))

        dib = DIB.determine_dib(raw)
        self.assertTrue(isinstance(dib, DIBDeviceInformation))
        self.assertEqual(dib.from_knx(raw), DIBDeviceInformation.LENGTH)
        self.assertEqual(dib.knx_medium, KNXMedium.TP1)
        self.assertEqual(dib.programming_mode, False)
        self.assertEqual(dib.individual_address, PhysicalAddress('1.1.0'))
        self.assertEqual(dib.name, 'Gira KNX/IP-Router')
        self.assertEqual(dib.mac_address, '00:01:02:03:04:05')
        self.assertEqual(dib.multicast_address, '224.0.23.12')
        self.assertEqual(dib.serial_number, '13:37:13:37:13:37')
        self.assertEqual(dib.project_number, 564)
        self.assertEqual(dib.installation_number, 2)
        self.assertEqual(dib.to_knx(), list(raw))

    def test_dib_sup_svc_families(self):
        """Test parsing of svc families."""
        raw = ((0x0c, 0x02, 0x02, 0x01, 0x03, 0x02, 0x04, 0x01,
                0x05, 0x01, 0x07, 0x01))

        dib = DIB.determine_dib(raw)
        self.assertTrue(isinstance(dib, DIBSuppSVCFamilies))
        self.assertEqual(dib.from_knx(raw), 12)

        self.assertEqual(dib.families, [
            DIBSuppSVCFamilies.Family(
                DIBServiceFamily.CORE, 1),
            DIBSuppSVCFamilies.Family(
                DIBServiceFamily.DEVICE_MANAGEMENT, 2),
            DIBSuppSVCFamilies.Family(
                DIBServiceFamily.TUNNELING, 1),
            DIBSuppSVCFamilies.Family(
                DIBServiceFamily.ROUTING, 1),
            DIBSuppSVCFamilies.Family(
                DIBServiceFamily.REMOTE_CONFIGURATION_DIAGNOSIS, 1)
        ])

        self.assertEqual(dib.to_knx(), list(raw))
