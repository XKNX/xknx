"""Unit test for RemoveValue objects."""
import asyncio
import unittest
from unittest.mock import MagicMock, patch

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.remote_value import RemoteValue, RemoteValueSwitch
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


@patch.multiple(RemoteValue, __abstractmethods__=set())
class TestRemoteValue(unittest.TestCase):
    """Test class for RemoteValue objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_info_set_uninitialized(self):
        """Test for info if RemoteValue is not initialized."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch("logging.Logger.info") as mock_info:
            self.loop.run_until_complete(remote_value.set(23))
            mock_info.assert_called_with(
                "Setting value of uninitialized device: %s - %s (value: %s)",
                "Unknown",
                "Unknown",
                23,
            )

    def test_info_set_unwritable(self):
        """Test for warning if RemoteValue is read only."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx, group_address_state=GroupAddress("1/2/3"))
        with patch("logging.Logger.warning") as mock_info:
            self.loop.run_until_complete(remote_value.set(23))
            mock_info.assert_called_with(
                "Attempted to set value for non-writable device: %s - %s (value: %s)",
                "Unknown",
                "Unknown",
                23,
            )

    def test_default_value_unit(self):
        """Test for the default value of unit_of_measurement."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        self.assertEqual(remote_value.unit_of_measurement, None)

    def test_process_unsupported_payload(self):
        """Test if exception is raised when processing telegram with unsupported payload."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch("xknx.remote_value.RemoteValue.payload_valid") as patch_valid, patch(
            "xknx.remote_value.RemoteValue.has_group_address"
        ) as patch_has_group_address:
            patch_valid.return_value = False
            patch_has_group_address.return_value = True

            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=object(),
            )
            with self.assertRaisesRegex(
                CouldNotParseTelegram,
                r".*payload not a GroupValueWrite or GroupValueResponse.*",
            ):
                self.loop.run_until_complete(remote_value.process(telegram))

    def test_process_invalid_payload(self):
        """Test if exception is raised when processing telegram with invalid payload."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch("xknx.remote_value.RemoteValue.payload_valid") as patch_valid, patch(
            "xknx.remote_value.RemoteValue.has_group_address"
        ) as patch_has_group_address:
            patch_valid.return_value = None
            patch_has_group_address.return_value = True

            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTArray((0x01, 0x02))),
            )
            with self.assertRaisesRegex(CouldNotParseTelegram, r".*payload invalid.*"):
                self.loop.run_until_complete(remote_value.process(telegram))

    def test_read_state(self):
        """Test read state while waiting for the result."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, group_address_state="1/2/3")

        with patch("xknx.remote_value.RemoteValue.payload_valid") as patch_valid, patch(
            "xknx.core.ValueReader.read", new_callable=MagicMock
        ) as patch_read:
            patch_valid.return_value = True

            fut = asyncio.Future()
            telegram = Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTBinary(1)),
            )
            fut.set_result(telegram)
            patch_read.return_value = fut

            self.loop.run_until_complete(remote_value.read_state(wait_for_result=True))

            self.assertTrue(remote_value.value)

    def test_read_state_none(self):
        """Test read state while waiting for the result but got None."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, group_address_state="1/2/3")

        with patch("xknx.remote_value.RemoteValue.payload_valid") as patch_valid, patch(
            "xknx.core.ValueReader.read", new_callable=MagicMock
        ) as patch_read, patch("logging.Logger.warning") as mock_info:
            fut = asyncio.Future()
            fut.set_result(None)
            patch_valid.return_value = False
            patch_read.return_value = fut

            self.loop.run_until_complete(remote_value.read_state(wait_for_result=True))

            mock_info.assert_called_with(
                "Could not sync group address '%s' (%s - %s)",
                GroupAddress("1/2/3"),
                "Unknown",
                "State",
            )

    def test_process_listening_address(self):
        """Test if listening group addresses are processed."""
        xknx = XKNX()
        remote_value = RemoteValue(
            xknx, group_address="1/2/3", passive_group_addresses=["1/1/1"]
        )
        self.assertTrue(remote_value.writable)
        self.assertFalse(remote_value.readable)
        # RemoteValue is initialized with only passive group address
        self.assertTrue(remote_value.initialized)
        with patch("xknx.remote_value.RemoteValue.payload_valid") as patch_always_valid:
            patch_always_valid.side_effect = lambda payload: payload
            test_payload = DPTArray((0x01, 0x02))
            telegram = Telegram(
                destination_address=GroupAddress("1/1/1"),
                payload=GroupValueWrite(test_payload),
            )
            self.assertTrue(
                self.loop.run_until_complete(
                    asyncio.Task(remote_value.process(telegram))
                )
            )
            self.assertEqual(remote_value.payload, test_payload)

    def test_eq(self):
        """Test __eq__ operator."""
        xknx = XKNX()
        remote_value1 = RemoteValue(xknx, group_address=GroupAddress("1/1/1"))
        remote_value2 = RemoteValue(xknx, group_address=GroupAddress("1/1/1"))
        remote_value3 = RemoteValue(xknx, group_address=GroupAddress("1/1/2"))
        remote_value4 = RemoteValue(xknx, group_address=GroupAddress("1/1/1"))
        remote_value4.fnord = "fnord"

        def _callback():
            pass

        remote_value5 = RemoteValue(
            xknx, group_address=GroupAddress("1/1/1"), after_update_cb=_callback()
        )

        self.assertEqual(remote_value1, remote_value2)
        self.assertEqual(remote_value2, remote_value1)
        self.assertNotEqual(remote_value1, remote_value3)
        self.assertNotEqual(remote_value3, remote_value1)
        self.assertNotEqual(remote_value1, remote_value4)
        self.assertNotEqual(remote_value4, remote_value1)
        self.assertEqual(remote_value1, remote_value5)
        self.assertEqual(remote_value5, remote_value1)
