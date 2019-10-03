"""Unit test for Switch objects."""
import asyncio
import unittest
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.devices import Device
from xknx.dpt import DPTArray
from xknx.exceptions import XKNXException
from xknx.telegram import GroupAddress, Telegram, TelegramType


class TestDevice(unittest.TestCase):
    """Test class for Switch object."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_state_addresses(self):
        """Test state_addresses() function."""
        xknx = XKNX(loop=self.loop)
        device = Device(xknx, 'TestDevice')
        self.assertEqual(device.state_addresses(), [])

    def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback was called."""
        xknx = XKNX(loop=self.loop)
        device = Device(xknx, 'TestDevice')

        after_update_callback1 = Mock()
        after_update_callback2 = Mock()

        async def async_after_update_callback1(device):
            """Async callback No. 1."""
            after_update_callback1(device)

        async def async_after_update_callback2(device):
            """Async callback No. 2."""
            after_update_callback2(device)

        device.register_device_updated_cb(async_after_update_callback1)
        device.register_device_updated_cb(async_after_update_callback2)

        # Triggering first time. Both have to be called
        self.loop.run_until_complete(asyncio.Task(device.after_update()))
        after_update_callback1.assert_called_with(device)
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Triggering 2nd time. Both have to be called
        self.loop.run_until_complete(asyncio.Task(device.after_update()))
        after_update_callback1.assert_called_with(device)
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering first callback
        device.unregister_device_updated_cb(async_after_update_callback1)
        self.loop.run_until_complete(asyncio.Task(device.after_update()))
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering second callback
        device.unregister_device_updated_cb(async_after_update_callback2)
        self.loop.run_until_complete(asyncio.Task(device.after_update()))
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_not_called()

    def test_process(self):
        """Test if telegram is handled by the correct process_* method."""
        xknx = XKNX(loop=self.loop)
        device = Device(xknx, 'TestDevice')

        with patch('xknx.devices.Device.process_group_read') as mock_group_read:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_group_read.return_value = fut
            telegram = Telegram(
                GroupAddress('1/2/1'),
                payload=DPTArray((0x01, 0x02)),
                telegramtype=TelegramType.GROUP_READ)
            self.loop.run_until_complete(asyncio.Task(device.process(telegram)))
            mock_group_read.assert_called_with(telegram)

        with patch('xknx.devices.Device.process_group_write') as mock_group_write:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_group_write.return_value = fut
            telegram = Telegram(
                GroupAddress('1/2/1'),
                payload=DPTArray((0x01, 0x02)),
                telegramtype=TelegramType.GROUP_WRITE)
            self.loop.run_until_complete(asyncio.Task(device.process(telegram)))
            mock_group_write.assert_called_with(telegram)

        with patch('xknx.devices.Device.process_group_response') as mock_group_response:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_group_response.return_value = fut
            telegram = Telegram(
                GroupAddress('1/2/1'),
                payload=DPTArray((0x01, 0x02)),
                telegramtype=TelegramType.GROUP_RESPONSE)
            self.loop.run_until_complete(asyncio.Task(device.process(telegram)))
            mock_group_response.assert_called_with(telegram)

    def test_process_group_write(self):
        """Test if process_group_write. Nothing really to test here."""
        xknx = XKNX(loop=self.loop)
        device = Device(xknx, 'TestDevice')
        self.loop.run_until_complete(asyncio.Task(device.process_group_write(Telegram())))

    def test_process_group_response(self):
        """Test if process_group_read. Testing if mapped to group_write."""
        xknx = XKNX(loop=self.loop)
        device = Device(xknx, 'TestDevice')
        with patch('xknx.devices.Device.process_group_write') as mock_group_write:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_group_write.return_value = fut
            self.loop.run_until_complete(asyncio.Task(device.process_group_response(Telegram())))
            mock_group_write.assert_called_with(Telegram())

    def test_process_group_read(self):
        """Test if process_group_read. Nothing really to test here."""
        xknx = XKNX(loop=self.loop)
        device = Device(xknx, 'TestDevice')
        self.loop.run_until_complete(asyncio.Task(device.process_group_read(Telegram())))

    def test_sync_exception(self):
        """Testing exception handling within sync()."""
        # pylint: disable=protected-access
        xknx = XKNX(loop=self.loop)
        device = Device(xknx, 'TestDevice')

        with patch('logging.Logger.error') as mock_error:
            with patch('xknx.devices.Device._sync_impl') as mock_sync_impl:
                fut = asyncio.Future()
                fut.set_result(None)
                mock_sync_impl.return_value = fut
                mock_sync_impl.side_effect = XKNXException()
                self.loop.run_until_complete(asyncio.Task(device.sync()))
                mock_sync_impl.assert_called_with(True)
                mock_error.assert_called_with('Error while syncing device: %s', XKNXException())

    def test_do(self):
        """Testing empty do."""
        xknx = XKNX(loop=self.loop)
        device = Device(xknx, 'TestDevice')
        with patch('logging.Logger.info') as mock_info:
            self.loop.run_until_complete(asyncio.Task(device.do("xx")))
            mock_info.assert_called_with("Do not implemented action '%s' for %s", 'xx', 'Device')

    #
    # _SYNC_IMPL()
    #
    def test_sync_no_response(self):
        """Testing _sync_impl() method with ValueReader returning no telegram as response."""
        # pylint: disable=protected-access
        xknx = XKNX(loop=self.loop)
        device = Device(xknx, 'TestDevice')
        with patch('xknx.devices.Device.state_addresses') as mock_state_addresses:
            mock_state_addresses.return_value = [GroupAddress('1/2/3'), ]
            with patch('xknx.core.ValueReader.read') as mock_value_reader_read:
                fut = asyncio.Future()
                fut.set_result(None)  # Make Value reader return no response
                mock_value_reader_read.return_value = fut
                with patch('logging.Logger.warning') as mock_warn:
                    self.loop.run_until_complete(asyncio.Task(device._sync_impl()))
                    mock_warn.assert_called_with("Could not sync group address '%s' from %s",
                                                 GroupAddress('1/2/3'), device)

    def test_sync_not_wait_for_response(self):
        """Testing _sync_impl() method without waiting for response (send_group_read should be called directly)."""
        # pylint: disable=protected-access
        xknx = XKNX(loop=self.loop)
        device = Device(xknx, 'TestDevice')
        with patch('xknx.devices.Device.state_addresses') as mock_state_addresses:
            mock_state_addresses.return_value = [GroupAddress('1/2/3'), ]
            with patch('xknx.core.ValueReader.send_group_read') as mock_value_reader_group_read:
                fut = asyncio.Future()
                fut.set_result(None)  # Make Value reader return no response
                mock_value_reader_group_read.return_value = fut
                self.loop.run_until_complete(asyncio.Task(device._sync_impl(wait_for_result=False)))
                mock_value_reader_group_read.assert_called_with()

    def test_sync_valid_response(self):
        """Testing _sync_imp() method with ValueReader.read returning a Telegram - which should be processed."""
        # pylint: disable=protected-access
        xknx = XKNX(loop=self.loop)
        device = Device(xknx, 'TestDevice')
        with patch('xknx.devices.Device.state_addresses') as mock_state_addresses:
            mock_state_addresses.return_value = [GroupAddress('1/2/3'), ]
            with patch('xknx.core.ValueReader.read') as mock_value_reader_read:
                fut = asyncio.Future()
                telegram = Telegram(GroupAddress("1/2/3"))
                fut.set_result(telegram)
                mock_value_reader_read.return_value = fut
                with patch('xknx.devices.Device.process') as mock_device_process:
                    fut2 = asyncio.Future()
                    fut2.set_result(None)
                    mock_device_process.return_value = fut2
                    self.loop.run_until_complete(asyncio.Task(device._sync_impl()))
                    mock_device_process.assert_called_with(telegram)
