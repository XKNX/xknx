"""Unit test for Switch objects."""

from unittest.mock import AsyncMock, Mock, patch

from xknx import XKNX
from xknx.devices import Device, Sensor
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


@patch.multiple(Device, __abstractmethods__=set())
class TestDevice:
    """Test class for Switch object."""

    def test_device_updated_cb(self) -> None:
        """Test device updated cb is added to the device."""
        xknx = XKNX()
        after_update_callback = Mock()
        device = Device(xknx, "TestDevice", device_updated_cb=after_update_callback)

        device.after_update()
        after_update_callback.assert_called_with(device)

    def test_process_callback(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if callback was called."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        after_update_callback1 = Mock()
        after_update_callback2 = Mock()
        device.register_device_updated_cb(after_update_callback1)
        device.register_device_updated_cb(after_update_callback2)

        # Triggering first time. Both have to be called
        device.after_update()
        after_update_callback1.assert_called_with(device)
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Triggering 2nd time. Both have to be called
        device.after_update()
        after_update_callback1.assert_called_with(device)
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering first callback
        device.unregister_device_updated_cb(after_update_callback1)
        device.after_update()
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_called_with(device)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering second callback
        device.unregister_device_updated_cb(after_update_callback2)
        device.after_update()
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_not_called()

    @patch("logging.Logger.exception")
    def test_bad_callback(self, logging_exception_mock: Mock) -> None:
        """Test handling callback raising an exception."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        good_callback_1 = Mock()
        bad_callback = Mock(side_effect=Exception("Boom"))
        good_callback_2 = Mock()

        device.register_device_updated_cb(good_callback_1)
        device.register_device_updated_cb(bad_callback)
        device.register_device_updated_cb(good_callback_2)

        device.after_update()
        good_callback_1.assert_called_with(device)
        bad_callback.assert_called_with(device)
        good_callback_2.assert_called_with(device)

        logging_exception_mock.assert_called_once_with(
            "Unexpected error while processing device_updated_cb for %s",
            device,
        )

    async def test_process(self) -> None:
        """Test if telegram is handled by the correct process_* method."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")

        with patch("xknx.devices.Device.process_group_read") as mock_group_read:
            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"), payload=GroupValueRead()
            )
            device.process(telegram)
            mock_group_read.assert_called_with(telegram)

        with patch("xknx.devices.Device.process_group_write") as mock_group_write:
            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTArray((0x01, 0x02))),
            )
            device.process(telegram)
            mock_group_write.assert_called_with(telegram)

        with patch("xknx.devices.Device.process_group_response") as mock_group_response:
            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueResponse(DPTArray((0x01, 0x02))),
            )
            device.process(telegram)
            mock_group_response.assert_called_with(telegram)

    async def test_sync_with_wait(self) -> None:
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

    async def test_process_group_write(self) -> None:
        """Test if process_group_write. Nothing really to test here."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        device.process_group_write(Telegram(destination_address=GroupAddress(1)))

    async def test_process_group_response(self) -> None:
        """Test if process_group_read. Testing if mapped to group_write."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        with patch("xknx.devices.Device.process_group_write") as mock_group_write:
            device.process_group_response(Telegram(destination_address=GroupAddress(1)))
            mock_group_write.assert_called_with(
                Telegram(destination_address=GroupAddress(1))
            )

    async def test_process_group_read(self) -> None:
        """Test if process_group_read. Nothing really to test here."""
        xknx = XKNX()
        device = Device(xknx, "TestDevice")
        device.process_group_read(Telegram(destination_address=GroupAddress(1)))
