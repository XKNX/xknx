"""Unit test for RemoteValueSensor objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueSensor


class TestRemoteValueSensor(unittest.TestCase):
    """Test class for RemoteValueSensor objects."""

    def test_wrong_value_type(self):
        """Test initializing with wrong value_type."""
        xknx = XKNX()
        with self.assertRaises(ConversionError):
            RemoteValueSensor(xknx=xknx, value_type="wrong_value_type")

    def test_payload_length_defined(self):
        """Test if all members of DPTMAP implement payload_length."""
        for value_type in RemoteValueSensor.DPTMAP:
            self.assertTrue(
                isinstance(RemoteValueSensor.DPTMAP[value_type].payload_length,
                           int))
