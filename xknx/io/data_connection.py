"""
Building blocks shared by KNXnet/IP data connections.

KNX v01.06.02 - Core 03.08.02 - §5 "Communication Channels" defines the data
connection between a client and a server, with mechanics common to every
connection type - heartbeat monitoring (§5.4) and the sequence counter of
received frames (§5.3.4). Tunnelling and Device Management connections share
those mechanics while differing in what a failure means for them, so this
module implements the mechanics and leaves the policy with their owner.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from enum import Enum, auto
import logging

from xknx.exceptions import CommunicationError

from .const import HEARTBEAT_RATE

logger = logging.getLogger("xknx.log")


class ConnectionHeartbeat:
    """
    Keep a KNXnet/IP connection alive (KNX v01.06.02 - Core 03.08.02 - §5.4).

    While started, `send_connectionstate` is called every HEARTBEAT_RATE
    seconds and shall return the outcome of one ConnectionStateRequest as
    `(success, status)` - or None when the connection is already gone, which
    ends the heartbeat quietly. A failed one is repeated three (3) times, as
    the Core specification requires; when those fail as well - or the callable
    raises CommunicationError - the failure is logged under `name`,
    `on_failure` is awaited once and the heartbeat ends. What failure means -
    reconnecting a tunnel, closing a device management connection - is the
    owner's call.
    """

    __slots__ = ("_name", "_on_failure", "_send_connectionstate", "_task")

    def __init__(
        self,
        name: str,
        send_connectionstate: Callable[[], Awaitable[tuple[bool, str | None] | None]],
        on_failure: Callable[[], Awaitable[None]],
    ) -> None:
        """Initialize ConnectionHeartbeat class."""
        self._name = name
        self._send_connectionstate = send_connectionstate
        self._on_failure = on_failure
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """Start heartbeating. A previously running heartbeat is stopped."""
        self.stop()
        self._task = asyncio.create_task(self._run(), name=f"{self._name} heartbeat")

    def stop(self) -> None:
        """Stop heartbeating."""
        if self._task is not None:
            # `on_failure` may stop the heartbeat from within its own task
            if self._task is not asyncio.current_task():
                self._task.cancel()
            self._task = None

    async def _run(self) -> None:
        """Send heartbeats until one fails repeatedly. Worker task."""
        while True:
            await asyncio.sleep(HEARTBEAT_RATE)
            try:
                if (outcome := await self._send_connectionstate()) is None:
                    return
                success, status = outcome
                if success:
                    continue
                # Repeat the ConnectionStateRequest three times, then
                # terminate the connection - KNX v01.06.02 - Core 03.08.02 - §5.4.
                for _retry in range(3):
                    if (outcome := await self._send_connectionstate()) is None:
                        return
                    success, status = outcome
                    if success:
                        break
                if success:
                    continue
                logger.warning(
                    "%s heartbeat failed %s.",
                    self._name,
                    "- no response from the server"
                    if status is None
                    else f"with status: {status}",
                )
            except CommunicationError as err:
                logger.warning("%s heartbeat failed: %s", self._name, err)
            await self._on_failure()
            return


class SequenceVerdict(Enum):
    """How a received frame relates to the expected sequence counter."""

    EXPECTED = auto()  # acknowledge and process
    REPEATED = auto()  # acknowledge again, discard
    # discard without acknowledgement
    # (E_SEQUENCE_NUMBER - KNX v01.06.02 - Core 03.08.02 - §7.3.4)
    OUT_OF_ORDER = auto()


class IncomingSequenceCounter:
    """
    Track the sequence counter of frames received over a data connection.

    KNX v01.07.01 - Tunnelling 03.08.04 - §2.6.1 states the rules for both
    ends of a tunnel: the expected counter is acknowledged and processed; one
    less than expected is a repetition whose acknowledgement went missing -
    it is acknowledged again but discarded; anything else is discarded
    without an acknowledgement, which has the sender repeat the frame and
    terminate the connection when that is not acknowledged either.
    KNX v01.07.03 - Device Management 03.08.03 - §2.3.2 only spells out the
    server side; a client follows the same rules - taking its sentence
    literally would break the repetition it exists for.

    What to do on OUT_OF_ORDER beyond discarding stays with the caller:
    a tunnel schedules a reconnect for servers that fail to terminate, a
    device management client only observes.
    """

    __slots__ = ("expected",)

    def __init__(self) -> None:
        """Initialize IncomingSequenceCounter class."""
        self.expected = 0

    def reset(self) -> None:
        """Reset the counter - it starts at 0 for every established connection."""
        self.expected = 0

    def evaluate(self, sequence_counter: int) -> SequenceVerdict:
        """Evaluate a received sequence counter, advancing on the expected one."""
        if sequence_counter == self.expected:
            self.expected = self.expected + 1 & 0xFF
            return SequenceVerdict.EXPECTED
        if sequence_counter == self.expected - 1 & 0xFF:
            return SequenceVerdict.REPEATED
        return SequenceVerdict.OUT_OF_ORDER
