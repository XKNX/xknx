"""Unit test for NumericValue objects."""
from unittest.mock import AsyncMock

import pytest
from xknx import XKNX
from xknx.devices import NumericValue
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


@pytest.mark.asyncio
class TestNumericValue:
    """Test class for NumericValue objects."""

    @pytest.mark.parametrize(
        "value_type,raw_payload,expected_state",
        [
            # DPT-14 values are according to ETS group monitor values
            (
                "absolute_temperature",
                DPTArray((0x44, 0xD7, 0xD2, 0x8B)),
                1726.579,
            ),
            (
                "angle",
                DPTArray((0xE4,)),
                322,
            ),
            (
                "brightness",
                DPTArray((0xC3, 0x56)),
                50006,
            ),
            (
                "color_temperature",
                DPTArray((0x6C, 0x95)),
                27797,
            ),
            (
                "counter_pulses",
                DPTArray((0x9D,)),
                -99,
            ),
            (
                "current",
                DPTArray((0xCA, 0xCC)),
                51916,
            ),
            (
                "percent",
                DPTArray((0xE3,)),
                89,
            ),
            (
                "percentU8",
                DPTArray((0x6B,)),
                107,
            ),
            (
                "percentV8",
                DPTArray((0x20,)),
                32,
            ),
            (
                "percentV16",
                DPTArray((0x8A, 0x2F)),
                -30161,
            ),
            (
                "pulse",
                DPTArray((0xFC,)),
                252,
            ),
            (
                "scene_number",
                DPTArray((0x1,)),
                2,
            ),
        ],
    )
    async def test_sensor_value_types(
        self,
        value_type,
        raw_payload,
        expected_state,
    ):
        """Test sensor value types."""
        xknx = XKNX()
        sensor = NumericValue(
            xknx,
            "TestSensor",
            group_address="1/2/3",
            value_type=value_type,
        )
        await sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(value=raw_payload),
            )
        )

        assert sensor.resolve_state() == expected_state

    async def test_manage_state(self):
        """Test manage_state function."""
        xknx = XKNX()
        managed = NumericValue(
            xknx,
            "TestSensor",
            group_address="1/1/1",
            manage_state=True,
            value_type="volume_liquid_litre",
        )
        unmanaged = NumericValue(
            xknx,
            "TestSensor",
            group_address="1/1/1",
            manage_state=False,
            value_type="volume_liquid_litre",
        )
        #  set initial payload of NumericValue
        managed.sensor_value.value = 256
        unmanaged.sensor_value.value = 256

        read_telegram = Telegram(
            destination_address=GroupAddress("1/1/1"), payload=GroupValueRead()
        )
        # verify no response when manage_state is False
        await unmanaged.process(read_telegram)
        assert xknx.telegrams.qsize() == 0

        # verify response when manage_state is True
        await managed.process(read_telegram)
        assert xknx.telegrams.qsize() == 1
        response = xknx.telegrams.get_nowait()
        assert response == Telegram(
            destination_address=GroupAddress("1/1/1"),
            payload=GroupValueResponse(DPTArray((0x00, 0x00, 0x01, 0x00))),
        )

    #
    # TEST SET
    #
    async def test_set_percent(self):
        """Test set with percent numeric value."""
        xknx = XKNX()
        num_value = NumericValue(
            xknx, "TestSensor", group_address="1/2/3", value_type="percent"
        )
        await num_value.set(75)
        assert xknx.telegrams.qsize() == 1

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0xBF,))),
        )

    async def test_set_temperature(self):
        """Test set with temperature numeric value."""
        xknx = XKNX()
        num_value = NumericValue(
            xknx, "TestSensor", group_address="1/2/3", value_type="temperature"
        )
        await num_value.set(21.0)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0C, 0x1A))),
        )
        # test HomeAssistant device class
        assert num_value.ha_device_class() == "temperature"

    #
    # SYNC
    #
    async def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        sensor = NumericValue(
            xknx, "TestSensor", value_type="temperature", group_address_state="1/2/3"
        )
        await sensor.sync()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )

    #
    # TEST PROCESS
    #
    async def test_process(self):
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        sensor = NumericValue(
            xknx, "TestSensor", value_type="temperature", group_address="1/2/3"
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x06, 0xA0))),
        )
        await sensor.process(telegram)
        assert sensor.sensor_value.value == 16.96
        assert sensor.sensor_value.telegram.payload.value == DPTArray((0x06, 0xA0))
        assert sensor.resolve_state() == 16.96

    async def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback is called."""

        xknx = XKNX()
        sensor = NumericValue(
            xknx, "TestSensor", group_address="1/2/3", value_type="temperature"
        )
        after_update_callback = AsyncMock()
        sensor.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x01, 0x02))),
        )
        await sensor.process(telegram)
        after_update_callback.assert_called_with(sensor)
        assert sensor.last_telegram == telegram

    async def test_process_callback_set(self):
        """Test setting value. Test if callback is called."""

        xknx = XKNX()
        after_update_callback = AsyncMock()
        num_value = NumericValue(
            xknx, "TestSensor", group_address="1/2/3", value_type="temperature"
        )
        num_value.register_device_updated_cb(after_update_callback)

        await num_value.set(21.0)
        await xknx.devices.process(xknx.telegrams.get_nowait())
        after_update_callback.assert_called_with(num_value)

    def test_string(self):
        """Test NumericValue string representation."""

        xknx = XKNX()
        value = NumericValue(
            xknx, "Num", group_address="1/2/3", value_type="temperature"
        )
        value.sensor_value.value = 4.9
        assert (
            str(value)
            == '<NumericValue name="Num" addresses=<1/2/3, None, [], 4.9 /> value=4.9 unit="°C"/>'
        )
