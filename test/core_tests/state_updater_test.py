"""Unit test for StateUpdater."""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from xknx import XKNX
from xknx.core import XknxConnectionState
from xknx.core.state_updater import StateTrackerType, StateUpdater, _StateTracker
import xknx.remote_value
from xknx.remote_value import RemoteValue
from xknx.telegram import GroupAddress


@patch.multiple(RemoteValue, __abstractmethods__=set())
@pytest.mark.asyncio
class TestStateUpdater:
    """Test class for state updater."""

    @pytest.mark.parametrize(
        "sync_state,expected_tracker_type,expected_update_interval",
        [
            (
                "init",
                StateTrackerType.INIT,
                60,
            ),
            (
                2,
                StateTrackerType.EXPIRE,
                2,
            ),
            (
                6.9,
                StateTrackerType.EXPIRE,
                6.9,
            ),
            (
                "expire",
                StateTrackerType.EXPIRE,
                60,
            ),
            (
                "expire 30",
                StateTrackerType.EXPIRE,
                30,
            ),
            (
                "every",
                StateTrackerType.PERIODICALLY,
                60,
            ),
            (
                "every 10",
                StateTrackerType.PERIODICALLY,
                10,
            ),
        ],
    )
    def test_tracker_parser(
        self, sync_state, expected_tracker_type, expected_update_interval
    ):
        """Test parsing tracker options."""
        xknx = XKNX()
        tracker_type, update_interval = StateUpdater.parse_tracker_options(
            sync_state, RemoteValue(xknx)
        )

        assert tracker_type == expected_tracker_type
        assert update_interval == expected_update_interval

    @patch("xknx.remote_value.RemoteValue.read_state")
    async def test_read_mutex(self, read_state):
        """Test read mutex."""
        xknx = XKNX()
        remote_value_invalid = RemoteValue(
            xknx, sync_state="invalid", group_address_state=GroupAddress("1/1/1")
        )
        state_updater = StateUpdater(xknx, remote_value_invalid)

        xknx.connection_manager.connected.set()

        await state_updater.read_state_mutex()

        read_state.assert_called_once()

    @patch("xknx.core.state_updater._StateTracker.reset")
    @patch("xknx.remote_value.RemoteValue.read_state")
    async def test_state_tracker_worker(self, reset, read_state):
        """Test state tracker worker."""
        xknx = XKNX()
        remote_value_invalid = RemoteValue(
            xknx, sync_state="invalid", group_address_state=GroupAddress("1/1/1")
        )
        state_updater = StateUpdater(xknx, remote_value_invalid)

        xknx.connection_manager.connected.set()

        state_updater.start()

        await state_updater._worker._task

        read_state.assert_called_once()
        reset.assert_called_once()

        assert state_updater.initialized

        state_updater._worker = None
        assert not state_updater.initialized

        state_updater.stop()

    @patch("xknx.core.state_updater._StateTracker.reset")
    async def test_state_tracker_update_received(self, reset):
        """Test state tracker."""
        xknx = XKNX()
        remote_value_invalid = RemoteValue(
            xknx, sync_state="invalid", group_address_state=GroupAddress("1/1/1")
        )
        state_updater = StateUpdater(xknx, remote_value_invalid)

        state_updater.started = True
        state_updater.update_received()
        reset.assert_called_once()

        state_updater = StateUpdater(xknx, remote_value_invalid, "init")
        state_updater.started = True
        reset.reset_mock()

        state_updater.update_received()
        reset.assert_not_called()

    @patch("xknx.core.state_updater._StateTracker._update_loop", new_callable=AsyncMock)
    async def test_state_updater_update_loop(self, _update_loop):
        """Test state tracker."""
        xknx = XKNX()
        remote_value_invalid = RemoteValue(
            xknx, sync_state="invalid", group_address_state=GroupAddress("1/1/1")
        )
        state_updater = StateUpdater(xknx, remote_value_invalid)
        state_updater._worker.reset()

        state_updater.stop()

    async def test_start_update_loop_and_stop_directly(self):
        """Test state tracker."""
        read_state_event = asyncio.Event()

        async def awaitable():
            """Fake read state mutex."""
            read_state_event.set()

        state_tracker = _StateTracker(awaitable, StateTrackerType.EXPIRE, 0.00001)
        task = asyncio.create_task(state_tracker._update_loop())
        await read_state_event.wait()
        task.cancel()

    @patch("logging.Logger.warning")
    def test_tracker_parser_invalid_options(self, logging_warning_mock):
        """Test parsing invalid tracker options."""
        xknx = XKNX()
        state_updater = None

        def _get_only_tracker() -> _StateTracker:
            # _workers is unordered so it just works with 1 item
            assert state_updater._worker
            return state_updater._worker

        # INVALID string
        remote_value_invalid = RemoteValue(
            xknx, sync_state="invalid", group_address_state=GroupAddress("1/1/1")
        )
        state_updater = StateUpdater(xknx, remote_value_invalid, "invalid")
        logging_warning_mock.assert_called_once_with(
            'Could not parse StateUpdater tracker_options "%s" for %s. Using default %s %s minutes.',
            "invalid",
            remote_value_invalid,
            StateTrackerType.EXPIRE,
            60,
        )
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 60 * 60
        remote_value_invalid.__del__()
        logging_warning_mock.reset_mock()
        # intervall too long
        remote_value_long = RemoteValue(
            xknx, sync_state=1441, group_address_state=GroupAddress("1/1/1")
        )
        state_updater = StateUpdater(xknx, remote_value_long, 1441)
        logging_warning_mock.assert_called_once_with(
            "StateUpdater interval of %s to long for %s. Using maximum of %s minutes (1 day)",
            1441,
            remote_value_long,
            1440,
        )
        remote_value_long.__del__()

    def test_state_updater_start_update_stop(self):
        """Test start, update_received and stop of StateUpdater."""
        xknx = XKNX()

        remote_value_1 = RemoteValue(
            xknx, sync_state=True, group_address_state=GroupAddress("1/1/1")
        )
        remote_value_2 = RemoteValue(
            xknx, sync_state=True, group_address_state=GroupAddress("1/1/2")
        )
        state_updater = StateUpdater(xknx, remote_value_1)
        state_updater._worker = Mock()

        assert not state_updater.started
        xknx.connection_manager._state = XknxConnectionState.CONNECTED
        state_updater.start()
        assert state_updater.started
        # start
        state_updater._worker.start.assert_called_once_with()
        # update
        state_updater.update_received()
        state_updater._worker.update_received.assert_called_once_with()
        # stop
        state_updater.stop()
        assert not state_updater.started
        state_updater._worker.stop.assert_called_once_with()
        # don't update when not started
        state_updater.update_received()
        state_updater._worker.update_received.assert_called_once_with()
