"""Unit test for Switch objects."""
import asyncio
import unittest
from unittest.mock import MagicMock, Mock, patch

from xknx import XKNX
from xknx.devices import Device, Sensor
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


@patch.multiple(Device, __abstractmethods__=set())
class TestDevice(unittest.TestCase):
    """Test class for Switch object."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_device_updated_cb(self):
        """Test device updated cb is added to the device."""
        xknx = XKNX()

        after_update_callback = Mock()

        async def async_after_update_callback(device1):
            """Async callback"""
            after_update_callback(device1)

        device = Device(
            xknx, "TestDevice", device_updated_cb=async_after_update_callback
        )

        self.loop.run_until_complete(device.after_update())
        after_update_callback.assert_called_with(device)

    def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback was called."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")

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
        self.loop.run_until_complete(device.after_update())
        after_update_callback1.assert_called_with(device)
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Triggering 2nd time. Both have to be called
        self.loop.run_until_complete(device.after_update())
        after_update_callback1.assert_called_with(device)
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering first callback
        device.unregister_device_updated_cb(async_after_update_callback1)
        self.loop.run_until_complete(device.after_update())
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering second callback
        device.unregister_device_updated_cb(async_after_update_callback2)
        self.loop.run_until_complete(device.after_update())
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_not_called()

    def test_process(self):
        """Test if telegram is handled by the correct process_* method."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")

        with patch("xknx.devices.Device.process_group_read") as mock_group_read:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_group_read.return_value = fut
            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"), payload=GroupValueRead()
            )
            self.loop.run_until_complete(device.process(telegram))
            mock_group_read.assert_called_with(telegram)

        with patch("xknx.devices.Device.process_group_write") as mock_group_write:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_group_write.return_value = fut
            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTArray((0x01, 0x02))),
            )
            self.loop.run_until_complete(device.process(telegram))
            mock_group_write.assert_called_with(telegram)

        with patch("xknx.devices.Device.process_group_response") as mock_group_response:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_group_response.return_value = fut
            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueResponse(DPTArray((0x01, 0x02))),
            )
            self.loop.run_until_complete(device.process(telegram))
            mock_group_response.assert_called_with(telegram)

    def test_sync_with_wait(self):
        """Test sync with wait_for_result=True."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "Sensor", group_address_state="1/2/3", value_type="wind_speed_ms"
        )

        with patch(
            "xknx.remote_value.RemoteValue.read_state", new_callable=MagicMock
        ) as read_state_mock:
            fut = asyncio.Future()
            fut.set_result(None)
            read_state_mock.return_value = fut
            self.loop.run_until_complete(sensor.sync(wait_for_result=True))

            read_state_mock.assert_called_with(wait_for_result=True)

    def test_process_group_write(self):
        """Test if process_group_write. Nothing really to test here."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        self.loop.run_until_complete(device.process_group_write(Telegram()))

    def test_process_group_response(self):
        """Test if process_group_read. Testing if mapped to group_write."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        with patch("xknx.devices.Device.process_group_write") as mock_group_write:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_group_write.return_value = fut
            self.loop.run_until_complete(device.process_group_response(Telegram()))

            mock_group_write.assert_called_with(Telegram())

    def test_process_group_read(self):
        """Test if process_group_read. Nothing really to test here."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        self.loop.run_until_complete(device.process_group_read(Telegram()))

    def test_do(self):
        """Testing empty do."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        with patch("logging.Logger.info") as mock_info:
            self.loop.run_until_complete(device.do("xx"))
            mock_info.assert_called_with(
                "'do()' not implemented for action '%s' of %s", "xx", "Device"
            )

    def test_unique_id(self):
        """Test unique id functionality."""
        xknx = XKNX()
        device = Device(xknx, "Test")
        self.assertIsNone(device.unique_id)
