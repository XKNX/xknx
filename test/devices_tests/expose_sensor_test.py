"""Unit test for Sensor objects."""
from unittest.mock import AsyncMock

from xknx import XKNX
from xknx.devices import ExposeSensor
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


class TestExposeSensor:
    """Test class for Sensor objects."""

    #
    # STR FUNCTIONS
    #
    async def test_str_binary(self):
        """Test resolve state with binary sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="binary"
        )
        await expose_sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(value=DPTBinary(1)),
            )
        )

        assert expose_sensor.resolve_state() is True
        assert expose_sensor.unit_of_measurement() is None

    async def test_str_percent(self):
        """Test resolve state with percent sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="percent"
        )

        await expose_sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x40,))),
            )
        )

        assert expose_sensor.resolve_state() == 25
        assert expose_sensor.unit_of_measurement() == "%"

    async def test_str_temperature(self):
        """Test resolve state with temperature sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="temperature"
        )

        await expose_sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x0C, 0x1A))),
            )
        )

        assert expose_sensor.resolve_state() == 21.0
        assert expose_sensor.unit_of_measurement() == "°C"

    #
    # TEST SET
    #
    async def test_set_binary(self):
        """Test set with binary sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="binary"
        )
        await expose_sensor.set(False)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

    async def test_set_percent(self):
        """Test set with percent sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="percent"
        )
        await expose_sensor.set(75)
        assert xknx.telegrams.qsize() == 1

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0xBF,))),
        )

    async def test_set_temperature(self):
        """Test set with temperature sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="temperature"
        )
        await expose_sensor.set(21.0)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0C, 0x1A))),
        )

    #
    # TEST PROCESS (GROUP READ)
    #
    async def test_process_binary(self):
        """Test reading binary expose sensor from bus."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", value_type="binary", group_address="1/2/3"
        )

        await expose_sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTBinary(True)),
            )
        )

        telegram = Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())
        await expose_sensor.process(telegram)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTBinary(True)),
        )

    async def test_process_percent(self):
        """Test reading percent expose sensor from bus."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", value_type="percent", group_address="1/2/3"
        )

        await expose_sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x40,))),
            )
        )

        telegram = Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())
        await expose_sensor.process(telegram)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTArray((0x40,))),
        )

    async def test_process_temperature(self):
        """Test reading temperature expose sensor from bus."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", value_type="temperature", group_address="1/2/3"
        )

        await expose_sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x0C, 0x1A))),
            )
        )

        telegram = Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())
        await expose_sensor.process(telegram)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTArray((0x0C, 0x1A))),
        )

    #
    # HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test expose sensor has group address."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", value_type="temperature", group_address="1/2/3"
        )
        assert expose_sensor.has_group_address(GroupAddress("1/2/3"))
        assert not expose_sensor.has_group_address(GroupAddress("1/2/4"))

    #
    # PROCESS CALLBACK
    #
    async def test_process_callback(self):
        """Test setting value. Test if callback is called."""

        xknx = XKNX()
        after_update_callback = AsyncMock()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="temperature"
        )
        expose_sensor.register_device_updated_cb(after_update_callback)

        await expose_sensor.set(21.0)
        await xknx.devices.process(xknx.telegrams.get_nowait())
        after_update_callback.assert_called_with(expose_sensor)
