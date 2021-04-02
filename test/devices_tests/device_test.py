"""Unit test for Switch objects."""
from unittest.mock import AsyncMock, patch

import pytest
from xknx import XKNX
from xknx.devices import Device, Sensor
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


@pytest.mark.asyncio
@patch.multiple(Device, __abstractmethods__=set())
class TestDevice:
    """Test class for Switch object."""

    async def test_device_updated_cb(self):
        """Test device updated cb is added to the device."""
        xknx = XKNX()
        after_update_callback = AsyncMock()
        device = Device(xknx, "TestDevice", device_updated_cb=after_update_callback)

        await device.after_update()
        after_update_callback.assert_called_with(device)

    async def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback was called."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        after_update_callback1 = AsyncMock()
        after_update_callback2 = AsyncMock()
        device.register_device_updated_cb(after_update_callback1)
        device.register_device_updated_cb(after_update_callback2)

        # Triggering first time. Both have to be called
        await device.after_update()
        after_update_callback1.assert_called_with(device)
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Triggering 2nd time. Both have to be called
        await device.after_update()
        after_update_callback1.assert_called_with(device)
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering first callback
        device.unregister_device_updated_cb(after_update_callback1)
        await device.after_update()
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering second callback
        device.unregister_device_updated_cb(after_update_callback2)
        await device.after_update()
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_not_called()

    async def test_process(self):
        """Test if telegram is handled by the correct process_* method."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")

        with patch(
            "xknx.devices.Device.process_group_read", new_callable=AsyncMock
        ) as mock_group_read:
            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"), payload=GroupValueRead()
            )
            await device.process(telegram)
            mock_group_read.assert_called_with(telegram)

        with patch(
            "xknx.devices.Device.process_group_write", new_callable=AsyncMock
        ) as mock_group_write:
            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTArray((0x01, 0x02))),
            )
            await device.process(telegram)
            mock_group_write.assert_called_with(telegram)

        with patch(
            "xknx.devices.Device.process_group_response", new_callable=AsyncMock
        ) as mock_group_response:
            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueResponse(DPTArray((0x01, 0x02))),
            )
            await device.process(telegram)
            mock_group_response.assert_called_with(telegram)

    async def test_sync_with_wait(self):
        """Test sync with wait_for_result=True."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, "Sensor", group_address_state="1/2/3", value_type="wind_speed_ms"
        )

        with patch(
            "xknx.remote_value.RemoteValue.read_state", new_callable=AsyncMock
        ) as read_state_mock:
            await sensor.sync(wait_for_result=True)
            read_state_mock.assert_called_with(wait_for_result=True)

    async def test_process_group_write(self):
        """Test if process_group_write. Nothing really to test here."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        await device.process_group_write(Telegram())

    async def test_process_group_response(self):
        """Test if process_group_read. Testing if mapped to group_write."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        with patch(
            "xknx.devices.Device.process_group_write", new_callable=AsyncMock
        ) as mock_group_write:
            await device.process_group_response(Telegram())
            mock_group_write.assert_called_with(Telegram())

    async def test_process_group_read(self):
        """Test if process_group_read. Nothing really to test here."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        await device.process_group_read(Telegram())

    async def test_do(self):
        """Testing empty do."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        with patch("logging.Logger.info") as mock_info:
            await device.do("xx")
            mock_info.assert_called_with(
                "'do()' not implemented for action '%s' of %s", "xx", "Device"
            )

    def test_unique_id(self):
        """Test unique id functionality."""
        xknx = XKNX()
        device = Device(xknx, "Test")
        assert device.unique_id is None
