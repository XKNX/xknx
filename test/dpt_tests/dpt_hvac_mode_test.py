"""Unit test for KNX DPT HVAC Operation modes."""
import unittest

from xknx.dpt import DPTControllerStatus, DPTHVACMode, HVACOperationMode
from xknx.exceptions import ConversionError, CouldNotParseKNXIP


class TestDPTControllerStatus(unittest.TestCase):
    """Test class for KNX DPT HVAC Operation modes."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_mode_to_knx(self):
        """Test parsing DPTHVACMode to KNX."""
        self.assertEqual(DPTHVACMode.to_knx(HVACOperationMode.AUTO), (0x00,))
        self.assertEqual(DPTHVACMode.to_knx(HVACOperationMode.COMFORT), (0x01,))
        self.assertEqual(DPTHVACMode.to_knx(HVACOperationMode.STANDBY), (0x02,))
        self.assertEqual(DPTHVACMode.to_knx(HVACOperationMode.NIGHT), (0x03,))
        self.assertEqual(DPTHVACMode.to_knx(HVACOperationMode.FROST_PROTECTION), (0x04,))

    def test_mode_to_knx_wrong_value(self):
        """Test serializing DPTHVACMode to KNX with wrong value."""
        with self.assertRaises(ConversionError):
            DPTHVACMode.to_knx(5)

    def test_mode_from_knx(self):
        """Test parsing DPTHVACMode from KNX."""
        self.assertEqual(DPTHVACMode.from_knx((0x00,)), HVACOperationMode.AUTO)
        self.assertEqual(DPTHVACMode.from_knx((0x01,)), HVACOperationMode.COMFORT)
        self.assertEqual(DPTHVACMode.from_knx((0x02,)), HVACOperationMode.STANDBY)
        self.assertEqual(DPTHVACMode.from_knx((0x03,)), HVACOperationMode.NIGHT)
        self.assertEqual(DPTHVACMode.from_knx((0x04,)), HVACOperationMode.FROST_PROTECTION)

    def test_controller_status_to_knx(self):
        """Test serializing DPTControllerStatus to KNX."""
        with self.assertRaises(ConversionError):
            DPTControllerStatus.to_knx(HVACOperationMode.AUTO)
        self.assertEqual(DPTControllerStatus.to_knx(HVACOperationMode.COMFORT), (0x21,))
        self.assertEqual(DPTControllerStatus.to_knx(HVACOperationMode.STANDBY), (0x22,))
        self.assertEqual(DPTControllerStatus.to_knx(HVACOperationMode.NIGHT), (0x24,))
        self.assertEqual(DPTControllerStatus.to_knx(HVACOperationMode.FROST_PROTECTION), (0x28,))

    def test_controller_status_to_knx_wrong_value(self):
        """Test serializing DPTControllerStatus to KNX with wrong value."""
        with self.assertRaises(ConversionError):
            DPTControllerStatus.to_knx(5)

    def test_controller_status_from_knx(self):
        """Test parsing DPTControllerStatus from KNX."""
        self.assertEqual(DPTControllerStatus.from_knx((0x21,)), HVACOperationMode.COMFORT)
        self.assertEqual(DPTControllerStatus.from_knx((0x22,)), HVACOperationMode.STANDBY)
        self.assertEqual(DPTControllerStatus.from_knx((0x24,)), HVACOperationMode.NIGHT)
        self.assertEqual(DPTControllerStatus.from_knx((0x28,)), HVACOperationMode.FROST_PROTECTION)

    def test_controller_status_from_knx_other_bits_set(self):
        """Test parsing DPTControllerStatus from KNX."""
        self.assertEqual(DPTControllerStatus.from_knx((0x21,)), HVACOperationMode.COMFORT)
        self.assertEqual(DPTControllerStatus.from_knx((0x23,)), HVACOperationMode.STANDBY)
        self.assertEqual(DPTControllerStatus.from_knx((0x27,)), HVACOperationMode.NIGHT)
        self.assertEqual(DPTControllerStatus.from_knx((0x2F,)), HVACOperationMode.FROST_PROTECTION)

    def test_mode_from_knx_wrong_value(self):
        """Test parsing of DPTControllerStatus with wrong value)."""
        with self.assertRaises(ConversionError):
            DPTHVACMode.from_knx((1, 2))

    def test_mode_from_knx_wrong_code(self):
        """Test parsing of DPTHVACMode with wrong code."""
        with self.assertRaises(CouldNotParseKNXIP):
            DPTHVACMode.from_knx((0x05,))

    def test_controller_status_from_knx_wrong_value(self):
        """Test parsing of DPTControllerStatus with wrong value)."""
        with self.assertRaises(ConversionError):
            DPTControllerStatus.from_knx((1, 2))

    def test_controller_status_from_knx_wrong_code(self):
        """Test parsing of DPTControllerStatus with wrong code."""
        with self.assertRaises(CouldNotParseKNXIP):
            DPTControllerStatus.from_knx((0x00,))
