"""Unit test for StateUpdater."""

import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from xknx import XKNX
from xknx.core import XknxConnectionState
from xknx.core.state_updater import StateTrackerType, _StateTracker
from xknx.dpt import DPTArray
from xknx.remote_value import RemoteValue, RemoteValueRaw
from xknx.telegram import GroupAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueRead, GroupValueResponse


@patch.multiple(RemoteValue, __abstractmethods__=set())
class TestStateUpdater:
    """Test class for state updater."""

    def test_register_unregister(self) -> None:
        """Test register and unregister."""
        xknx = XKNX()
        assert len(xknx.state_updater._workers) == 0
        # register when state address and sync_state is set
        remote_value_1: RemoteValue[Any] = RemoteValue(
            xknx, sync_state=True, group_address_state=GroupAddress("1/1/1")
        )
        assert len(xknx.state_updater._workers) == 0
        remote_value_1.register_state_updater()
        assert len(xknx.state_updater._workers) == 1
        # don't register when sync_state is False
        remote_value_2: RemoteValue[Any] = RemoteValue(
            xknx, sync_state=False, group_address_state=GroupAddress("1/1/1")
        )
        assert len(xknx.state_updater._workers) == 1
        remote_value_2.register_state_updater()
        assert len(xknx.state_updater._workers) == 1
        # manual registration
        xknx.state_updater.register_remote_value(remote_value_2)
        assert len(xknx.state_updater._workers) == 2
        # manual unregister
        xknx.state_updater.unregister_remote_value(remote_value_1)
        # only remote_value_2 remaining
        assert len(xknx.state_updater._workers) == 1
        assert next(iter(xknx.state_updater._workers.keys())) == id(remote_value_2)
        # unregister
        remote_value_2.unregister_state_updater()
        assert len(xknx.state_updater._workers) == 0
        # nothing to read without a state address
        remote_value_3: RemoteValue[Any] = RemoteValue(xknx, group_address="1/1/1")
        with pytest.raises(ValueError):
            xknx.state_updater.register_remote_value(remote_value_3)
        assert len(xknx.state_updater._workers) == 0

    def test_tracker_parser(self) -> None:
        """Test parsing tracker options."""
        xknx = XKNX()

        def _get_only_tracker() -> _StateTracker:
            # _workers is unordered so it just works with 1 item
            assert len(xknx.state_updater._workers) == 1
            _tracker = next(iter(xknx.state_updater._workers.values()))
            return _tracker

        # INIT
        remote_value_init: RemoteValue[Any] = RemoteValue(
            xknx, sync_state="init", group_address_state=GroupAddress("1/1/1")
        )
        remote_value_init.register_state_updater()
        assert _get_only_tracker().tracker_type == StateTrackerType.INIT
        remote_value_init.unregister_state_updater()
        # DEFAULT with int
        remote_value_expire: RemoteValue[Any] = RemoteValue(
            xknx, sync_state=2, group_address_state=GroupAddress("1/1/1")
        )
        remote_value_expire.register_state_updater()
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 2 * 60
        remote_value_expire.unregister_state_updater()
        # DEFAULT with float
        remote_value_expire = RemoteValue(
            xknx, sync_state=6.9, group_address_state=GroupAddress("1/1/1")
        )
        remote_value_expire.register_state_updater()
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 6.9 * 60
        remote_value_expire.unregister_state_updater()
        # EXPIRE with default time
        remote_value_expire = RemoteValue(
            xknx, sync_state="expire", group_address_state=GroupAddress("1/1/1")
        )
        remote_value_expire.register_state_updater()
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 60 * 60
        remote_value_expire.unregister_state_updater()
        # EXPIRE with 30 minutes
        remote_value_expire = RemoteValue(
            xknx, sync_state="expire 30", group_address_state=GroupAddress("1/1/1")
        )
        remote_value_expire.register_state_updater()
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 30 * 60
        remote_value_expire.unregister_state_updater()
        # PERIODICALLY with default time
        remote_value_every: RemoteValue[Any] = RemoteValue(
            xknx, sync_state="every", group_address_state=GroupAddress("1/1/1")
        )
        remote_value_every.register_state_updater()
        assert _get_only_tracker().tracker_type == StateTrackerType.PERIODICALLY
        assert _get_only_tracker().update_interval == 60 * 60
        remote_value_every.unregister_state_updater()
        # PERIODICALLY 10 * 60 seconds
        remote_value_every = RemoteValue(
            xknx, sync_state="every 10", group_address_state=GroupAddress("1/1/1")
        )
        remote_value_every.register_state_updater()
        assert _get_only_tracker().tracker_type == StateTrackerType.PERIODICALLY
        assert _get_only_tracker().update_interval == 10 * 60
        remote_value_every.unregister_state_updater()

    @patch("logging.Logger.warning")
    def test_tracker_parser_invalid_options(self, logging_warning_mock: Mock) -> None:
        """Test parsing invalid tracker options."""
        xknx = XKNX()

        def _get_only_tracker() -> _StateTracker:
            # _workers is unordered so it just works with 1 item
            assert len(xknx.state_updater._workers) == 1
            _tracker = next(iter(xknx.state_updater._workers.values()))
            return _tracker

        # INVALID string
        remote_value_invalid: RemoteValue[Any] = RemoteValue(
            xknx, sync_state="invalid", group_address_state=GroupAddress("1/1/1")
        )
        remote_value_invalid.register_state_updater()
        logging_warning_mock.assert_called_once_with(
            'Could not parse StateUpdater tracker_options "%s" for %s. Using default %s %s minutes.',
            "invalid",
            str(remote_value_invalid),
            StateTrackerType.EXPIRE,
            60,
        )
        assert _get_only_tracker().tracker_type == StateTrackerType.EXPIRE
        assert _get_only_tracker().update_interval == 60 * 60
        remote_value_invalid.unregister_state_updater()
        logging_warning_mock.reset_mock()
        # interval too long
        remote_value_long: RemoteValue[Any] = RemoteValue(
            xknx, sync_state=1441, group_address_state=GroupAddress("1/1/1")
        )
        remote_value_long.register_state_updater()
        logging_warning_mock.assert_called_once_with(
            "StateUpdater interval of %s to long for %s. Using maximum of %s minutes (1 day)",
            1441,
            str(remote_value_long),
            1440,
        )
        remote_value_long.unregister_state_updater()

    def test_state_updater_start_update_stop(self) -> None:
        """Test start, update_received and stop of StateUpdater."""
        xknx = XKNX()
        remote_value_1: RemoteValue[Any] = RemoteValue(
            xknx, sync_state=True, group_address_state=GroupAddress("1/1/1")
        )
        remote_value_2: RemoteValue[Any] = RemoteValue(
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

    async def test_parallel_reads_update_received(self) -> None:
        """Test update_received() while reading doesn't free a parallel read slot too early."""
        xknx = XKNX()
        xknx.state_updater._semaphore = asyncio.Semaphore(value=1)
        read_1_running = asyncio.Event()
        read_1_finish = asyncio.Event()

        async def read_state_1(wait_for_result: bool = False) -> None:
            """Read state of remote_value_1 - finishes when told to."""
            read_1_running.set()
            await read_1_finish.wait()

        remote_value_1 = Mock(read_state=read_state_1)
        remote_value_2 = Mock(read_state=AsyncMock())

        xknx.state_updater.register_remote_value(remote_value_1)
        xknx.connection_manager._state = XknxConnectionState.CONNECTED
        xknx.state_updater.start()
        await read_1_running.wait()
        assert xknx.state_updater._semaphore.locked()
        # a telegram for remote_value_1 was received while reading - the
        # tracker is reset, the read itself is shielded and keeps running
        xknx.state_updater.update_received(remote_value_1)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert xknx.state_updater._semaphore.locked()
        # the next read has to wait for the running one
        xknx.state_updater.register_remote_value(remote_value_2)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        remote_value_2.read_state.assert_not_awaited()

        read_1_finish.set()
        for _ in range(10):
            await asyncio.sleep(0)
        remote_value_2.read_state.assert_awaited_once_with(wait_for_result=True)
        assert not xknx.state_updater._semaphore.locked()
        xknx.state_updater.stop()

    async def test_read_error_after_update_received(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test an error of a read still running after update_received() is logged."""
        xknx = XKNX()
        xknx.state_updater._semaphore = asyncio.Semaphore(value=1)
        read_running = asyncio.Event()
        read_finish = asyncio.Event()

        async def read_state(wait_for_result: bool = False) -> None:
            """Read state - fails when told to finish."""
            read_running.set()
            await read_finish.wait()
            raise ValueError("read failed")

        remote_value = Mock(read_state=read_state)
        xknx.state_updater.register_remote_value(remote_value)
        xknx.connection_manager._state = XknxConnectionState.CONNECTED
        xknx.state_updater.start()
        await read_running.wait()
        # the tracker is cancelled while the shielded read keeps running
        xknx.state_updater.update_received(remote_value)
        await asyncio.sleep(0)
        assert xknx.state_updater._semaphore.locked()

        with caplog.at_level(logging.ERROR, logger="xknx.state_updater"):
            read_finish.set()
            for _ in range(10):
                await asyncio.sleep(0)
        assert not xknx.state_updater._semaphore.locked()
        assert "Unexpected error reading state of" in caplog.text
        assert "read failed" in caplog.text
        xknx.state_updater.stop()

    async def test_shared_state_address_single_read(self) -> None:
        """Test RemoteValues sharing a state address are read with one GroupValueRead."""
        xknx = XKNX()
        xknx.state_updater._semaphore = asyncio.Semaphore(value=2)
        read_1_running = asyncio.Event()
        read_1_finish = asyncio.Event()

        async def read_state_1(wait_for_result: bool = False) -> None:
            """Read state of remote_value_1 - finishes when told to."""
            read_1_running.set()
            await read_1_finish.wait()

        shared_address = GroupAddress("1/1/1")
        remote_value_1 = Mock(
            group_address_state=shared_address, read_state=read_state_1
        )
        remote_value_2 = Mock(
            group_address_state=shared_address, read_state=AsyncMock()
        )
        remote_value_3 = Mock(
            group_address_state=GroupAddress("1/1/3"), read_state=AsyncMock()
        )
        remote_value_4 = Mock(
            group_address_state=GroupAddress("1/1/4"), read_state=AsyncMock()
        )
        for remote_value in (
            remote_value_1,
            remote_value_2,
            remote_value_3,
            remote_value_4,
        ):
            xknx.state_updater.register_remote_value(remote_value, "init")
        xknx.connection_manager._state = XknxConnectionState.CONNECTED
        xknx.state_updater.start()
        await read_1_running.wait()
        for _ in range(10):
            await asyncio.sleep(0)
        # remote_value_2 waits for the read of remote_value_1 without holding a
        # `parallel_reads` slot - remote_value_3 is read in the second slot meanwhile
        remote_value_2.read_state.assert_not_awaited()
        remote_value_3.read_state.assert_awaited_once_with(wait_for_result=True)
        remote_value_4.read_state.assert_awaited_once_with(wait_for_result=True)
        assert not xknx.state_updater._workers[id(remote_value_2)]._task.done()

        read_1_finish.set()
        for _ in range(10):
            await asyncio.sleep(0)
        # the response to the read of remote_value_1 updated remote_value_2 as well
        remote_value_2.read_state.assert_not_awaited()
        assert xknx.state_updater._workers[id(remote_value_1)]._task.done()
        assert xknx.state_updater._workers[id(remote_value_2)]._task.done()
        assert not xknx.state_updater._pending_reads
        assert not xknx.state_updater._semaphore.locked()
        xknx.state_updater.stop()

    async def test_shared_state_address_leader_cancelled(self) -> None:
        """Test a waiting RemoteValue reads itself when the reading tracker is removed."""
        xknx = XKNX()
        xknx.state_updater._semaphore = asyncio.Semaphore(value=1)
        read_0_running = asyncio.Event()
        read_0_finish = asyncio.Event()

        async def read_state_0(wait_for_result: bool = False) -> None:
            """Read state of remote_value_0 - blocks the only slot until told to finish."""
            read_0_running.set()
            await read_0_finish.wait()

        shared_address = GroupAddress("1/1/1")
        remote_value_0 = Mock(
            group_address_state=GroupAddress("1/1/0"), read_state=read_state_0
        )
        remote_value_1 = Mock(
            group_address_state=shared_address, read_state=AsyncMock()
        )
        remote_value_2 = Mock(
            group_address_state=shared_address, read_state=AsyncMock()
        )
        for remote_value in (remote_value_0, remote_value_1, remote_value_2):
            xknx.state_updater.register_remote_value(remote_value, "init")
        xknx.connection_manager._state = XknxConnectionState.CONNECTED
        xknx.state_updater.start()
        await read_0_running.wait()
        await asyncio.sleep(0)
        # remote_value_1 waits for the slot, remote_value_2 waits for remote_value_1
        assert shared_address in xknx.state_updater._pending_reads
        xknx.state_updater.unregister_remote_value(remote_value_1)
        for _ in range(10):
            await asyncio.sleep(0)
        # remote_value_2 takes over the read
        assert shared_address in xknx.state_updater._pending_reads
        remote_value_2.read_state.assert_not_awaited()

        read_0_finish.set()
        for _ in range(10):
            await asyncio.sleep(0)
        remote_value_1.read_state.assert_not_awaited()
        remote_value_2.read_state.assert_awaited_once_with(wait_for_result=True)
        assert not xknx.state_updater._pending_reads
        assert not xknx.state_updater._semaphore.locked()
        xknx.state_updater.stop()

    async def test_shared_state_address_follower_cancelled(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test a waiting tracker being reset doesn't affect the running read."""
        xknx = XKNX()
        xknx.state_updater._semaphore = asyncio.Semaphore(value=1)
        read_1_running = asyncio.Event()
        read_1_finish = asyncio.Event()

        async def read_state_1(wait_for_result: bool = False) -> None:
            """Read state of remote_value_1 - finishes when told to."""
            read_1_running.set()
            await read_1_finish.wait()

        shared_address = GroupAddress("1/1/1")
        remote_value_1 = Mock(
            group_address_state=shared_address, read_state=read_state_1
        )
        remote_value_2 = Mock(
            group_address_state=shared_address, read_state=AsyncMock()
        )
        xknx.state_updater.register_remote_value(remote_value_1)
        xknx.state_updater.register_remote_value(remote_value_2)
        xknx.connection_manager._state = XknxConnectionState.CONNECTED
        xknx.state_updater.start()
        await read_1_running.wait()
        await asyncio.sleep(0)
        # a telegram for remote_value_2 was received while waiting - its tracker is reset
        xknx.state_updater.update_received(remote_value_2)
        await asyncio.sleep(0)
        assert shared_address in xknx.state_updater._pending_reads
        assert xknx.state_updater._semaphore.locked()

        with caplog.at_level(logging.WARNING, logger="xknx"):
            read_1_finish.set()
            for _ in range(10):
                await asyncio.sleep(0)
        assert not caplog.records
        remote_value_2.read_state.assert_not_awaited()
        assert not xknx.state_updater._pending_reads
        assert not xknx.state_updater._semaphore.locked()
        xknx.state_updater.stop()

    @patch("xknx.cemi.CEMIHandler.send_telegram", new_callable=AsyncMock)
    async def test_shared_state_address_one_telegram(
        self, _send_telegram_mock: AsyncMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test one GroupValueRead is sent and its response resolves every reader."""
        xknx = XKNX()
        shared_address = GroupAddress("1/1/1")
        remote_value_1 = RemoteValueRaw(
            xknx, 1, group_address_state=shared_address, sync_state="init"
        )
        remote_value_2 = RemoteValueRaw(
            xknx, 1, group_address_state=shared_address, sync_state="init"
        )
        remote_value_1.register_state_updater()
        remote_value_2.register_state_updater()
        xknx.connection_manager._state = XknxConnectionState.CONNECTED
        xknx.state_updater.start()
        for _ in range(10):
            await asyncio.sleep(0)
        assert xknx.telegrams.qsize() == 1
        assert xknx.telegrams.get_nowait() == Telegram(
            destination_address=shared_address, payload=GroupValueRead()
        )
        xknx.telegrams.task_done()
        # only one ValueReader - remote_value_2 waits for its result
        assert len(xknx.telegram_queue.telegram_received_cbs) == 1

        with caplog.at_level(logging.WARNING, logger="xknx"):
            await xknx.telegram_queue.process_telegram_incoming(
                Telegram(
                    destination_address=shared_address,
                    direction=TelegramDirection.INCOMING,
                    payload=GroupValueResponse(DPTArray((0x01,))),
                )
            )
            for _ in range(10):
                await asyncio.sleep(0)
        assert not caplog.records
        assert not xknx.telegram_queue.telegram_received_cbs
        assert xknx.telegrams.qsize() == 0
        assert xknx.state_updater._workers[id(remote_value_1)]._task.done()
        assert xknx.state_updater._workers[id(remote_value_2)]._task.done()
        assert not xknx.state_updater._pending_reads
        xknx.state_updater.stop()

    async def test_stop_start_state_updater_when_reconnecting(self) -> None:
        """Test start/stop state updater after reconnect."""

        xknx = XKNX()
        assert not xknx.state_updater.started

        xknx.connection_manager._state = XknxConnectionState.CONNECTED
        xknx.state_updater.start()

        assert xknx.state_updater.started

        xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )

        assert not xknx.state_updater.started

        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)

        assert xknx.state_updater.started

    @pytest.mark.parametrize(
        ("default", "sync_state_value", "expected_interval", "expected_tracker_type"),
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
        self,
        default: int | str | bool,
        sync_state_value: int | str | bool | None,
        expected_interval: int,
        expected_tracker_type: StateTrackerType,
    ) -> None:
        """Test setting a default for StateUpdater."""
        xknx = XKNX(state_updater=default)
        remote_value: RemoteValue[Any] = RemoteValue(
            xknx, sync_state=sync_state_value, group_address_state=GroupAddress("1/1/1")
        )
        remote_value.register_state_updater()
        assert (
            xknx.state_updater._workers[id(remote_value)].update_interval
            == expected_interval * 60
        )
        assert (
            xknx.state_updater._workers[id(remote_value)].tracker_type
            == expected_tracker_type
        )
