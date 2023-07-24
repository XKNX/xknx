"""Unit test for StateUpdater."""
from unittest.mock import Mock, patch

import pytest

from xknx import XKNX
from xknx.core import XknxConnectionState
from xknx.core.state_updater import StateTrackerType, _StateTracker
from xknx.remote_value import RemoteValue
from xknx.telegram import GroupAddress


@patch.multiple(RemoteValue, __abstractmethods__=set())
class TestStateUpdater:
    """Test class for state updater."""

    def test_register_unregister(self):
        """Test register and unregister."""
        xknx = XKNX()
        assert len(xknx.state_updater._workers) == 0
        # register when state address and sync_state is set
        remote_value_1 = RemoteValue(
            xknx, sync_state=True, group_address_state=GroupAddress("1/1/1")
        )
        assert len(xknx.state_updater._workers) == 1
        # don't register when sync_state is False
        remote_value_2 = RemoteValue(
            xknx, sync_state=False, group_address_state=GroupAddress("1/1/1")
        )
        assert len(xknx.state_updater._workers) == 1
        # manual registration
        xknx.state_updater.register_remote_value(remote_value_2)
        assert len(xknx.state_updater._workers) == 2
        # manual unregister
        xknx.state_updater.unregister_remote_value(remote_value_1)
        # only remote_value_2 remaining
        assert len(xknx.state_updater._workers) == 1
        assert next(iter(xknx.state_updater._workers.keys())) == id(remote_value_2)
        # unregister on RemoteValue.__del__()
        remote_value_2.__del__()
        assert len(xknx.state_updater._workers) == 0

    def test_tracker_parser(self):
        """Test parsing tracker options."""
        xknx = XKNX()

        def _get_only_tracker() -> _StateTracker:
            # _workers is unordered so it just works with 1 item
            assert len(xknx.state_updater._workers) == 1
            _tracker = next(iter(xknx.state_updater._workers.values()))
            return _tracker

        # INIT
        remote_value_init = RemoteValue(
            xknx, sync_state="init", group_address_state=GroupAddress("1/1/1")
        )
        assert _get_only_tracker().tracker_type == StateTrackerType.INIT
        remote_value_init.__del__()
        # DEFAULT with int
        remote_value_expire = RemoteValue(
            xknx, sync_state=2, group_address_state=GroupAddress("1/1/1")
        )
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 2 * 60
        remote_value_expire.__del__()
        # DEFAULT with float
        remote_value_expire = RemoteValue(
            xknx, sync_state=6.9, group_address_state=GroupAddress("1/1/1")
        )
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 6.9 * 60
        remote_value_expire.__del__()
        # EXPIRE with default time
        remote_value_expire = RemoteValue(
            xknx, sync_state="expire", group_address_state=GroupAddress("1/1/1")
        )
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 60 * 60
        remote_value_expire.__del__()
        # EXPIRE with 30 minutes
        remote_value_expire = RemoteValue(
            xknx, sync_state="expire 30", group_address_state=GroupAddress("1/1/1")
        )
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 30 * 60
        remote_value_expire.__del__()
        # PERIODICALLY with default time
        remote_value_every = RemoteValue(
            xknx, sync_state="every", group_address_state=GroupAddress("1/1/1")
        )
        assert _get_only_tracker().tracker_type == StateTrackerType.PERIODICALLY
        assert _get_only_tracker().update_interval == 60 * 60
        remote_value_every.__del__()
        # PERIODICALLY 10 * 60 seconds
        remote_value_every = RemoteValue(
            xknx, sync_state="every 10", group_address_state=GroupAddress("1/1/1")
        )
        assert _get_only_tracker().tracker_type == StateTrackerType.PERIODICALLY
        assert _get_only_tracker().update_interval == 10 * 60
        remote_value_every.__del__()

    @patch("logging.Logger.warning")
    def test_tracker_parser_invalid_options(self, logging_warning_mock):
        """Test parsing invalid tracker options."""
        xknx = XKNX()

        def _get_only_tracker() -> _StateTracker:
            # _workers is unordered so it just works with 1 item
            assert len(xknx.state_updater._workers) == 1
            _tracker = next(iter(xknx.state_updater._workers.values()))
            return _tracker

        # INVALID string
        remote_value_invalid = RemoteValue(
            xknx, sync_state="invalid", group_address_state=GroupAddress("1/1/1")
        )
        logging_warning_mock.assert_called_once_with(
            'Could not parse StateUpdater tracker_options "%s" for %s. Using default %s %s minutes.',
            "invalid",
            str(remote_value_invalid),
            StateTrackerType.EXPIRE,
            60,
        )
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 60 * 60
        remote_value_invalid.__del__()
        logging_warning_mock.reset_mock()
        # interval too long
        remote_value_long = RemoteValue(
            xknx, sync_state=1441, group_address_state=GroupAddress("1/1/1")
        )
        logging_warning_mock.assert_called_once_with(
            "StateUpdater interval of %s to long for %s. Using maximum of %s minutes (1 day)",
            1441,
            str(remote_value_long),
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
        xknx.state_updater._workers[id(remote_value_1)] = Mock()
        xknx.state_updater._workers[id(remote_value_2)] = Mock()

        assert not xknx.state_updater.started
        xknx.connection_manager._state = XknxConnectionState.CONNECTED
        xknx.state_updater.start()
        assert xknx.state_updater.started
        # start
        xknx.state_updater._workers[id(remote_value_1)].start.assert_called_once_with()
        xknx.state_updater._workers[id(remote_value_2)].start.assert_called_once_with()
        # update
        xknx.state_updater.update_received(remote_value_2)
        xknx.state_updater._workers[
            id(remote_value_1)
        ].update_received.assert_not_called()
        xknx.state_updater._workers[
            id(remote_value_2)
        ].update_received.assert_called_once_with()
        # stop
        xknx.state_updater.stop()
        assert not xknx.state_updater.started
        xknx.state_updater._workers[id(remote_value_1)].stop.assert_called_once_with()
        xknx.state_updater._workers[id(remote_value_2)].stop.assert_called_once_with()
        # don't update when not started
        xknx.state_updater.update_received(remote_value_1)
        xknx.state_updater._workers[
            id(remote_value_1)
        ].update_received.assert_not_called()

    async def test_stop_start_state_updater_when_reconnecting(self):
        """Test start/stop state updater after reconnect."""

        xknx = XKNX()
        assert not xknx.state_updater.started

        xknx.connection_manager._state = XknxConnectionState.CONNECTED
        xknx.state_updater.start()

        assert xknx.state_updater.started

        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )

        assert not xknx.state_updater.started

        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )

        assert xknx.state_updater.started

    @pytest.mark.parametrize(
        "default,sync_state_value,expected_interval,expected_tracker_type",
        [
            (90, True, 90, StateTrackerType.EXPIRE),
            (False, True, 60, StateTrackerType.EXPIRE),
            (True, None, 60, StateTrackerType.EXPIRE),
            (40, None, 40, StateTrackerType.EXPIRE),
            ("every 70", None, 70, StateTrackerType.PERIODICALLY),
            ("init", True, 60, StateTrackerType.INIT),
            ("every 80", "expire 20", 20, StateTrackerType.EXPIRE),
        ],
    )
    async def test_stat_updater_default(
        self, default, sync_state_value, expected_interval, expected_tracker_type
    ):
        """Test setting a default for StateUpdater."""
        xknx = XKNX(state_updater=default)
        remote_value = RemoteValue(
            xknx, sync_state=sync_state_value, group_address_state=GroupAddress("1/1/1")
        )
        assert (
            xknx.state_updater._workers[id(remote_value)].update_interval
            == expected_interval * 60
        )
        assert (
            xknx.state_updater._workers[id(remote_value)].tracker_type
            == expected_tracker_type
        )
