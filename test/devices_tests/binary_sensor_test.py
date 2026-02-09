"""Unit test for BinarySensor objects."""

from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.devices import BinarySensor
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueResponse, GroupValueWrite

from ..conftest import EventLoopClockAdvancer


class TestBinarySensor:
    """Test class for BinarySensor objects."""

    #
    # TEST PROCESS
    #
    async def test_process(self) -> None:
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, "TestInput", "1/2/3")

        assert binaryinput.state is None

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        binaryinput.process(telegram_on)
        assert binaryinput.state is True

        telegram_off = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        binaryinput.process(telegram_off)
        assert binaryinput.state is False

        binaryinput2 = BinarySensor(xknx, "TestInput", "1/2/4")
        assert binaryinput2.state is None

        telegram_off2 = Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        binaryinput2.process(telegram_off2)
        assert binaryinput2.last_telegram == telegram_off2
        assert binaryinput2.state is False

    async def test_process_invert(self) -> None:
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        bs_invert = BinarySensor(xknx, "TestInput", "1/2/3", invert=True)

        assert bs_invert.state is None

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        bs_invert.process(telegram_on)

        assert bs_invert.state is True

        telegram_off = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        bs_invert.process(telegram_off)
        assert bs_invert.state is False

    async def test_process_reset_after(
        self, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        reset_after_sec = 1
        after_update_callback = Mock()
        binaryinput = BinarySensor(
            xknx,
            "TestInput",
            "1/2/3",
            reset_after=reset_after_sec,
            device_updated_cb=after_update_callback,
        )
        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        binaryinput.process(telegram_on)
        assert binaryinput.state

        await time_travel(reset_after_sec)
        assert not binaryinput.state
        # once for 'on' and once for 'off'
        assert after_update_callback.call_count == 2

        after_update_callback.reset_mock()
        # multiple telegrams during reset_after time period shall reset timer
        binaryinput.process(telegram_on)
        after_update_callback.assert_called_once()
        binaryinput.process(telegram_on)
        binaryinput.process(telegram_on)
        # second and third telegram resets timer but doesn't run callback
        after_update_callback.assert_called_once()
        assert binaryinput.state

        await time_travel(reset_after_sec)
        assert not binaryinput.state
        # once for 'on' and once for 'off'
        assert after_update_callback.call_count == 2

    async def test_process_wrong_payload(self) -> None:
        """Test process wrong telegram (wrong payload type)."""
        xknx = XKNX()
        binary_sensor = BinarySensor(xknx, "Warning", group_address_state="1/2/3")
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x1, 0x2, 0x3))),
        )
        with patch("logging.Logger.warning") as log_mock:
            binary_sensor.process(telegram)
            log_mock.assert_called_once()
            assert binary_sensor.state is None

    #
    # TEST SWITCHED ON
    #
    def test_is_on(self) -> None:
        """Test is_on() and is_off() of a BinarySensor with state 'on'."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, "TestInput", "1/2/3")
        assert not binaryinput.is_on()
        assert binaryinput.is_off()
        binaryinput._set_internal_state(True)

        assert binaryinput.is_on()
        assert not binaryinput.is_off()

    #
    # TEST SWITCHED OFF
    #
    def test_is_off(self) -> None:
        """Test is_on() and is_off() of a BinarySensor with state 'off'."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, "TestInput", "1/2/3")
        binaryinput._set_internal_state(False)

        assert not binaryinput.is_on()
        assert binaryinput.is_off()

    #
    # TEST PROCESS CALLBACK
    #
    async def test_process_callback(self) -> None:
        """Test after_update_callback after state of binary sensor was changed."""
        xknx = XKNX()
        switch = BinarySensor(
            xknx, "TestInput", group_address_state="1/2/3", ignore_internal_state=False
        )
        after_update_callback = Mock()

        switch.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        switch.process(telegram)
        # no _context_task started because ignore_internal_state is False
        assert switch._context_task is None
        after_update_callback.assert_called_once_with(switch)

        after_update_callback.reset_mock()
        # send same telegram again
        switch.process(telegram)
        after_update_callback.assert_not_called()

    async def test_process_callback_context_timeout(
        self, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test after_update_callback after context_timeout."""
        _timeout = 3
        xknx = XKNX()
        switch = BinarySensor(
            xknx,
            "TestInput",
            group_address_state="1/2/3",
            ignore_internal_state=True,
            context_timeout=_timeout,
        )
        after_update_callback = Mock()

        switch.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert switch.counter == 0

        switch.process(telegram)
        after_update_callback.assert_not_called()
        assert switch.counter == 1
        await time_travel(_timeout)
        after_update_callback.assert_called_with(switch)
        # once with counter 1 and once with counter 0
        assert after_update_callback.call_count == 2

        after_update_callback.reset_mock()
        # send same telegram again
        switch.process(telegram)
        assert switch.counter == 1
        await time_travel(_timeout / 2)  # not yet timed out
        switch.process(telegram)
        assert switch.counter == 2
        # incoming telegram resets timer (not sure if this is what we actually want)
        await time_travel(_timeout / 2)  # not yet timed out
        after_update_callback.assert_not_called()

        await time_travel(_timeout / 2)
        after_update_callback.assert_called_with(switch)
        # once with counter 2 and once with counter 0
        assert after_update_callback.call_count == 2
        assert switch.counter == 0

    async def test_process_callback_ignore_internal_state_no_counter(self) -> None:
        """Test after_update_callback after state of switch was changed."""
        xknx = XKNX()
        switch = BinarySensor(
            xknx,
            "TestInput",
            group_address_state="1/2/3",
            ignore_internal_state=True,
            context_timeout=0,
        )
        after_update_callback = Mock()

        switch.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        switch.process(telegram)
        # no _context_task started because context_timeout is False
        assert switch._context_task is None
        after_update_callback.assert_called_once_with(switch)

        after_update_callback.reset_mock()
        # send same telegram again
        switch.process(telegram)
        after_update_callback.assert_called_once_with(switch)

    async def test_process_group_value_response(self) -> None:
        """Test process of GroupValueResponse telegrams."""
        xknx = XKNX()
        switch = BinarySensor(
            xknx,
            "TestInput",
            group_address_state="1/2/3",
            ignore_internal_state=True,
        )
        after_update_callback = Mock()

        switch.register_device_updated_cb(after_update_callback)

        write_telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        response_telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(
                DPTBinary(1),
            ),
        )
        assert switch.state is None
        # initial GroupValueResponse changes state and runs callback
        switch.process(response_telegram)
        assert switch.state
        after_update_callback.assert_called_once_with(switch)
        # GroupValueWrite with same payload runs callback because of `ignore_internal_state`
        after_update_callback.reset_mock()
        switch.process(write_telegram)
        assert switch.state
        after_update_callback.assert_called_once_with(switch)
        # GroupValueResponse should not run callback when state has not changed
        after_update_callback.reset_mock()
        switch.process(response_telegram)
        after_update_callback.assert_not_called()

    async def test_process_always_callback(self) -> None:
        """Test process of GroupValueResponse telegrams."""
        xknx = XKNX()
        switch = BinarySensor(
            xknx,
            "TestInput",
            group_address_state="1/2/3",
            always_callback=True,
        )
        after_update_callback = Mock()

        switch.register_device_updated_cb(after_update_callback)

        write_telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        response_telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(
                DPTBinary(1),
            ),
        )
        assert switch.state is None
        # initial GroupValueResponse changes state and runs callback
        switch.process(response_telegram)
        assert switch.state
        after_update_callback.assert_called_once_with(switch)
        # GroupValueWrite with same payload runs callback because of `always_callback`
        after_update_callback.reset_mock()
        switch.process(write_telegram)
        assert switch.state
        after_update_callback.assert_called_once_with(switch)
        # GroupValueResponse should run callback because of `always_callback`
        after_update_callback.reset_mock()
        switch.process(response_telegram)
        after_update_callback.assert_called_once_with(switch)

    #
    # TEST COUNTER
    #
    def test_counter(self) -> None:
        """Test counter functionality."""
        xknx = XKNX()
        switch = BinarySensor(
            xknx, "TestInput", group_address_state="1/2/3", context_timeout=1
        )
        with patch("time.time") as mock_time:
            mock_time.return_value = 1517000000.0
            assert switch.bump_and_get_counter(True) == 1

            mock_time.return_value = 1517000000.1
            assert switch.bump_and_get_counter(True) == 2

            mock_time.return_value = 1517000000.2
            assert switch.bump_and_get_counter(False) == 1

            mock_time.return_value = 1517000000.3
            assert switch.bump_and_get_counter(True) == 3

            mock_time.return_value = 1517000000.4
            assert switch.bump_and_get_counter(False) == 2

            mock_time.return_value = 1517000002.0  # TIME OUT ...
            assert switch.bump_and_get_counter(True) == 1

            mock_time.return_value = 1517000004.1  # TIME OUT ...
            assert switch.bump_and_get_counter(False) == 1

    async def test_remove_tasks(self, xknx_no_interface: XKNX) -> None:
        """Test remove tasks."""
        xknx = xknx_no_interface
        switch = BinarySensor(
            xknx,
            "TestInput",
            group_address_state="1/2/3",
            context_timeout=1,
            reset_after=10,
        )
        xknx.devices.async_add(switch)
        async with xknx:
            write_telegram = Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTBinary(1)),
            )
            switch.process(write_telegram)
            assert switch._context_task
            assert switch._reset_task
            xknx.devices.async_remove(switch)
            assert switch._context_task.done()
            assert switch._reset_task.done()
