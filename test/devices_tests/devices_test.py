"""Unit test for devices container within XKNX."""
from unittest.mock import AsyncMock, patch

import pytest
from xknx import XKNX
from xknx.devices import BinarySensor, Device, Devices, Light, Switch
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
        switch1 = Switch(xknx, "TestOutlet_1", group_address="1/2/3")
        light2 = Light(xknx, "Living-Room.Light_2", group_address_switch="1/6/8")
        switch2 = Switch(xknx, "TestOutlet_2", group_address="1/2/4")

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
        devices = Devices()

        light1 = Light(xknx, "Livingroom", group_address_switch="1/6/7")
        sensor1 = BinarySensor(xknx, "Diningroom", group_address_state="3/0/1")
        sensor2 = BinarySensor(xknx, "Diningroom", group_address_state="3/0/1")
        light2 = Light(xknx, "Livingroom", group_address_switch="1/6/8")
        devices.add(light1)
        devices.add(sensor1)
        devices.add(sensor2)
        devices.add(light2)

        assert tuple(devices.devices_by_group_address(GroupAddress("1/6/7"))) == (
            light1,
        )
        assert tuple(devices.devices_by_group_address(GroupAddress("1/6/8"))) == (
            light2,
        )
        assert tuple(devices.devices_by_group_address(GroupAddress("3/0/1"))) == (
            sensor1,
            sensor2,
        )

    def test_iter(self):
        """Test __iter__() function."""
        xknx = XKNX()
        devices = Devices()

        light1 = Light(xknx, "Livingroom", group_address_switch="1/6/7")
        sensor1 = BinarySensor(xknx, "Diningroom", group_address_state="3/0/1")
        sensor2 = BinarySensor(xknx, "Diningroom", group_address_state="3/0/1")
        light2 = Light(xknx, "Livingroom", group_address_switch="1/6/8")
        devices.add(light1)
        devices.add(sensor1)
        devices.add(sensor2)
        devices.add(light2)

        assert tuple(devices.__iter__()) == (light1, sensor1, sensor2, light2)

    def test_len(self):
        """Test len() function."""
        xknx = XKNX()
        assert len(xknx.devices) == 0

        Light(xknx, "Living-Room.Light_1", group_address_switch="1/6/7")
        assert len(xknx.devices) == 1

        BinarySensor(xknx, "DiningRoom.Motion.Sensor", group_address_state="3/0/1")
        assert len(xknx.devices) == 2

        BinarySensor(xknx, "DiningRoom.Motion.Sensor", group_address_state="3/0/1")
        assert len(xknx.devices) == 3

        Light(xknx, "Living-Room.Light_2", group_address_switch="1/6/8")
        assert len(xknx.devices) == 4

    def test_contains(self):
        """Test __contains__() function."""
        xknx = XKNX()
        Light(xknx, "Living-Room.Light_1", group_address_switch="1/6/7")
        Light(xknx, "Living-Room.Light_2", group_address_switch="1/6/8")

        assert "Living-Room.Light_1" in xknx.devices
        assert "Living-Room.Light_2" in xknx.devices
        assert "Living-Room.Light_3" not in xknx.devices

    @patch.multiple(Device, __abstractmethods__=set())
    def test_add_remove(self):
        """Tesst add and remove functions."""
        xknx = XKNX()
        device1 = Device(xknx, "TestDevice1")
        device2 = Device(xknx, "TestDevice2")
        assert len(xknx.devices) == 2
        device1.shutdown()
        assert len(xknx.devices) == 1
        assert "TestDevice1" not in xknx.devices
        device2.shutdown()
        assert len(xknx.devices) == 0

    async def test_modification_of_device(self):
        """Test if devices object does store references and not copies of objects."""
        xknx = XKNX()
        light1 = Light(xknx, "Living-Room.Light_1", group_address_switch="1/6/7")
        for device in xknx.devices:
            await device.set_on()
            await xknx.devices.process(xknx.telegrams.get_nowait())
        assert light1.state

        device2 = xknx.devices["Living-Room.Light_1"]
        await device2.set_off()
        await xknx.devices.process(xknx.telegrams.get_nowait())
        assert not light1.state

        for device in xknx.devices.devices_by_group_address(GroupAddress("1/6/7")):
            await device.set_on()
            await xknx.devices.process(xknx.telegrams.get_nowait())
        assert light1.state

    def test_add_wrong_type(self):
        """Test if exception is raised when wrong type of devices is added."""
        xknx = XKNX()
        with pytest.raises(TypeError):
            xknx.devices.add("fnord")

    #
    # TEST SYNC
    #
    @patch.multiple(Device, __abstractmethods__=set())
    async def test_sync(self):
        """Test sync function."""
        xknx = XKNX()
        Device(xknx, "TestDevice1")
        Device(xknx, "TestDevice2")
        with patch("xknx.devices.Device.sync", new_callable=AsyncMock) as mock_sync:
            await xknx.devices.sync()
            assert mock_sync.call_count == 2

    #
    # TEST CALLBACK
    #
    @patch.multiple(Device, __abstractmethods__=set())
    async def test_device_updated_callback(self):
        """Test if device updated callback is called correctly if device was updated."""
        xknx = XKNX()
        device1 = Device(xknx, "TestDevice1")
        device2 = Device(xknx, "TestDevice2")

        async_after_update_callback1 = AsyncMock()
        async_after_update_callback2 = AsyncMock()

        # Registering both callbacks
        xknx.devices.register_device_updated_cb(async_after_update_callback1)
        xknx.devices.register_device_updated_cb(async_after_update_callback2)

        # Triggering first device. Both callbacks to be called
        await device1.after_update()
        async_after_update_callback1.assert_called_with(device1)
        async_after_update_callback2.assert_called_with(device1)
        async_after_update_callback1.reset_mock()
        async_after_update_callback2.reset_mock()

        # Triggering 2nd device. Both callbacks have to be called
        await device2.after_update()
        async_after_update_callback1.assert_called_with(device2)
        async_after_update_callback2.assert_called_with(device2)
        async_after_update_callback1.reset_mock()
        async_after_update_callback2.reset_mock()

        # Unregistering first callback
        xknx.devices.unregister_device_updated_cb(async_after_update_callback1)

        # Triggering first device. Only second callback has to be called
        await device1.after_update()
        async_after_update_callback1.assert_not_called()
        async_after_update_callback2.assert_called_with(device1)
        async_after_update_callback1.reset_mock()
        async_after_update_callback2.reset_mock()

        # Unregistering second callback
        xknx.devices.unregister_device_updated_cb(async_after_update_callback2)

        # Triggering second device. No callback should be called
        await device2.after_update()
        async_after_update_callback1.assert_not_called()
        async_after_update_callback2.assert_not_called()
        async_after_update_callback1.reset_mock()
        async_after_update_callback2.reset_mock()
