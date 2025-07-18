"""Unit test for Switch objects."""

from unittest.mock import Mock

from xknx import XKNX
from xknx.devices import Switch
from xknx.dpt import DPTBinary
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite

from ..conftest import EventLoopClockAdvancer


class TestSwitch:
    """Test class for Switch object."""

    #
    # SYNC
    #
    async def test_sync(self) -> None:
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        switch = Switch(
            xknx, "TestOutlet", group_address_state="1/2/3", group_address="1/2/4"
        )
        await switch.sync()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )

    async def test_sync_state_address(self) -> None:
        """Test sync function / sending group reads to KNX bus. Test with Switch with explicit state address."""
        xknx = XKNX()
        switch = Switch(
            xknx, "TestOutlet", group_address="1/2/3", group_address_state="1/2/4"
        )
        await switch.sync()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
        )

    #
    # TEST PROCESS
    #
    async def test_process(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if device was updated."""
        xknx = XKNX()
        callback_mock = Mock()

        switch1 = Switch(
            xknx, "TestOutlet", group_address="1/2/3", device_updated_cb=callback_mock
        )
        switch2 = Switch(
            xknx, "TestOutlet", group_address="1/2/3", device_updated_cb=callback_mock
        )
        assert switch1.state is None
        assert switch2.state is None
        callback_mock.assert_not_called()

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        telegram_off = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

        switch1.process(telegram_on)
        assert switch1.state is True
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        switch1.process(telegram_off)
        assert switch1.state is False
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        # test setting switch2 to False with first telegram
        switch2.process(telegram_off)
        assert switch2.state is False
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        switch2.process(telegram_on)
        assert switch2.state is True
        callback_mock.assert_called_once()
        callback_mock.reset_mock()

    async def test_process_state(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if device was updated."""
        xknx = XKNX()
        callback_mock = Mock()

        switch1 = Switch(
            xknx,
            "TestOutlet",
            group_address="1/2/3",
            group_address_state="1/2/4",
            device_updated_cb=callback_mock,
        )
        switch2 = Switch(
            xknx,
            "TestOutlet",
            group_address="1/2/3",
            group_address_state="1/2/4",
            device_updated_cb=callback_mock,
        )
        assert switch1.state is None
        assert switch2.state is None
        callback_mock.assert_not_called()

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueResponse(DPTBinary(1)),
        )
        telegram_off = Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueResponse(DPTBinary(0)),
        )

        switch1.process(telegram_on)
        assert switch1.state is True
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        switch1.process(telegram_off)
        assert switch1.state is False
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        # test setting switch2 to False with first telegram
        switch2.process(telegram_off)
        assert switch2.state is False
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        switch2.process(telegram_on)
        assert switch2.state is True
        callback_mock.assert_called_once()
        callback_mock.reset_mock()

    async def test_process_invert(self) -> None:
        """Test process / reading telegrams from telegram queue with inverted switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3", invert=True)
        assert switch.state is None

        telegram_inv_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        telegram_inv_off = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        switch.process(telegram_inv_on)
        assert switch.state is True
        switch.process(telegram_inv_off)
        assert switch.state is False

    async def test_process_reset_after(
        self, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test process reset_after."""
        xknx = XKNX()
        reset_after_sec = 1
        switch = Switch(
            xknx, "TestInput", group_address="1/2/3", reset_after=reset_after_sec
        )
        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        switch.process(telegram_on)
        assert switch.state
        assert xknx.telegrams.qsize() == 0
        await time_travel(reset_after_sec)
        assert xknx.telegrams.qsize() == 1
        switch.process(xknx.telegrams.get_nowait())
        assert not switch.state

    async def test_process_reset_after_cancel_existing(
        self, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test process reset_after cancels existing reset tasks."""
        xknx = XKNX()
        reset_after_sec = 0.01
        switch = Switch(
            xknx, "TestInput", group_address="1/2/3", reset_after=reset_after_sec
        )
        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTBinary(1)),
        )

        switch.process(telegram_on)
        assert switch.state
        assert xknx.telegrams.qsize() == 0
        await time_travel(reset_after_sec / 2)
        # half way through the reset timer
        switch.process(telegram_on)
        assert switch.state

        await time_travel(reset_after_sec / 2)
        assert xknx.telegrams.qsize() == 0

    async def test_remove_device(self, xknx_no_interface: XKNX) -> None:
        """Test device removal cancels task."""
        xknx = xknx_no_interface
        switch = Switch(xknx, "TestInput", group_address="1/2/3", reset_after=1)
        xknx.devices.async_add(switch)
        async with xknx:
            telegram_on = Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueResponse(DPTBinary(1)),
            )
            switch.process(telegram_on)
            assert switch.state
            assert switch._reset_task is not None
            xknx.devices.async_remove(switch)
            assert switch._reset_task is None

    async def test_process_callback(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if callback was called."""

        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")

        after_update_callback = Mock()
        switch.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        switch.process(telegram)

        after_update_callback.assert_called_with(switch)

    #
    # TEST RESPOND
    #
    async def test_respond_to_read(self) -> None:
        """Test respond_to_read function."""
        xknx = XKNX()
        responding = Switch(
            xknx,
            "TestSensor1",
            group_address="1/1/1",
            respond_to_read=True,
        )
        non_responding = Switch(
            xknx,
            "TestSensor2",
            group_address="1/1/1",
            respond_to_read=False,
        )
        responding_multiple = Switch(
            xknx,
            "TestSensor3",
            group_address=["1/1/1", "3/3/3"],
            group_address_state="2/2/2",
            respond_to_read=True,
        )
        #  set initial payload of Switch
        responding.switch.value = True
        non_responding.switch.value = True
        responding_multiple.switch.value = True

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
            payload=GroupValueResponse(DPTBinary(True)),
        )
        # verify no response when GroupValueRead request is not for group_address
        responding_multiple.process(read_telegram)
        assert xknx.telegrams.qsize() == 1
        response = xknx.telegrams.get_nowait()
        assert response == Telegram(
            destination_address=GroupAddress("1/1/1"),
            payload=GroupValueResponse(DPTBinary(True)),
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
    # TEST SET ON
    #
    async def test_set_on(self) -> None:
        """Test switching on switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        await switch.set_on()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

    #
    # TEST SET OFF
    #
    async def test_set_off(self) -> None:
        """Test switching off switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        await switch.set_off()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

    #
    # TEST SET INVERT
    #
    async def test_set_invert(self) -> None:
        """Test switching on/off inverted switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3", invert=True)

        await switch.set_on()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

        await switch.set_off()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

    #
    # TEST has_group_address
    #
    def test_has_group_address(self) -> None:
        """Test has_group_address."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        assert switch.has_group_address(GroupAddress("1/2/3"))
        assert not switch.has_group_address(GroupAddress("2/2/2"))

        assert switch.group_addresses() == {GroupAddress("1/2/3")}

    #
    # TEST passive group addresses
    #
    def test_has_group_address_passive(self) -> None:
        """Test has_group_address with passive group address."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address=["1/2/3", "4/4/4"])
        assert switch.has_group_address(GroupAddress("1/2/3"))
        assert switch.has_group_address(GroupAddress("4/4/4"))
        assert not switch.has_group_address(GroupAddress("2/2/2"))

        assert switch.group_addresses() == {
            GroupAddress("1/2/3"),
            GroupAddress("4/4/4"),
        }

    async def test_process_passive(self) -> None:
        """Test process / reading telegrams from telegram queue. Test if device was updated."""
        xknx = XKNX()
        callback_mock = Mock()

        switch1 = Switch(
            xknx,
            "TestOutlet",
            group_address=["1/2/3", "4/4/4"],
            group_address_state=["1/2/30", "5/5/5"],
            device_updated_cb=callback_mock,
        )
        assert switch1.state is None
        callback_mock.assert_not_called()

        telegram_on_passive = Telegram(
            destination_address=GroupAddress("4/4/4"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        telegram_off_passive = Telegram(
            destination_address=GroupAddress("5/5/5"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

        switch1.process(telegram_on_passive)
        assert switch1.state is True
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        switch1.process(telegram_off_passive)
        assert switch1.state is False
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
