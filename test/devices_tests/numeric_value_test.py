"""Unit test for NumericValue objects."""

from unittest.mock import Mock

import pytest

from xknx import XKNX
from xknx.devices import NumericValue
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


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
                -301.61,
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
        value_type: str,
        raw_payload: DPTArray,
        expected_state: int,
    ) -> None:
        """Test sensor value types."""
        xknx = XKNX()
        sensor = NumericValue(
            xknx,
            "TestSensor",
            group_address="1/2/3",
            value_type=value_type,
        )
        sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(value=raw_payload),
            )
        )

        assert sensor.resolve_state() == expected_state

    #
    # TEST RESPOND
    #
    async def test_respond_to_read(self) -> None:
        """Test respond_to_read function."""
        xknx = XKNX()
        responding = NumericValue(
            xknx,
            "TestSensor1",
            group_address="1/1/1",
            respond_to_read=True,
            value_type="volume_liquid_litre",
        )
        non_responding = NumericValue(
            xknx,
            "TestSensor2",
            group_address="1/1/1",
            respond_to_read=False,
            value_type="volume_liquid_litre",
        )
        responding_multiple = NumericValue(
            xknx,
            "TestSensor3",
            group_address=["1/1/1", "3/3/3"],
            group_address_state="2/2/2",
            respond_to_read=True,
            value_type="volume_liquid_litre",
        )
        #  set initial payload of NumericValue
        responding.sensor_value.value = 256
        non_responding.sensor_value.value = 256
        responding_multiple.sensor_value.value = 256

        read_telegram = Telegram(
            destination_address=GroupAddress("1/1/1"), payload=GroupValueRead()
        )
        # verify no response when respond is False
        non_responding.process(read_telegram)
        assert xknx.telegrams.qsize() == 0

        # verify response when respond is True
        responding.process(read_telegram)
        assert xknx.telegrams.qsize() == 1
        response = xknx.telegrams.get_nowait()
        assert response == Telegram(
            destination_address=GroupAddress("1/1/1"),
            payload=GroupValueResponse(DPTArray((0x00, 0x00, 0x01, 0x00))),
        )
        # verify no response when GroupValueRead request is not for group_address
        responding_multiple.process(read_telegram)
        assert xknx.telegrams.qsize() == 1
        response = xknx.telegrams.get_nowait()
        assert response == Telegram(
            destination_address=GroupAddress("1/1/1"),
            payload=GroupValueResponse(DPTArray((0x00, 0x00, 0x01, 0x00))),
        )
        responding_multiple.process(
            Telegram(
                destination_address=GroupAddress("2/2/2"), payload=GroupValueRead()
            )
        )
        responding_multiple.process(
            Telegram(
                destination_address=GroupAddress("3/3/3"), payload=GroupValueRead()
            )
        )
        assert xknx.telegrams.qsize() == 0

    #
    # TEST SET
    #
    async def test_set_percent(self) -> None:
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

    async def test_set_temperature(self) -> None:
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
    async def test_sync(self) -> None:
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
    async def test_process(self) -> None:
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        sensor = NumericValue(
            xknx, "TestSensor", value_type="temperature", group_address="1/2/3"
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x06, 0xA0))),
        )
        sensor.process(telegram)
        assert sensor.sensor_value.value == 16.96
        assert sensor.sensor_value.telegram.payload.value == DPTArray((0x06, 0xA0))
        assert sensor.resolve_state() == 16.96

    async def test_process_callback(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if callback is called."""

        xknx = XKNX()
        sensor = NumericValue(
            xknx, "TestSensor", group_address="1/2/3", value_type="temperature"
        )
        after_update_callback = Mock()
        sensor.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x01, 0x02))),
        )
        sensor.process(telegram)
        after_update_callback.assert_called_with(sensor)
        assert sensor.last_telegram == telegram
        # consecutive telegrams with same payload shall only trigger one callback
        after_update_callback.reset_mock()
        sensor.process(telegram)
        after_update_callback.assert_not_called()

    async def test_process_callback_always(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if callback is called."""

        xknx = XKNX()
        sensor = NumericValue(
            xknx,
            "TestSensor",
            group_address="1/2/3",
            value_type="temperature",
            always_callback=True,
        )
        after_update_callback = Mock()
        sensor.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x01, 0x02))),
        )
        sensor.process(telegram)
        after_update_callback.assert_called_with(sensor)
        assert sensor.last_telegram == telegram
        # every telegram shall trigger callback
        after_update_callback.reset_mock()
        sensor.process(telegram)
        after_update_callback.assert_called_with(sensor)

    async def test_process_callback_set(self) -> None:
        """Test setting value. Test if callback is called."""

        xknx = XKNX()
        after_update_callback = Mock()
        num_value = NumericValue(
            xknx, "TestSensor", group_address="1/2/3", value_type="temperature"
        )
        xknx.devices.async_add(num_value)
        num_value.register_device_updated_cb(after_update_callback)

        await num_value.set(21.0)
        xknx.devices.process(xknx.telegrams.get_nowait())
        after_update_callback.assert_called_with(num_value)

    def test_string(self) -> None:
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
