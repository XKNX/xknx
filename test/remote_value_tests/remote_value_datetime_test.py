"""Unit test for RemoteValueDateTime objects."""
import asyncio
import time
import unittest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, HVACOperationMode
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import (
    RemoteValueBinaryHeatCool,
    RemoteValueBinaryOperationMode,
    RemoteValueClimateMode,
    RemoteValueDateTime,
)
from xknx.remote_value.remote_value_climate_mode import _RemoteValueBinaryClimateMode
from xknx.telegram import GroupAddress, Telegram


class TestRemoteValueDateTime(unittest.TestCase):
    """Test class for RemoteValueDateTime objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_init_raises_keyerror(self):
        """Test init raises KeyError if not supported."""
        xknx = XKNX()
        with self.assertRaises(ConversionError):
            RemoteValueDateTime(xknx, value_type="trees_are_important")

    def test_from_knx(self):
        """Test parsing of RV with datetime object."""
        xknx = XKNX()
        rv = RemoteValueDateTime(xknx, value_type="datetime")
        self.assertEqual(
            rv.from_knx(DPTArray((0x75, 0x0B, 0x1C, 0x17, 0x07, 0x18, 0x20, 0x80))),
            time.strptime("2017-11-28 23:7:24", "%Y-%m-%d %H:%M:%S"),
        )

    def test_to_knx(self):
        """Testing date time object."""
        xknx = XKNX()
        rv = RemoteValueDateTime(xknx, value_type="datetime")
        array = rv.to_knx(time.strptime("2017-11-28 23:7:24", "%Y-%m-%d %H:%M:%S"))
        self.assertEqual(array.value, (0x75, 0x0B, 0x1C, 0x57, 0x07, 0x18, 0x20, 0x80))

    def test_payload_valid(self):
        """Testing KNX/Byte representation of DPTDateTime object."""
        xknx = XKNX()
        rv = RemoteValueDateTime(xknx, value_type="datetime")
        self.assertTrue(
            rv.payload_valid(DPTArray((0x75, 0x0B, 0x1C, 0x57, 0x07, 0x18, 0x20, 0x80)))
        )

    def test_payload_invalid(self):
        """Testing KNX/Byte representation of DPTDateTime object."""
        xknx = XKNX()
        rv = RemoteValueDateTime(xknx, value_type="datetime")
        self.assertFalse(
            rv.payload_valid(DPTArray((0x0B, 0x1C, 0x57, 0x07, 0x18, 0x20, 0x80)))
        )
