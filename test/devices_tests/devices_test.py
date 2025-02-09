"""Unit test for devices container within XKNX."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from xknx import XKNX
from xknx.devices import BinarySensor, Device, Light, Switch
from xknx.telegram import GroupAddress


class TestDevices:
    """Test class for devices container within XKNX."""

    #
    # XKNX Config
    #
    def test_get_item(self):
        """Test get item by name or by index."""
        xknx = XKNX()
        light1 = Light(xknx, "Living-Room.Light_1", group_address_switch="1/6/7")
        xknx.devices.async_add(light1)
        switch1 = Switch(xknx, "TestOutlet_1", group_address="1/2/3")
        xknx.devices.async_add(switch1)
        light2 = Light(xknx, "Living-Room.Light_2", group_address_switch="1/6/8")
        xknx.devices.async_add(light2)
        switch2 = Switch(xknx, "TestOutlet_2", group_address="1/2/4")
        xknx.devices.async_add(switch2)

        assert xknx.devices["Living-Room.Light_1"] == light1
        assert xknx.devices["TestOutlet_1"] == switch1
        assert xknx.devices["Living-Room.Light_2"] == light2
        assert xknx.devices["TestOutlet_2"] == switch2
        with pytest.raises(KeyError):
            # pylint: disable=pointless-statement
            xknx.devices["TestOutlet_2sdds"]

        assert xknx.devices[0] == light1
        assert xknx.devices[1] == switch1
        assert xknx.devices[2] == light2
        assert xknx.devices[3] == switch2
        with pytest.raises(IndexError):
            # pylint: disable=pointless-statement
            xknx.devices[4]

    def test_device_by_group_address(self):
        """Test get devices by group address."""
        xknx = XKNX()

        light1 = Light(xknx, "Livingroom", group_address_switch="1/6/7")
        sensor1 = BinarySensor(xknx, "Diningroom", group_address_state="3/0/1")
        sensor2 = BinarySensor(xknx, "Diningroom", group_address_state="3/0/1")
        light2 = Light(xknx, "Livingroom", group_address_switch="1/6/8")
        xknx.devices.async_add(light1)
        xknx.devices.async_add(sensor1)
        xknx.devices.async_add(sensor2)
        xknx.devices.async_add(light2)

        assert tuple(xknx.devices.devices_by_group_address(GroupAddress("1/6/7"))) == (
            light1,
        )
        assert tuple(xknx.devices.devices_by_group_address(GroupAddress("1/6/8"))) == (
            light2,
        )
        assert tuple(xknx.devices.devices_by_group_address(GroupAddress("3/0/1"))) == (
            sensor1,
            sensor2,
        )

    def test_iter(self):
        """Test __iter__() function."""
        xknx = XKNX()

        light1 = Light(xknx, "Livingroom", group_address_switch="1/6/7")
        sensor1 = BinarySensor(xknx, "Diningroom", group_address_state="3/0/1")
        sensor2 = BinarySensor(xknx, "Diningroom", group_address_state="3/0/1")
        light2 = Light(xknx, "Livingroom", group_address_switch="1/6/8")
        xknx.devices.async_add(light1)
        xknx.devices.async_add(sensor1)
        xknx.devices.async_add(sensor2)
        xknx.devices.async_add(light2)

        assert tuple(iter(xknx.devices)) == (light1, sensor1, sensor2, light2)

    def test_len(self):
        """Test len() function."""
        xknx = XKNX()
        assert len(xknx.devices) == 0

        light = Light(xknx, "Living-Room.Light_1", group_address_switch="1/6/7")
        xknx.devices.async_add(light)
        assert len(xknx.devices) == 1

        binary_sensor = BinarySensor(
            xknx, "DiningRoom.Motion.Sensor", group_address_state="3/0/1"
        )
        xknx.devices.async_add(binary_sensor)
        assert len(xknx.devices) == 2

        xknx.devices.async_remove(light)
        assert len(xknx.devices) == 1

        xknx.devices.async_add(light)
        assert len(xknx.devices) == 2

    def test_contains(self):
        """Test __contains__() function."""
        xknx = XKNX()
        xknx.devices.async_add(
            Light(xknx, "Living-Room.Light_1", group_address_switch="1/6/7")
        )
        xknx.devices.async_add(
            Light(xknx, "Living-Room.Light_2", group_address_switch="1/6/8")
        )

        assert "Living-Room.Light_1" in xknx.devices
        assert "Living-Room.Light_2" in xknx.devices
        assert "Living-Room.Light_3" not in xknx.devices

    @patch.multiple(Device, __abstractmethods__=set())
    def test_add_remove(self):
        """Tesst add and remove functions."""
        xknx = XKNX()
        device1 = Device(xknx, "TestDevice1")
        device2 = Device(xknx, "TestDevice2")
        xknx.devices.async_add(device1)
        xknx.devices.async_add(device2)
        assert len(xknx.devices) == 2
        xknx.devices.async_remove(device1)
        assert len(xknx.devices) == 1
        assert "TestDevice1" not in xknx.devices
        xknx.devices.async_remove(device2)
        assert len(xknx.devices) == 0

    async def test_modification_of_device(self):
        """Test if devices object does store references and not copies of objects."""
        xknx = XKNX()
        light1 = Light(xknx, "Living-Room.Light_1", group_address_switch="1/6/7")
        xknx.devices.async_add(light1)
        for device in xknx.devices:
            await device.set_on()
            xknx.devices.process(xknx.telegrams.get_nowait())
        assert light1.state

        device2 = xknx.devices["Living-Room.Light_1"]
        await device2.set_off()
        xknx.devices.process(xknx.telegrams.get_nowait())
        assert not light1.state

        for device in xknx.devices.devices_by_group_address(GroupAddress("1/6/7")):
            await device.set_on()
            xknx.devices.process(xknx.telegrams.get_nowait())
        assert light1.state

    #
    # TEST SYNC
    #
    @patch.multiple(Device, __abstractmethods__=set())
    async def test_sync(self):
        """Test sync function."""
        xknx = XKNX()
        xknx.devices.async_add(Device(xknx, "TestDevice1"))
        xknx.devices.async_add(Device(xknx, "TestDevice2"))
        with patch("xknx.devices.Device.sync", new_callable=AsyncMock) as mock_sync:
            await xknx.devices.sync()
            assert mock_sync.call_count == 2

    #
    # TEST CALLBACK
    #
    @patch.multiple(Device, __abstractmethods__=set())
    def test_device_updated_callback(self):
        """Test if device updated callback is called correctly if device was updated."""
        xknx = XKNX()
        device1 = Device(xknx, "TestDevice1")
        device2 = Device(xknx, "TestDevice2")
        xknx.devices.async_add(device1)
        xknx.devices.async_add(device2)

        after_update_callback1 = Mock()
        after_update_callback2 = Mock()

        # Registering both callbacks
        xknx.devices.register_device_updated_cb(after_update_callback1)
        xknx.devices.register_device_updated_cb(after_update_callback2)

        # Triggering first device. Both callbacks to be called
        device1.after_update()
        after_update_callback1.assert_called_with(device1)
        after_update_callback2.assert_called_with(device1)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Triggering 2nd device. Both callbacks have to be called
        device2.after_update()
        after_update_callback1.assert_called_with(device2)
        after_update_callback2.assert_called_with(device2)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering first callback
        xknx.devices.unregister_device_updated_cb(after_update_callback1)

        # Triggering first device. Only second callback has to be called
        device1.after_update()
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_called_with(device1)
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()

        # Unregistering second callback
        xknx.devices.unregister_device_updated_cb(after_update_callback2)

        # Triggering second device. No callback should be called
        device2.after_update()
        after_update_callback1.assert_not_called()
        after_update_callback2.assert_not_called()
        after_update_callback1.reset_mock()
        after_update_callback2.reset_mock()
