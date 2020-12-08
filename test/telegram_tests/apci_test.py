"""Unit test for APCI objects."""
import unittest
from unittest.mock import patch

from pytest import raises
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.telegram.apci import APCI, GroupValueRead, GroupValueResponse, GroupValueWrite


class TestAPCI(unittest.TestCase):
    """Test class for APCI objects."""

    def test_resolve_class(self):
        """Test resolve_class for supported services."""
        test_cases = [
            (GroupValueRead.code.value, GroupValueRead),
            (GroupValueWrite.code.value, GroupValueWrite),
            (GroupValueResponse.code.value, GroupValueResponse),
        ]

        for code, clazz in test_cases:
            self.assertEqual(APCI.resolve_class(code), clazz)

    def test_resolve_class_unsupported(self):
        """Test resolve_class for unsupported services."""

        with raises(ConversionError, match=r".*Class not implemented for APCI.*"):
            APCI.resolve_class(0x0100)

        with raises(
            ConversionError, match=r".*Class not implemented for extended APCI.*"
        ):
            APCI.resolve_class(0x03C0)


class TestGroupValueRead(unittest.TestCase):
    """Test class for GroupValueRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = GroupValueRead()

        self.assertEqual(payload.calculated_length(), 1)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = GroupValueRead()
        payload.from_knx(bytes([0x00, 0x00]))

        self.assertEqual(payload, GroupValueRead())

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = GroupValueRead()

        self.assertEqual(payload.to_knx(), bytes([0x00, 0x00]))

    def test_str(self):
        """Test the __str__ method."""
        payload = GroupValueRead()

        self.assertEqual(str(payload), "<GroupValueRead />")


class TestGroupValueWrite(unittest.TestCase):
    """Test class for GroupValueWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload_a = GroupValueWrite(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueWrite(DPTBinary(1))

        self.assertEqual(payload_a.calculated_length(), 4)
        self.assertEqual(payload_b.calculated_length(), 1)

    def test_calculated_length_exception(self):
        """Test the test_calculated_length method for unsupported dpt."""
        payload = GroupValueWrite(object())

        with self.assertRaises(TypeError):
            payload.calculated_length()

    def test_from_knx(self):
        """Test the from_knx method."""
        payload_a = GroupValueWrite()
        payload_a.from_knx(bytes([0x00, 0x80, 0x05, 0x04, 0x03, 0x02, 0x01]))
        payload_b = GroupValueWrite()
        payload_b.from_knx(bytes([0x00, 0x82]))

        self.assertEqual(
            payload_a, GroupValueWrite(DPTArray((0x05, 0x04, 0x03, 0x02, 0x01)))
        )
        self.assertEqual(payload_b, GroupValueWrite(DPTBinary(0x02)))

    def test_to_knx(self):
        """Test the to_knx method."""

        payload_a = GroupValueWrite(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueWrite(DPTBinary(1))

        self.assertEqual(payload_a.to_knx(), bytes([0x00, 0x80, 0x01, 0x02, 0x03]))
        self.assertEqual(payload_b.to_knx(), bytes([0x00, 0x81]))

    def test_to_knx_exception(self):
        """Test the to_knx method for unsupported dpt."""
        payload = GroupValueWrite(object())

        with self.assertRaises(TypeError):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = GroupValueWrite(DPTBinary(1))

        self.assertEqual(
            str(payload), '<GroupValueWrite value="<DPTBinary value="1" />" />'
        )


class TestGroupValueResponse(unittest.TestCase):
    """Test class for TestGroupValueResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload_a = GroupValueResponse(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueResponse(DPTBinary(1))

        self.assertEqual(payload_a.calculated_length(), 4)
        self.assertEqual(payload_b.calculated_length(), 1)

    def test_calculated_length_exception(self):
        """Test the test_calculated_length method for unsupported dpt."""
        payload = GroupValueResponse(object())

        with self.assertRaises(TypeError):
            payload.calculated_length()

    def test_from_knx(self):
        """Test the from_knx method."""
        payload_a = GroupValueResponse()
        payload_a.from_knx(bytes([0x00, 0x80, 0x05, 0x04, 0x03, 0x02, 0x01]))
        payload_b = GroupValueResponse()
        payload_b.from_knx(bytes([0x00, 0x82]))

        self.assertEqual(
            payload_a, GroupValueResponse(DPTArray((0x05, 0x04, 0x03, 0x02, 0x01)))
        )
        self.assertEqual(payload_b, GroupValueResponse(DPTBinary(0x02)))

    def test_to_knx(self):
        """Test the to_knx method."""

        payload_a = GroupValueResponse(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueResponse(DPTBinary(1))

        self.assertEqual(payload_a.to_knx(), bytes([0x00, 0x40, 0x01, 0x02, 0x03]))
        self.assertEqual(payload_b.to_knx(), bytes([0x00, 0x41]))

    def test_to_knx_exception(self):
        """Test the to_knx method for unsupported dpt."""
        payload = GroupValueResponse(object())

        with self.assertRaises(TypeError):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = GroupValueResponse(DPTBinary(1))

        self.assertEqual(
            str(payload), '<GroupValueResponse value="<DPTBinary value="1" />" />'
        )
