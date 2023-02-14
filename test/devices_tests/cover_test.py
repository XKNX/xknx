"""Unit test for Cover objects."""
from unittest.mock import AsyncMock, patch

from xknx import XKNX
from xknx.devices import Cover
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


class TestCover:
    """Test class for Cover objects."""

    #
    # SUPPORTS STOP/POSITION/ANGLE
    #
    def test_supports_stop_true(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover_short_stop = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
        )
        assert cover_short_stop.supports_stop

        cover_manual_stop = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_stop="1/4/15",
        )
        assert cover_manual_stop.supports_stop

    async def test_supports_stop_false(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_position="1/4/16",
            group_address_angle="1/4/18",
        )
        assert not cover.supports_stop
        with patch("logging.Logger.warning") as mock_warn:
            await cover.stop()
            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "Stop not supported for device %s", "Children.Venetian"
            )

    def test_supports_position_true(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
            group_address_position="1/4/16",
        )
        assert cover.supports_position

    def test_supports_position_false(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
        )
        assert not cover.supports_position

    def test_supports_angle_true(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
            group_address_angle="1/4/18",
        )
        assert cover.supports_angle

    def test_support_angle_false(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
        )
        assert not cover.supports_angle

    #
    # SUPPORTS LOCKED
    #
    def test_support_locked(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover_locked = Cover(
            xknx,
            "Children.Venetian",
            group_address_locked_state="1/4/14",
        )
        assert cover_locked.supports_locked
        cover_manual_stop = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_stop="1/4/15",
        )
        assert cover_manual_stop.supports_locked is False

    #
    # SYNC
    #
    async def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverSync",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/3",
        )
        await cover.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )

    async def test_sync_state(self):
        """Test sync function with explicit state address."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverSyncState",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        await cover.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(
            destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
        )

    async def test_sync_angle(self):
        """Test sync function for cover with angle."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverSyncAngle",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/3",
            group_address_angle_state="1/2/4",
        )
        await cover.sync()
        assert xknx.telegrams.qsize() == 2
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )
        telegram2 = xknx.telegrams.get_nowait()
        assert telegram2 == Telegram(
            destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
        )

    async def test_sync_angle_state(self):
        """Test sync function with angle/explicit state."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverSyncAngleState",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_angle="1/2/3",
            group_address_angle_state="1/2/4",
        )
        await cover.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(
            destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
        )

    #
    # TEST SET UP
    #
    async def test_set_up(self):
        """Test moving cover to 'up' position."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverSetUp",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        await cover.set_up()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        # DPT 1.008 - 0:up 1:down
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

    #
    # TEST SET DOWN
    #
    async def test_set_short_down(self):
        """Test moving cover to 'down' position."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverShortDown",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        await cover.set_down()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

    #
    # TEST SET DOWN INVERTED
    #
    async def test_set_down_inverted(self):
        """Test moving cover to 'down' position."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverSetDownInverted",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
            invert_updown=True,
        )
        await cover.set_down()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

    #
    # TEST SET SHORT UP
    #
    async def test_set_short_up(self):
        """Test moving cover 'short up'."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverSetShortUp",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        await cover.set_short_up()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        # DPT 1.008 - 0:up 1:down
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

    #
    # TEST SET UP INVERTED
    #
    async def test_set_up_inverted(self):
        """Test moving cover 'short up'."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverSetUpInverted",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
            invert_updown=True,
        )
        await cover.set_short_up()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        # DPT 1.008 - 0:up 1:down
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

    #
    # TEST SET SHORT DOWN
    #
    async def test_set_down(self):
        """Test moving cover 'short down'."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverSetDown",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        await cover.set_short_down()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        # DPT 1.008 - 0:up 1:down
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

    #
    # TEST STOP
    #
    async def test_stop(self):
        """Test stopping cover."""
        xknx = XKNX()
        cover_short_stop = Cover(
            xknx,
            "TestCoverStop",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        # Attempt stopping while not actually moving
        await cover_short_stop.stop()
        assert xknx.telegrams.qsize() == 0

        # Attempt stopping while moving down
        cover_short_stop.travelcalculator.set_position(0)
        await cover_short_stop.set_down()
        await cover_short_stop.stop()
        assert xknx.telegrams.qsize() == 2
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        # Attempt stopping while moving up
        cover_short_stop.travelcalculator.set_position(100)
        await cover_short_stop.set_up()
        await cover_short_stop.stop()
        assert xknx.telegrams.qsize() == 2
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

        cover_manual_stop = Cover(
            xknx,
            "TestCoverManualStop",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_stop="1/2/0",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        await cover_manual_stop.stop()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/0"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

    async def test_stop_angle(self):
        """Test stopping cover during angle move / tilting."""
        xknx = XKNX()
        cover_short_stop = Cover(
            xknx,
            "TestCoverStopAngle",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_angle="1/2/5",
            group_address_angle_state="1/2/6",
        )
        # Attempt stopping while not actually tilting
        await cover_short_stop.stop()
        assert xknx.telegrams.qsize() == 0

        # Set cover tilt to a dummy start value, since otherwise we cannot
        # determine later on a tilt direction and without it, stopping the
        # til process has no effect.
        await cover_short_stop.angle.process(
            Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTArray(0xAA)),
            )
        )

        # Attempt stopping while tilting down
        await cover_short_stop.set_angle(100)
        await cover_short_stop.stop()
        assert xknx.telegrams.qsize() == 2
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray(0xFF)),
        )
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        # Attempt stopping while tilting up
        await cover_short_stop.set_angle(0)
        await cover_short_stop.stop()
        assert xknx.telegrams.qsize() == 2
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray(0x00)),
        )
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

    #
    # TEST POSITION
    #
    async def test_position(self):
        """Test moving cover to absolute position."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverPosition",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        await cover.set_position(50)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0x80)),
        )
        await cover.stop()  # clean up tasks

    async def test_position_without_binary(self):
        """Test moving cover - with no binary positioning supported."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverPositionWithoutBinary",
            group_address_position="1/2/3",
        )
        await cover.set_down()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0xFF)),
        )
        await cover.set_position(50)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0x80)),
        )
        await cover.set_up()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0x00)),
        )

    async def test_position_without_position_address_up(self):
        """Test moving cover to absolute position - with no absolute positioning supported."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverPWPAD",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/4",
        )
        cover.travelcalculator.set_position(60)
        await cover.set_position(50)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        # DPT 1.008 - 0:up 1:down
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        assert cover.travelcalculator._travel_to_position == 50
        assert cover.is_opening()
        # process the outgoing telegram to make sure it doesn't overwrite the target position
        await cover.process(telegram)
        assert cover.travelcalculator._travel_to_position == 50
        assert xknx.telegrams.qsize() == 0

        await cover.stop()  # clean up tasks

    async def test_position_without_position_address_down(self):
        """Test moving cover down - with no absolute positioning supported."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverPWPAD",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/4",
        )
        cover.travelcalculator.set_position(70)
        await cover.set_position(80)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert cover.travelcalculator._travel_to_position == 80
        assert cover.is_closing()
        # process the outgoing telegram to make sure it doesn't overwrite the target position
        await cover.process(telegram)
        assert cover.travelcalculator._travel_to_position == 80

        await cover.stop()  # clean up tasks

    async def test_position_without_position_address_uninitialized_up(self):
        """Test moving uninitialized cover to absolute position - with no absolute positioning supported."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverPWPAUU",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/4",
        )

        with patch("logging.Logger.warning") as mock_warn:
            await cover.set_position(50)
            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "Current position unknown. Initialize cover by moving to end position."
            )

        await cover.set_position(0)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        await cover.stop()  # clean up tasks

    async def test_position_without_position_address_uninitialized_down(self):
        """Test moving uninitialized cover to absolute position - with no absolute positioning supported."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverPWPAUD",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/4",
        )

        with patch("logging.Logger.warning") as mock_warn:
            await cover.set_position(50)
            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "Current position unknown. Initialize cover by moving to end position."
            )

        await cover.set_position(100)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await cover.stop()  # clean up tasks

    async def test_angle(self):
        """Test changing angle."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
            group_address_position_state="1/4/17",
            group_address_position="1/4/16",
            group_address_angle="1/4/18",
            group_address_angle_state="1/4/19",
        )
        await cover.set_angle(50)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/4/18"),
            payload=GroupValueWrite(DPTArray(0x80)),
        )

    async def test_angle_not_supported(self):
        """Test changing angle on cover which does not support angle."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
        )
        with patch("logging.Logger.warning") as mock_warn:
            await cover.set_angle(50)
            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "Angle not supported for device %s", "Children.Venetian"
            )

    #
    # TEST PROCESS
    #
    async def test_process_position(self):
        """Test process / reading telegrams from telegram queue. Test if position is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverProcessPosition",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        # initial position process - position is unknown so this is the new state - not moving
        telegram = Telegram(
            GroupAddress("1/2/3"), payload=GroupValueWrite(DPTArray(213))
        )
        await cover.process(telegram)
        assert cover.current_position() == 84
        assert not cover.is_traveling()
        # state telegram updates current position - we are not moving so this is new state - not moving
        telegram = Telegram(
            GroupAddress("1/2/4"), payload=GroupValueWrite(DPTArray(42))
        )
        await cover.process(telegram)
        assert cover.current_position() == 16
        assert not cover.is_traveling()
        assert cover.travelcalculator._travel_to_position == 16
        # new position - movement starts
        telegram = Telegram(
            GroupAddress("1/2/3"), payload=GroupValueWrite(DPTArray(255))
        )
        await cover.process(telegram)
        assert cover.current_position() == 16
        assert cover.is_closing()
        assert cover.travelcalculator._travel_to_position == 100
        # new state while moving - movement goes on; travelcalculator updated
        telegram = Telegram(
            GroupAddress("1/2/4"), payload=GroupValueWrite(DPTArray(213))
        )
        await cover.process(telegram)
        assert cover.current_position() == 84
        assert cover.is_closing()
        assert cover.travelcalculator._travel_to_position == 100

        await cover.stop()  # clean up tasks

    async def test_process_angle(self):
        """Test process / reading telegrams from telegram queue. Test if position is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverProcessAngle",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_angle="1/2/3",
            group_address_angle_state="1/2/4",
        )
        telegram = Telegram(
            GroupAddress("1/2/4"), payload=GroupValueWrite(DPTArray(42))
        )
        await cover.process(telegram)
        assert cover.current_angle() == 16

    async def test_process_locked(self):
        """Test process / reading telegrams from telegram queue. Test if position is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverProcessLocked",
            group_address_long="1/2/1",
            group_address_locked_state="1/2/4",
        )
        telegram = Telegram(
            GroupAddress("1/2/4"), payload=GroupValueWrite(DPTBinary(1))
        )
        await cover.process(telegram)
        assert cover.is_locked() is True

    async def test_process_up(self):
        """Test process / reading telegrams from telegram queue. Test if up/down is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverProcessUp",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
        )
        cover.travelcalculator.set_position(50)
        assert not cover.is_traveling()
        telegram = Telegram(
            GroupAddress("1/2/1"), payload=GroupValueWrite(DPTBinary(0))
        )
        await cover.process(telegram)
        assert cover.is_opening()

        await cover.stop()  # clean up tasks

    async def test_process_down(self):
        """Test process / reading telegrams from telegram queue. Test if up/down is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverProcessDown",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
        )
        cover.travelcalculator.set_position(50)
        assert not cover.is_traveling()
        telegram = Telegram(
            GroupAddress("1/2/1"), payload=GroupValueWrite(DPTBinary(1))
        )
        await cover.process(telegram)
        assert cover.is_closing()

        await cover.stop()  # clean up tasks

    async def test_process_stop(self):
        """Test process / reading telegrams from telegram queue. Test if stop is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverProcessStop",
            group_address_long="1/2/1",
            group_address_stop="1/2/2",
        )
        cover.travelcalculator.set_position(50)
        await cover.set_down()
        assert cover.is_traveling()
        telegram = Telegram(
            GroupAddress("1/2/2"), payload=GroupValueWrite(DPTBinary(1))
        )
        await cover.process(telegram)
        assert not cover.is_traveling()

    async def test_process_short_stop(self):
        """Test process / reading telegrams from telegram queue. Test if stop is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverProcessShortStop",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
        )
        cover.travelcalculator.set_position(50)
        await cover.set_down()
        assert cover.is_traveling()
        telegram = Telegram(
            GroupAddress("1/2/2"), payload=GroupValueWrite(DPTBinary(1))
        )
        await cover.process(telegram)
        assert not cover.is_traveling()

    async def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback is executed."""

        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverProcessCallback",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_stop="1/2/3",
            group_address_position="1/2/4",
            group_address_position_state="1/2/5",
            group_address_angle="1/2/6",
            group_address_angle_state="1/2/7",
        )

        after_update_callback = AsyncMock()

        cover.register_device_updated_cb(after_update_callback)
        for address, payload, _feature in [
            ("1/2/1", DPTBinary(1), "long"),
            ("1/2/2", DPTBinary(1), "short"),
            ("1/2/4", DPTArray(42), "position"),
            ("1/2/3", DPTBinary(1), "stop"),
            # call position with same value again to make sure `always_callback` is set for target position
            ("1/2/4", DPTArray(42), "position"),
            ("1/2/5", DPTArray(42), "position state"),
            ("1/2/6", DPTArray(42), "angle"),
            ("1/2/7", DPTArray(51), "angle state"),
        ]:
            telegram = Telegram(
                destination_address=GroupAddress(address),
                payload=GroupValueWrite(payload),
            )
            await cover.process(telegram)
            after_update_callback.assert_called_with(cover)
            after_update_callback.reset_mock()
        # Stop only when cover is travelling
        telegram = Telegram(
            GroupAddress("1/2/3"), payload=GroupValueWrite(DPTBinary(1))
        )
        await cover.process(telegram)
        after_update_callback.assert_not_called()
        await cover.set_down()
        await cover.process(telegram)
        after_update_callback.assert_called_with(cover)

        await cover.stop()  # clean up tasks

    #
    # IS TRAVELING / IS UP / IS DOWN
    #
    async def test_is_traveling(self):
        """Test moving cover to absolute position."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverIsTraveling",
            group_address_long="1/2/1",
            group_address_stop="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
            travel_time_down=10,
            travel_time_up=10,
        )
        with patch("time.time") as mock_time:
            mock_time.return_value = 1517000000.0
            assert not cover.is_traveling()
            assert not cover.is_opening()
            assert not cover.is_closing()
            assert cover.position_reached()
            # we start with state open covers (up)
            cover.travelcalculator.set_position(0)
            await cover.set_down()
            assert cover.is_traveling()
            assert cover.is_open()
            assert not cover.is_closed()
            assert not cover.is_opening()
            assert cover.is_closing()

            mock_time.return_value = 1517000005.0  # 5 Seconds, half way
            assert not cover.position_reached()
            assert cover.is_traveling()
            assert not cover.is_open()
            assert not cover.is_closed()
            assert not cover.is_opening()
            assert cover.is_closing()

            mock_time.return_value = 1517000010.0  # 10 Seconds, fully closed
            assert cover.position_reached()
            assert not cover.is_traveling()
            assert not cover.is_open()
            assert cover.is_closed()
            assert not cover.is_opening()
            assert not cover.is_closing()
            # up again
            await cover.set_up()
            assert not cover.position_reached()
            assert cover.is_traveling()
            assert not cover.is_open()
            assert cover.is_closed()
            assert cover.is_opening()
            assert not cover.is_closing()

            mock_time.return_value = 1517000015.0  # 15 Seconds, half way
            assert not cover.position_reached()
            assert cover.is_traveling()
            assert not cover.is_open()
            assert not cover.is_closed()
            assert cover.is_opening()
            assert not cover.is_closing()

            mock_time.return_value = 1517000016.0  # 16 Seconds, manual stop
            await cover.stop()
            assert cover.position_reached()
            assert not cover.is_traveling()
            assert not cover.is_open()
            assert not cover.is_closed()
            assert not cover.is_opening()
            assert not cover.is_closing()

    #
    # TEST TASKS
    #
    async def test_auto_stop(self, time_travel):
        """Test auto stop functionality."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverAutoStop",
            group_address_long="1/2/1",
            group_address_stop="1/2/2",
            travel_time_down=10,
            travel_time_up=10,
        )
        with patch("time.time") as mock_time:
            mock_time.return_value = 1517000000.0
            # we start with state 0 - open covers (up) this is assumed immediately
            await cover.set_position(0)
            assert xknx.telegrams.qsize() == 1
            _ = xknx.telegrams.get_nowait()

            await cover.set_position(50)

            await time_travel(1)
            mock_time.return_value = 1517000001.0
            assert xknx.telegrams.qsize() == 1
            telegram1 = xknx.telegrams.get_nowait()
            assert telegram1 == Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTBinary(True)),
            )

            await time_travel(4)
            mock_time.return_value = 1517000005.0
            assert xknx.telegrams.qsize() == 1
            telegram1 = xknx.telegrams.get_nowait()
            assert telegram1 == Telegram(
                destination_address=GroupAddress("1/2/2"),
                payload=GroupValueWrite(DPTBinary(True)),
            )

    async def test_periodic_update(self, time_travel):
        """Test periodic update functionality."""
        xknx = XKNX()
        callback_mock = AsyncMock()
        cover = Cover(
            xknx,
            "TestCoverPeriodicUpdate",
            group_address_long="1/2/1",
            group_address_stop="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
            travel_time_down=10,
            travel_time_up=10,
            device_updated_cb=callback_mock,
        )
        with patch("time.time") as mock_time:
            mock_time.return_value = 1517000000.0
            # state telegram updates current position - we are not moving so this is new state - not moving
            telegram = Telegram(
                GroupAddress("1/2/4"), payload=GroupValueWrite(DPTArray(0))
            )
            await cover.process(telegram)
            assert (
                callback_mock.call_count == 2
            )  # 1 additional form _stop_position_update because previous state was None
            callback_mock.reset_mock()
            # move to 50%
            telegram = Telegram(
                GroupAddress("1/2/3"), payload=GroupValueWrite(DPTArray(125))
            )
            await cover.process(telegram)
            await time_travel(0)
            assert callback_mock.call_count == 1

            mock_time.return_value = 1517000001.0
            await time_travel(1)
            assert callback_mock.call_count == 2

            # state telegram from bus too early
            mock_time.return_value = 1517000001.6
            await time_travel(0.6)
            assert callback_mock.call_count == 2
            telegram = Telegram(
                GroupAddress("1/2/4"), payload=GroupValueWrite(DPTArray(42))
            )
            await cover.process(telegram)
            assert callback_mock.call_count == 3
            # next update 1 second after last received state telegram
            mock_time.return_value = 1517000002.0
            await time_travel(0.4)
            assert callback_mock.call_count == 3
            mock_time.return_value = 1517000002.6
            await time_travel(0.6)
            assert callback_mock.call_count == 4
            # last callback - auto updater is removed
            mock_time.return_value = 1517000005.0
            await time_travel(2.4)
            assert callback_mock.call_count == 5
            assert cover.position_reached()
            assert cover._periodic_update_task is None

    #
    # HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test sensor has group address."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCoverHasGroupAddress",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
            group_address_angle="1/2/5",
            group_address_angle_state="1/2/6",
        )

        assert cover.has_group_address(GroupAddress("1/2/1"))
        assert cover.has_group_address(GroupAddress("1/2/2"))
        assert cover.has_group_address(GroupAddress("1/2/3"))
        assert cover.has_group_address(GroupAddress("1/2/4"))
        assert cover.has_group_address(GroupAddress("1/2/5"))
        assert cover.has_group_address(GroupAddress("1/2/6"))
        assert not cover.has_group_address(GroupAddress("1/2/7"))
