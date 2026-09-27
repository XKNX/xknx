"""Unit test for the cause of device updates passed to device updated callbacks."""

from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.devices import BinarySensor, Cover, DeviceUpdate, Light, Switch
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDirection,
    telegram_context,
)
from xknx.telegram.apci import GroupValueWrite

from ..conftest import EventLoopClockAdvancer


def _incoming(
    group_address: str, payload: DPTArray | DPTBinary, context: object = None
) -> Telegram:
    return Telegram(
        destination_address=GroupAddress(group_address),
        direction=TelegramDirection.INCOMING,
        payload=GroupValueWrite(payload),
        source_address=IndividualAddress("1.1.23"),
        context=context,
    )


def test_incoming_telegram_update() -> None:
    """Test an incoming telegram is passed as cause with the context set on it."""
    xknx = XKNX()
    callback = Mock()
    switch = Switch(
        xknx, name="TestSwitch", group_address="1/2/3", device_updated_cb=callback
    )
    context = object()
    telegram = _incoming("1/2/3", DPTBinary(1), context=context)

    switch.process(telegram)

    callback.assert_called_once_with(
        switch, DeviceUpdate(telegram=telegram, context=context)
    )
    assert callback.call_args.args[1].telegram is telegram


async def test_outgoing_telegram_update() -> None:
    """Test an outgoing telegram carries the context it was created in."""
    xknx = XKNX()
    callback = Mock()
    switch = Switch(
        xknx, name="TestSwitch", group_address="1/2/3", device_updated_cb=callback
    )
    context = object()

    with telegram_context(context):
        await switch.set_on()
    telegram = xknx.telegrams.get_nowait()
    assert telegram.context is context

    # outgoing telegrams are processed later by the TelegramQueue - outside the scope
    switch.process(telegram)
    callback.assert_called_once_with(
        switch, DeviceUpdate(telegram=telegram, context=context)
    )


def test_update_without_telegram() -> None:
    """Test an update not caused by a telegram uses the active telegram_context."""
    xknx = XKNX()
    callback = Mock()
    switch = Switch(
        xknx, name="TestSwitch", group_address="1/2/3", device_updated_cb=callback
    )
    context = object()

    with telegram_context(context):
        switch.switch.update_value(True)
    callback.assert_called_once_with(switch, DeviceUpdate(context=context))

    callback.reset_mock()
    switch.switch.update_value(False)
    callback.assert_called_once_with(switch, DeviceUpdate())


def test_global_device_updated_cb() -> None:
    """Test the cause is passed to callbacks registered on XKNX."""
    callback = Mock()
    xknx = XKNX(device_updated_cb=callback)
    switch = Switch(xknx, name="TestSwitch", group_address="1/2/3")
    xknx.devices.async_add(switch)
    telegram = _incoming("1/2/3", DPTBinary(1))

    xknx.devices.process(telegram)

    callback.assert_called_once_with(switch, DeviceUpdate(telegram=telegram))


async def test_cover_travel_updates(time_travel: EventLoopClockAdvancer) -> None:
    """Test periodic travel updates keep the telegram starting the travel as cause."""
    xknx = XKNX()
    callback = Mock()
    cover = Cover(
        xknx,
        name="TestCover",
        group_address_long="1/2/1",
        group_address_position="1/2/3",
        group_address_position_state="1/2/4",
        travel_time_down=10,
        travel_time_up=10,
        device_updated_cb=callback,
    )
    with patch("time.time") as mock_time:
        mock_time.return_value = 1517000000.0
        cover.process(_incoming("1/2/4", DPTArray(0)))
        await time_travel(0)
        callback.reset_mock()

        start_telegram = _incoming("1/2/3", DPTArray(255), context=object())
        cover.process(start_telegram)
        assert callback.call_count == 1

        mock_time.return_value = 1517000001.0
        await time_travel(1)
        assert callback.call_count == 2
        callback.assert_called_with(
            cover,
            DeviceUpdate(telegram=start_telegram, context=start_telegram.context),
        )


async def test_cover_set_position_context(time_travel: EventLoopClockAdvancer) -> None:
    """Test a travel started by the application carries the applications context."""
    xknx = XKNX()
    callback = Mock()
    cover = Cover(
        xknx,
        name="TestCover",
        group_address_long="1/2/1",
        group_address_stop="1/2/2",
        group_address_position_state="1/2/4",
        travel_time_down=10,
        travel_time_up=10,
        device_updated_cb=callback,
    )
    with patch("time.time") as mock_time:
        mock_time.return_value = 1517000000.0
        cover.process(_incoming("1/2/4", DPTArray(0)))
        callback.reset_mock()
        context = object()

        with telegram_context(context):
            await cover.set_position(50)
        callback.assert_called_once_with(cover, DeviceUpdate(context=context))

        mock_time.return_value = 1517000005.0
        await time_travel(5)
        # periodic update and final update from the auto stopper
        callback.assert_called_with(cover, DeviceUpdate(context=context))
        # auto stopper telegram is sent from a task started by `set_position()`
        telegrams = []
        while not xknx.telegrams.empty():
            telegrams.append(xknx.telegrams.get_nowait())
        assert telegrams[-1].destination_address == GroupAddress("1/2/2")
        assert all(telegram.context is context for telegram in telegrams)


async def test_light_individual_color_debouncer(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test debounced individual color updates use the last telegram as cause."""
    xknx = XKNX()
    callback = Mock()
    light = Light(
        xknx,
        name="TestRGBLight",
        group_address_brightness_red="1/1/3",
        group_address_brightness_green="1/1/7",
        group_address_brightness_blue="1/1/11",
        device_updated_cb=callback,
    )
    light.process(_incoming("1/1/3", DPTArray(42)))
    last_telegram = _incoming("1/1/7", DPTArray(43))
    light.process(last_telegram)
    callback.assert_not_called()

    await time_travel(0.2)
    callback.assert_called_once_with(light, DeviceUpdate(telegram=last_telegram))


async def test_binary_sensor_counter(time_travel: EventLoopClockAdvancer) -> None:
    """Test counter updates after context_timeout use the counted telegram as cause."""
    xknx = XKNX()
    callback = Mock()
    binary_sensor = BinarySensor(
        xknx,
        name="TestInput",
        group_address_state="1/2/3",
        ignore_internal_state=True,
        context_timeout=1,
        device_updated_cb=callback,
    )
    telegram = _incoming("1/2/3", DPTBinary(1))
    binary_sensor.process(telegram)
    callback.assert_not_called()

    await time_travel(1)
    assert callback.call_count == 2
    callback.assert_called_with(binary_sensor, DeviceUpdate(telegram=telegram))
