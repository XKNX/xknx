"""Unit test for RemoveValue objects."""
import asyncio
import unittest
from unittest.mock import patch

import pytest
pytestmark = pytest.mark.asyncio

from xknx import XKNX
from xknx.devices import RemoteValue
from xknx.exceptions import CouldNotParseTelegram
from xknx.knx import DPTArray, DPTBinary, GroupAddress, Telegram


class TestRemoteValue(unittest.TestCase):
    """Test class for RemoteValue objects."""

    def test_warn_payload_valid(self):
        """Test for warning if payload_valid is not implemented."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch('logging.Logger.warning') as mock_warn:
            remote_value.payload_valid(DPTBinary(0))
            mock_warn.assert_called_with('payload_valid not implemented for %s', 'RemoteValue')

    def test_warn_to_knx(self):
        """Test for warning if to_knx is not implemented."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch('logging.Logger.warning') as mock_warn:
            remote_value.to_knx(23)
            mock_warn.assert_called_with('to_knx not implemented for %s', 'RemoteValue')

    def test_warn_from_knx(self):
        """Test for warning if from_knx is not implemented."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch('logging.Logger.warning') as mock_warn:
            remote_value.from_knx(DPTBinary(0))
            mock_warn.assert_called_with('from_knx not implemented for %s', 'RemoteValue')

    async def test_info_set_uninitialized(self):
        """Test for info if RemoteValue is not initialized."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch('logging.Logger.info') as mock_info:
            await asyncio.Task(remote_value.set(23))
            mock_info.assert_called_with('Setting value of uninitialized device: %s (value: %s)', 'Unknown', 23)

    async def test_info_set_unwritable(self):
        """Test for warning if RemoteValue is read only."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx, group_address_state=GroupAddress('1/2/3'))
        with patch('logging.Logger.warning') as mock_info:
            await asyncio.Task(remote_value.set(23))
            mock_info.assert_called_with('Attempted to set value for non-writable device: %s (value: %s)', 'Unknown', 23)

    def test_default_value_unit(self):
        """Test for the default value of unit_of_measurement."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        self.assertEqual(remote_value.unit_of_measurement, None)

    async def test_process_invalid_payload(self):
        """Test if exception is raised when processing telegram with invalid payload."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch('xknx.devices.RemoteValue.payload_valid') as patch_valid, \
                patch('xknx.devices.RemoteValue.has_group_address') as patch_has_group_address:
            patch_valid.return_value = False
            patch_has_group_address.return_value = True

            telegram = Telegram(
                GroupAddress('1/2/1'),
                payload=DPTArray((0x01, 0x02)))
            with self.assertRaises(CouldNotParseTelegram):
                await asyncio.Task(remote_value.process(telegram))

    def test_eq(self):
        """Test __eq__ operator."""
        xknx = XKNX()
        remote_value1 = RemoteValue(xknx, group_address=GroupAddress('1/1/1'))
        remote_value2 = RemoteValue(xknx, group_address=GroupAddress('1/1/1'))
        remote_value3 = RemoteValue(xknx, group_address=GroupAddress('1/1/2'))
        remote_value4 = RemoteValue(xknx, group_address=GroupAddress('1/1/1'))
        remote_value4.fnord = "fnord"

        def _callback():
            pass

        remote_value5 = RemoteValue(xknx, group_address=GroupAddress('1/1/1'), after_update_cb=_callback())

        self.assertEqual(remote_value1, remote_value2)
        self.assertEqual(remote_value2, remote_value1)
        self.assertNotEqual(remote_value1, remote_value3)
        self.assertNotEqual(remote_value3, remote_value1)
        self.assertNotEqual(remote_value1, remote_value4)
        self.assertNotEqual(remote_value4, remote_value1)
        self.assertEqual(remote_value1, remote_value5)
        self.assertEqual(remote_value5, remote_value1)
