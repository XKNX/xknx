"""Test for the shared KNXnet/IP connection primitives."""

from unittest.mock import AsyncMock

from xknx.exceptions import CommunicationError
from xknx.io.const import HEARTBEAT_RATE
from xknx.io.data_connection import (
    ConnectionHeartbeat,
    IncomingSequenceCounter,
    SequenceVerdict,
)

from ..conftest import EventLoopClockAdvancer


class TestIncomingSequenceCounter:
    """Test class for the incoming sequence counter."""

    def test_expected_advances(self) -> None:
        """Test that only the expected counter advances the state."""
        sequence = IncomingSequenceCounter()
        assert sequence.evaluate(0) is SequenceVerdict.EXPECTED
        assert sequence.expected == 1
        assert sequence.evaluate(1) is SequenceVerdict.EXPECTED
        assert sequence.expected == 2

    def test_repeated(self) -> None:
        """Test that a repetition is recognized and does not advance the state."""
        sequence = IncomingSequenceCounter()
        assert sequence.evaluate(0) is SequenceVerdict.EXPECTED
        assert sequence.evaluate(0) is SequenceVerdict.REPEATED
        assert sequence.expected == 1

    def test_out_of_sequence(self) -> None:
        """Test that any other counter is out of sequence."""
        sequence = IncomingSequenceCounter()
        assert sequence.evaluate(1) is SequenceVerdict.OUT_OF_ORDER
        assert sequence.evaluate(254) is SequenceVerdict.OUT_OF_ORDER
        assert sequence.expected == 0

    def test_wraparound(self) -> None:
        """Test that the counter wraps after 255, also for repetitions."""
        sequence = IncomingSequenceCounter()
        sequence.expected = 255
        assert sequence.evaluate(255) is SequenceVerdict.EXPECTED
        assert sequence.expected == 0
        # the frame before the expected one is still a repetition after the wrap
        assert sequence.evaluate(255) is SequenceVerdict.REPEATED

    def test_reset(self) -> None:
        """Test resetting the counter for a new connection."""
        sequence = IncomingSequenceCounter()
        sequence.expected = 42
        sequence.reset()
        assert sequence.expected == 0


class TestConnectionHeartbeat:
    """Test class for the connection heartbeat."""

    async def test_regular_heartbeat(self, time_travel: EventLoopClockAdvancer) -> None:
        """Test that a ConnectionStateRequest is sent every HEARTBEAT_RATE seconds."""
        send = AsyncMock(return_value=(True, None))
        on_failure = AsyncMock()
        heartbeat = ConnectionHeartbeat(send, on_failure)

        heartbeat.start()
        await time_travel(HEARTBEAT_RATE)
        assert send.await_count == 1
        await time_travel(HEARTBEAT_RATE)
        assert send.await_count == 2
        on_failure.assert_not_awaited()

        heartbeat.stop()
        assert heartbeat._task is None

    async def test_answered_repetition_recovers(
        self, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that an answered repetition keeps the heartbeat going."""
        send = AsyncMock(side_effect=[(False, None), (True, None), (True, None)])
        on_failure = AsyncMock()
        heartbeat = ConnectionHeartbeat(send, on_failure)

        heartbeat.start()
        await time_travel(HEARTBEAT_RATE)
        # the failed request and its answered repetition
        assert send.await_count == 2
        on_failure.assert_not_awaited()
        # the next regular heartbeat is sent again
        await time_travel(HEARTBEAT_RATE)
        assert send.await_count == 3

        heartbeat.stop()

    async def test_repeated_failure(self, time_travel: EventLoopClockAdvancer) -> None:
        """Test that a request failing repeatedly calls on_failure once and ends."""
        send = AsyncMock(return_value=(False, "E_CONNECTION_ID"))
        on_failure = AsyncMock()
        heartbeat = ConnectionHeartbeat(send, on_failure)

        heartbeat.start()
        task = heartbeat._task
        assert task is not None
        await time_travel(HEARTBEAT_RATE)

        # the initial request plus 3 repetitions - Core 03.08.02 §5.4
        assert send.await_count == 4
        on_failure.assert_awaited_once()
        assert task.done()

    async def test_communication_error(
        self, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a raising callable calls on_failure once and ends."""
        send = AsyncMock(side_effect=CommunicationError("boom"))
        on_failure = AsyncMock()
        heartbeat = ConnectionHeartbeat(send, on_failure)

        heartbeat.start()
        task = heartbeat._task
        assert task is not None
        await time_travel(HEARTBEAT_RATE)

        on_failure.assert_awaited_once()
        assert task.done()

    async def test_stop_from_on_failure(
        self, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that on_failure may stop the heartbeat from within its own task."""
        send = AsyncMock(return_value=(False, None))
        heartbeat = ConnectionHeartbeat(send, AsyncMock())

        async def stop_heartbeat() -> None:
            heartbeat.stop()

        heartbeat._on_failure = stop_heartbeat
        heartbeat.start()
        task = heartbeat._task
        assert task is not None
        await time_travel(HEARTBEAT_RATE)

        assert heartbeat._task is None
        assert task.done()
        assert not task.cancelled()

    async def test_restart(self, time_travel: EventLoopClockAdvancer) -> None:
        """Test that starting again stops a previously running heartbeat."""
        send = AsyncMock(return_value=(True, None))
        heartbeat = ConnectionHeartbeat(send, AsyncMock())

        heartbeat.start()
        first_task = heartbeat._task
        assert first_task is not None
        heartbeat.start()
        await time_travel(0)

        assert first_task.cancelled()
        assert heartbeat._task is not first_task

        heartbeat.stop()
