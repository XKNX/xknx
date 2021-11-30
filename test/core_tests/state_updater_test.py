"""Unit test for StateUpdater."""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from xknx import XKNX
from xknx.core import XknxConnectionState
from xknx.core.state_updater import StateTrackerType, StateUpdater, _StateTracker
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
        remote_value = RemoteValue(
            xknx, group_address_state=GroupAddress("1/1/1"), sync_state=False
        )

        xknx.connection_manager.connected.set()

        await remote_value.state_updater.read_state_mutex()

        read_state.assert_called_once()

    @patch("xknx.core.state_updater._StateTracker.reset")
    @patch("xknx.remote_value.RemoteValue.read_state")
    async def test_state_tracker_worker(self, reset, read_state, monkeypatch):
        """Test state tracker worker."""
        monkeypatch.undo()
        xknx = XKNX()
        remote_value = RemoteValue(xknx, group_address_state=GroupAddress("1/1/1"))

        xknx.connection_manager._state = XknxConnectionState.CONNECTED

        remote_value.state_updater.start()

        await remote_value.state_updater._worker._task

        read_state.assert_called_once()
        reset.assert_called_once()

        assert remote_value.state_updater.initialized.is_set()

        remote_value.state_updater.stop()

    @patch("xknx.core.state_updater._StateTracker.reset")
    async def test_state_tracker_update_received(self, reset):
        """Test state tracker."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx, group_address_state=GroupAddress("1/1/1"))

        remote_value.state_updater.started = True
        remote_value.state_updater.update_received()
        reset.assert_called_once()

        remote_value = RemoteValue(
            xknx, sync_state="init", group_address_state=GroupAddress("1/1/1")
        )
        remote_value.state_updater.started = True
        reset.reset_mock()

        remote_value.state_updater.update_received()
        reset.assert_not_called()

    @patch("xknx.core.state_updater._StateTracker._update_loop", new_callable=AsyncMock)
    async def test_state_updater_update_loop(self, _update_loop):
        """Test state tracker."""
        xknx = XKNX()
        remote_value = RemoteValue(
            xknx, sync_state=False, group_address_state=GroupAddress("1/1/1")
        )
        remote_value.state_updater._worker.reset()

        remote_value.state_updater.stop()

    async def test_start_update_loop_and_stop_directly(self):
        """Test state tracker."""
        read_state_event = asyncio.Event()

        async def awaitable():
            """Fake read state mutex."""
            read_state_event.set()

        def set_initialized_cb():
            """Fake set in intialized."""

        state_tracker = _StateTracker(
            awaitable, set_initialized_cb, StateTrackerType.EXPIRE, 0.00002
        )
        task = asyncio.create_task(state_tracker._update_loop())
        await read_state_event.wait()
        task.cancel()

    @patch("xknx.core.StateUpdater.start")
    @patch("xknx.core.StateUpdater.stop")
    @patch("logging.Logger.warning")
    def test_tracker_parser_invalid_options(self, logging_warning_mock, stop, start):
        """Test parsing invalid tracker options."""
        xknx = XKNX()
        remote_value = None

        def _get_only_tracker() -> _StateTracker:
            # _workers is unordered so it just works with 1 item
            assert remote_value.state_updater._worker
            return remote_value.state_updater._worker

        # INVALID string
        remote_value = RemoteValue(
            xknx, sync_state="invalid", group_address_state=GroupAddress("1/1/1")
        )
        logging_warning_mock.assert_called_once_with(
            'Could not parse StateUpdater tracker_options "%s" for %s. Using default %s %s minutes.',
            "invalid",
            remote_value,
            StateTrackerType.EXPIRE,
            60,
        )
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 60 * 60
        remote_value.__del__()
        logging_warning_mock.reset_mock()
        # intervall too long
        remote_value = RemoteValue(
            xknx, sync_state=1441, group_address_state=GroupAddress("1/1/1")
        )
        logging_warning_mock.assert_called_once_with(
            "StateUpdater interval of %s to long for %s. Using maximum of %s minutes (1 day)",
            1441,
            remote_value,
            1440,
        )
        remote_value.__del__()

    async def test_state_updater_start_update_stop(self, monkeypatch):
        """Test start, update_received and stop of StateUpdater."""
        monkeypatch.undo()
        xknx = XKNX()

        remote_value = RemoteValue(
            xknx, sync_state=True, group_address_state=GroupAddress("1/1/1")
        )
        remote_value.state_updater._worker = Mock()

        assert not remote_value.state_updater.started
        xknx.connection_manager._state = XknxConnectionState.CONNECTED
        remote_value.state_updater.start()
        assert remote_value.state_updater.started
        # start
        remote_value.state_updater._worker.start.assert_called_once_with()
        # update
        remote_value.state_updater.update_received()
        remote_value.state_updater._worker.update_received.assert_called_once_with()
        # stop
        remote_value.state_updater.stop()
        assert not remote_value.state_updater.started
        remote_value.state_updater._worker.stop.assert_called_once_with()
        # don't update when not started
        remote_value.state_updater.update_received()
        remote_value.state_updater._worker.update_received.assert_called_once_with()

        remote_value = RemoteValue(xknx, sync_state=True)
        remote_value.state_updater.start()

        assert not remote_value.state_updater.started

    async def test_state_updater_connection_handling(self, monkeypatch):
        """Test connection handling of state updater."""
        monkeypatch.undo()
        xknx = XKNX()

        remote_value = RemoteValue(
            xknx, sync_state=True, group_address_state=GroupAddress("1/1/1")
        )
        remote_value.state_updater._worker = Mock()

        assert not remote_value.state_updater.started
        remote_value.state_updater.start()
        assert not remote_value.state_updater.started

        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        assert remote_value.state_updater.started

        # process disconnect
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        assert not remote_value.state_updater.started

        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTING
        )
        assert not remote_value.state_updater.started

        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        assert remote_value.state_updater.started
