"""Package for management communication."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import aclosing, asynccontextmanager
import logging
import time
from typing import TYPE_CHECKING, overload

from xknx.exceptions import (
    CommunicationError,
    ConfirmationError,
    ManagementConnectionError,
    ManagementConnectionRefused,
    ManagementConnectionTimeout,
)
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import (
    APCI,
    APCIBroadcastRequest,
    APCIRequest,
    APCIResponseT,
)
from xknx.telegram.tpci import (
    TAck,
    TConnect,
    TDataBroadcast,
    TDataConnected,
    TDataIndividual,
    TDisconnect,
    TNak,
)

if TYPE_CHECKING:
    from xknx.xknx import XKNX
logger = logging.getLogger("xknx.management")

MANAGEMENT_ACK_TIMEOUT = 3
# KNX v01.02.03 - Transport Layer 03.03.04 - §4: max_rep_count, how often a
# T_Data_Connected is repeated without an ACK
MANAGEMENT_MAX_REPETITIONS = 3
MANAGEMENT_CONNECTION_TIMEOUT = 6
# telegrams per second a point-to-point connection sends at most
MANAGEMENT_RATE_LIMIT = 20


class Management:
    """Class for management procedures as described in KNX-Standard 3.5.2."""

    __slots__ = ("_connectionless", "_connections", "broadcast", "xknx")

    def __init__(self, xknx: XKNX) -> None:
        """Initialize Management class."""
        self.xknx = xknx
        self._connections: dict[IndividualAddress, P2PConnection] = {}
        self._connectionless: dict[IndividualAddress, P2PConnectionless] = {}
        self.broadcast = Broadcast(xknx)

    def process(self, telegram: Telegram) -> None:
        """Process incoming telegrams."""
        # only telegrams of a point-to-point connection are the connections
        # business - a device we are connected to may just as well send us an
        # unnumbered telegram, eg. answer a broadcast we sent
        if isinstance(telegram.tpci, TDataConnected | TAck | TNak | TDisconnect):
            if conn := self._connections.get(telegram.source_address):
                conn.process(telegram)
                return
            logger.warning(
                "No active point-to-point connection for received telegram: %s",
                telegram,
            )
            return
        if isinstance(telegram.tpci, TConnect):
            # refuse incoming connections
            # TODO: handle incoming telegrams for connections
            # not initiated by us, connection-less and broadcast
            disconnect = Telegram(
                destination_address=telegram.source_address, tpci=TDisconnect()
            )
            self.xknx.task_registry.background(
                self.xknx.cemi_handler.send_telegram(disconnect)
            )
            return
        if isinstance(telegram.tpci, TDataBroadcast):
            self.broadcast.process(telegram)
            return
        if isinstance(telegram.tpci, TDataIndividual) and (
            connectionless := self._connectionless.get(telegram.source_address)
        ):
            connectionless.process(telegram)
            return
        logger.debug("Unhandled management telegram: %r", telegram)

    async def connect(
        self, address: IndividualAddress, rate_limit: int = MANAGEMENT_RATE_LIMIT
    ) -> P2PConnection:
        """Open a point-to-point connection to a KNX device."""
        if address in self._connections:
            raise ManagementConnectionError(f"Connection to {address} already exists.")
        p2p_connection = P2PConnection(self.xknx, address, rate_limit)
        try:
            await p2p_connection.connect()
        except ManagementConnectionError as exc:
            logger.error("Establishing connection to %s failed: %s", address, exc)
            raise
        self._connections[address] = p2p_connection

        def remove_connection_hook() -> None:
            """Remove connection from management."""
            try:
                del self._connections[address]
            except KeyError:
                logger.error("Connection to %s already closed.", address)

        p2p_connection.disconnect_hook = remove_connection_hook
        return p2p_connection

    async def disconnect(self, address: IndividualAddress) -> None:
        """Close a point-to-point connection to a KNX device."""
        connection = self._connections.get(address)
        if connection is None:
            logger.error(
                "Closing connection to %s failed - connection does not exist.",
                address,
            )
            return
        try:
            await connection.disconnect()
        except ManagementConnectionError as exc:
            logger.error("Closing connection to %s failed: %s", connection.address, exc)
            raise

    @asynccontextmanager
    async def connection(
        self, address: IndividualAddress, rate_limit: int = MANAGEMENT_RATE_LIMIT
    ) -> AsyncGenerator[P2PConnection, None]:
        """Provide a point-to-point connection to a KNX device."""
        conn = await self.connect(address, rate_limit)
        try:
            yield conn
        finally:
            await self.disconnect(address)

    @asynccontextmanager
    async def connectionless(
        self, address: IndividualAddress, rate_limit: int = MANAGEMENT_RATE_LIMIT
    ) -> AsyncGenerator[P2PConnectionless, None]:
        """
        Provide connectionless point-to-point communication with a KNX device.

        Nothing is sent to open or close it - while the context is open, the
        T_Data_Individual telegrams the device sends us are handed to it instead
        of being dropped. Only one context per device can be open at a time, as
        a response could not be told apart otherwise.

        A connection-oriented `connection()` to the same device may be open at
        the same time - T_Data_Connected telegrams go to the connection,
        T_Data_Individual telegrams to this context.
        """
        if address in self._connectionless:
            raise ManagementConnectionError(
                f"Connectionless communication with {address} already exists."
            )
        connectionless = P2PConnectionless(self.xknx, address, rate_limit)
        self._connectionless[address] = connectionless
        try:
            yield connectionless
        finally:
            del self._connectionless[address]


class Broadcast:
    """
    Class for broadcast communication.

    Broadcast telegrams are sent to every device on the bus and answered by any
    number of them, so this owns the sending, the open receive contexts and the
    dispatching of incoming telegrams to them.
    """

    __slots__ = ("_contexts", "xknx")

    def __init__(self, xknx: XKNX) -> None:
        """Initialize Broadcast class."""
        self.xknx = xknx
        self._contexts: set[BroadcastContext] = set()

    def process(self, telegram: Telegram) -> None:
        """Hand an incoming broadcast telegram to every open context."""
        for context in self._contexts:
            context.queue.put_nowait(telegram)

    async def send(self, payload: APCI) -> None:
        """Send a broadcast message."""
        await self.xknx.cemi_handler.send_telegram(
            Telegram(
                GroupAddress("0/0/0"),
                tpci=TDataBroadcast(),
                payload=payload,
            )
        )

    async def request(
        self,
        payload: APCIBroadcastRequest[APCIResponseT],
        timeout: float | None = 3,
    ) -> AsyncGenerator[Telegram[APCIResponseT], None]:
        """
        Broadcast a request service and yield the responses to it.

        The request goes out when iteration starts, not when this is called. The
        receive context is opened before it is sent, so a device answering
        immediately can not be missed.

        Any number of devices may answer, so this yields until `timeout` elapses
        rather than returning one telegram like `P2PConnection.request()` does.
        Leaving the loop early is fine. Use `context()` with `send()` and
        `receive()` directly to keep one context across several requests.
        """
        async with self.context() as context:
            await self.send(payload)
            async for telegram in context.receive(
                payload.RESPONSE_TYPE, timeout=timeout
            ):
                yield telegram

    @asynccontextmanager
    async def context(self) -> AsyncGenerator[BroadcastContext, None]:
        """Provide a broadcast context."""
        context = BroadcastContext()
        self._contexts.add(context)
        try:
            yield context
        finally:
            self._contexts.remove(context)


class BroadcastContext:
    """
    A subscription to the broadcast channel.

    While the context is open every telegram sent to the broadcast address is
    queued here, whatever service it carries and whichever device sent it.
    """

    __slots__ = ("queue",)

    def __init__(self) -> None:
        """Initialize BroadcastContext class."""
        self.queue: asyncio.Queue[Telegram] = asyncio.Queue()

    @overload
    def receive(
        self,
        expected: type[APCIResponseT],
        timeout: float | None = 3,
    ) -> AsyncGenerator[Telegram[APCIResponseT], None]: ...
    @overload
    def receive(
        self,
        expected: None = None,
        timeout: float | None = 3,
    ) -> AsyncGenerator[Telegram, None]: ...
    async def receive(
        self,
        expected: type[APCI] | None = None,
        timeout: float | None = 3,
    ) -> AsyncGenerator[Telegram, None]:
        """
        Receive telegrams from the broadcast context.

        The broadcast channel carries telegrams of every service and from every
        device. Passing the APCI class to listen for yields only those, already
        narrowed to it; without it the caller has to sort them out itself.

        `timeout` is the window for the whole iteration, not for a single
        telegram. It is armed around the wait for the next telegram only, never
        across a `yield`, so that a caller can leave the loop as soon as it has
        what it needs - a timeout spanning the `yield` would stay armed on the
        abandoned generator and cancel whoever entered it once it elapsed.
        """
        deadline = (
            None if timeout is None else asyncio.get_running_loop().time() + timeout
        )
        while True:
            try:
                async with asyncio.timeout_at(deadline):
                    telegram = await self.queue.get()
            except TimeoutError:
                return
            if expected is None or isinstance(telegram.payload, expected):
                yield telegram


class P2PConnectionless:
    """
    Connectionless point-to-point communication with a KNX device.

    KNX v01.02.03 - Transport Layer 03.03.04 - §1.5: the point-to-point
    connectionless communication mode uses T_Data_Individual - no transport
    connection and no sequence numbers. §3.6: T_Data_Individual is neither
    acknowledged nor confirmed by the remote Transport Layer entity. Several
    management procedures may use it instead of a connection, e.g.
    DM_FunctionProperty_Write_R (KNX v02.01.02 - Management Procedures
    03.05.02 - §3.30.1). Open it with `Management.connectionless()`.

    `send()`, `receive()` and `request()` work like their counterparts of
    `Broadcast` and `BroadcastContext`, for the telegrams of one device.

    Named `P2PConnectionless` rather than `ConnectionlessP2P` so it sits next
    to `P2PConnection`: both are the point-to-point channel to one device, the
    suffix tells the transport mode apart.
    """

    __slots__ = (
        "_last_response_time",
        "_request_lock",
        "address",
        "queue",
        "rate_limit",
        "xknx",
    )

    def __init__(
        self,
        xknx: XKNX,
        address: IndividualAddress,
        rate_limit: int = MANAGEMENT_RATE_LIMIT,
    ) -> None:
        """Initialize P2PConnectionless class."""
        self.xknx = xknx
        self.address = address
        self.rate_limit = rate_limit
        self.queue: asyncio.Queue[Telegram] = asyncio.Queue()
        self._last_response_time: float = 0
        self._request_lock = asyncio.Lock()

    def process(self, telegram: Telegram) -> None:
        """Queue a T_Data_Individual telegram received from the device."""
        self.queue.put_nowait(telegram)

    async def send(self, payload: APCI) -> None:
        """
        Send a payload to the KNX device without waiting for a response.

        This is the call to make for one-way services like A_Restart - `request()`
        with a payload that is no `APCIRequest` waits up to its timeout for any
        telegram from the device.

        Telegrams queued before are discarded, so `receive()` afterwards yields
        only telegrams that arrived after this was sent, not e.g. a late response
        to an earlier request that timed out.
        """
        while not self.queue.empty():
            self.queue.get_nowait()
        telegram = Telegram(
            destination_address=self.address,
            source_address=self.xknx.current_address,
            payload=payload,
            tpci=TDataIndividual(),
        )
        try:
            await self.xknx.cemi_handler.send_telegram(telegram)
        except ConfirmationError as exc:
            raise ManagementConnectionError(
                f"Error while sending Telegram: {exc}"
            ) from exc
        except CommunicationError as exc:
            raise ManagementConnectionError("Error while sending Telegram") from exc

    @overload
    def receive(
        self,
        expected: type[APCIResponseT],
        timeout: float | None = MANAGEMENT_CONNECTION_TIMEOUT,
    ) -> AsyncGenerator[Telegram[APCIResponseT], None]: ...
    @overload
    def receive(
        self,
        expected: type[APCI] | None = None,
        timeout: float | None = MANAGEMENT_CONNECTION_TIMEOUT,
    ) -> AsyncGenerator[Telegram, None]: ...
    async def receive(
        self,
        expected: type[APCI] | None = None,
        timeout: float | None = MANAGEMENT_CONNECTION_TIMEOUT,
    ) -> AsyncGenerator[Telegram, None]:
        """
        Receive the telegrams the KNX device sends, until `timeout` elapses.

        Passing the APCI class to listen for yields only those, already narrowed
        to it, and skips any other telegram. Use it after `send()` when a
        procedure needs more than the first response - e.g. DMP_Connect_RCl
        (KNX v02.01.02 - Management Procedures 03.05.02 - §3.2.2): more than one
        A_DeviceDescriptor_Response means more than one device with the target
        address. Connectionless procedures carry their own timing, so pass
        theirs as `timeout`.

        `timeout` is the window for the whole iteration, not for a single
        telegram. Like for `BroadcastContext.receive()`, it is armed around the
        wait for the next telegram only, never across a `yield`, so a caller can
        leave the loop as soon as it has what it needs.

        Don't call it while a `request()` is running: both take telegrams from
        the same queue.
        """
        deadline = (
            None if timeout is None else asyncio.get_running_loop().time() + timeout
        )
        while True:
            try:
                async with asyncio.timeout_at(deadline):
                    telegram = await self.queue.get()
            except TimeoutError:
                return
            if expected is None or isinstance(telegram.payload, expected):
                yield telegram

    @overload
    async def request(
        self,
        payload: APCIRequest[APCIResponseT],
        *,
        timeout: float = MANAGEMENT_CONNECTION_TIMEOUT,
    ) -> Telegram[APCIResponseT]: ...
    @overload
    async def request(
        self, payload: APCI, *, timeout: float = MANAGEMENT_CONNECTION_TIMEOUT
    ) -> Telegram: ...
    async def request(
        self, payload: APCI, *, timeout: float = MANAGEMENT_CONNECTION_TIMEOUT
    ) -> Telegram:
        """
        Send a payload to the KNX device and wait for the response.

        This is `send()` followed by the first telegram of `receive()`. If the
        payload is an `APCIRequest`, the first telegram from the device carrying
        its `RESPONSE_TYPE` is returned and any other telegram is skipped -
        unlike a connection, the connectionless channel has no sequence to tell
        a response from unrelated traffic. Otherwise the first telegram from the
        device is returned. Use `send()` and `receive()` directly to see more
        than the first response.

        Telegrams queued before the request is sent are discarded, so a late
        response to an earlier request that timed out is not mistaken for this
        one's. Raises `ManagementConnectionTimeout` if no response arrives
        within `timeout` seconds.

        Concurrent calls are serialized - the next request is sent only after
        the previous one got its response or timed out, as nothing in a
        response tells which request it answers.
        """
        async with self._request_lock:
            if self.rate_limit:
                # time in seconds since the last request operation
                time_diff = time.time() - self._last_response_time
                wait_time = 1 / self.rate_limit
                if time_diff < wait_time:
                    await asyncio.sleep(wait_time - time_diff)

            expected = (
                payload.RESPONSE_TYPE if isinstance(payload, APCIRequest) else None
            )
            await self.send(payload)
            async with aclosing(self.receive(expected, timeout=timeout)) as telegrams:
                async for telegram in telegrams:
                    self._last_response_time = time.time()
                    return telegram
            raise ManagementConnectionTimeout(f"Timeout while waiting for {expected}")


class P2PConnection:
    """
    Class to manage a point-to-point connection with a KNX device.

    The connection follows the client state machine of KNX v01.02.03 -
    Transport Layer 03.03.04 - §5.4.1 (style 1, for clients that do not accept
    a connection from the bus). The states of §5.1 map to:

    - CLOSED: before `connect()`, and after the device or the connection itself
      closed it (`_connected` is False).
    - OPEN_IDLE: connected, no sent T_Data_Connected awaits its T_ACK
      (`_sequence_awaiting_ack` is None).
    - OPEN_WAIT: connected, `_sequence_awaiting_ack` holds SeqNoSend of the
      telegram awaiting its T_ACK.

    A transport layer error - no T_ACK after the last repetition, a T_NAK after
    it, or a T_ACK/T_NAK with an unexpected sequence number - closes the
    connection with action A6 (§5.3): a T_Disconnect is sent to the device and
    the waiting `send_data()` or `request()` raises. Later calls raise
    `ManagementConnectionRefused`; `disconnect()` only unregisters the
    connection then, as the T_Disconnect was sent already.
    """

    __slots__ = (
        "_ack_waiter",
        "_closed_locally",
        "_connected",
        "_expected_sequence_number",
        "_last_response_time",
        "_rep_count",
        "_response_waiter",
        "_sequence_awaiting_ack",
        "address",
        "disconnect_hook",
        "rate_limit",
        "sequence_number",
        "xknx",
    )

    def __init__(
        self,
        xknx: XKNX,
        address: IndividualAddress,
        rate_limit: int = MANAGEMENT_RATE_LIMIT,
    ) -> None:
        """Initialize P2PConnection class."""
        self.xknx = xknx
        self.address = address
        self.disconnect_hook: Callable[[], None]
        self.rate_limit = rate_limit

        self.sequence_number = self._sequence_number_generator()
        self._expected_sequence_number = 0
        self._connected = False
        # the connection closed itself (action A6) - the device was sent a
        # T_Disconnect already
        self._closed_locally = False
        # SeqNoSend of the T_Data_Connected awaiting its T_ACK (OPEN_WAIT)
        self._sequence_awaiting_ack: int | None = None
        # repetitions of that telegram - rep_count of §5
        self._rep_count = 0

        self._last_response_time: float = 0

        self._ack_waiter: asyncio.Future[TAck | TNak] | None = None
        self._response_waiter: asyncio.Future[Telegram] = (
            asyncio.get_event_loop().create_future()
        )

    @staticmethod
    def _sequence_number_generator() -> Generator[int, None, None]:
        """Generate sequence numbers."""
        seq_num = 0
        while True:
            yield seq_num
            seq_num = seq_num + 1 & 0xF

    async def connect(self) -> None:
        """
        Connect to the KNX device.

        Sends T_Connect-PDU (= A_Connect at wire level). KNX v02.01.01 - Application Layer
        03.03.07 - §3.5.1: "T_Connect.ind and T_Disconnect.ind are mapped transparently to
        A_Connect.ind and A_Disconnect.ind service and passed to the user of Application Layer."
        """
        connect = Telegram(
            destination_address=self.address,
            source_address=self.xknx.current_address,
            tpci=TConnect(),
        )
        try:
            await self.xknx.cemi_handler.send_telegram(connect)
        except ConfirmationError as exc:
            self._response_waiter.cancel()
            raise ManagementConnectionError(
                f"Connection to {self.address} failed: {exc}"
            ) from exc
        except CommunicationError as exc:
            self._response_waiter.cancel()
            raise ManagementConnectionError("Error while sending Telegram") from exc
        self._connected = True

    async def disconnect(self) -> None:
        """
        Disconnect from the KNX device. Sends T_Disconnect-PDU (= A_Disconnect, see connect()).

        Raises `ManagementConnectionRefused` if the device closed the connection
        before. If the connection closed itself after a transport layer error,
        the T_Disconnect was sent then - it is only unregistered here, without
        raising, so the error that closed it is the one the caller sees.
        """
        if not self._connected:
            self.disconnect_hook()  # remove connection from management class
            if self._closed_locally:
                return
            raise ManagementConnectionRefused(
                "Management connection disconnected by the peer."
            )
        self._connected = False

        disconnect = Telegram(
            destination_address=self.address,
            source_address=self.xknx.current_address,
            tpci=TDisconnect(),
        )
        try:
            await self.xknx.cemi_handler.send_telegram(disconnect)
        except ConfirmationError as exc:
            raise ManagementConnectionError(
                f"Disconnect from {self.address} failed: {exc}"
            ) from exc
        except CommunicationError as exc:
            raise ManagementConnectionError("Error while sending Telegram") from exc
        finally:
            if self._ack_waiter:
                self._ack_waiter.cancel()
            self._response_waiter.cancel()
            self.disconnect_hook()  # remove connection from management class

    def _send_control(self, tpci: TAck | TNak) -> None:
        """Acknowledge a received telegram - sent in the background."""
        telegram = Telegram(
            destination_address=self.address,
            source_address=self.xknx.current_address,
            tpci=tpci,
        )
        self.xknx.task_registry.background(
            self.xknx.cemi_handler.send_telegram(telegram)
        )

    def _closed_error(self) -> ManagementConnectionRefused:
        """Return the error for using a closed connection."""
        if self._closed_locally:
            return ManagementConnectionRefused(
                f"Management connection to {self.address} is closed."
            )
        return ManagementConnectionRefused(
            "Management connection disconnected by the peer."
        )

    def _wake_waiters(self, error: ManagementConnectionError) -> None:
        """
        End the waits for an ACK and for a response with `error`.

        This is the T_Disconnect.ind to the user of actions A5 and A6 - KNX
        v01.02.03 - Transport Layer 03.03.04 - §5.3.
        """
        for waiter in (self._ack_waiter, self._response_waiter):
            if waiter is not None and not waiter.done():
                waiter.set_exception(error)
                # no task may await it - e.g. no `request()` waits for a
                # response - so asyncio must not report it as never retrieved
                waiter.exception()

    def _close(self, error: ManagementConnectionError) -> None:
        """
        Close the connection after a transport layer error.

        Action A6 of KNX v01.02.03 - Transport Layer 03.03.04 - §5.3: send a
        T_Disconnect with priority system and sequence number 0 to the device,
        a T_Disconnect.ind to the user - here `error` for whoever waits - and
        go to CLOSED.
        """
        logger.warning("%s: %s Closing the connection.", self.address, error)
        self._connected = False
        self._closed_locally = True
        self._sequence_awaiting_ack = None
        self._wake_waiters(error)
        # individually addressed telegrams are sent with priority system, the
        # unnumbered T_Disconnect carries sequence number 0
        disconnect = Telegram(
            destination_address=self.address,
            source_address=self.xknx.current_address,
            tpci=TDisconnect(),
        )
        self.xknx.task_registry.background(
            self.xknx.cemi_handler.send_telegram(disconnect)
        )

    def _process_ack(self, ack: TAck | TNak) -> None:
        """
        Process a T_ACK or T_NAK from the device.

        KNX v01.02.03 - Transport Layer 03.03.04 - §5.4.1, events E08 and E09
        (T_ACK) and E11 to E13 (T_NAK) of §5.2. E10 and E14 - a T_ACK or T_NAK
        from another source address, ignored in OPEN_IDLE and OPEN_WAIT - never
        reach the connection, as `Management.process()` hands it only the
        telegrams of its device.
        """
        name = "ACK" if isinstance(ack, TAck) else "NAK"
        awaited = self._sequence_awaiting_ack
        if awaited is None:
            # OPEN_IDLE: E08, E09, E11, E12 and E13 -> A6
            self._close(
                ManagementConnectionError(
                    f"Received {name} {ack.sequence_number} while no telegram "
                    "awaits an acknowledgement."
                )
            )
            return
        if ack.sequence_number != awaited:
            # OPEN_WAIT: E09 and E11 -> A6
            self._close(
                ManagementConnectionError(
                    f"{name} sequence number {ack.sequence_number} does not match "
                    f"sequence number {awaited} of the sent telegram."
                )
            )
            return
        if isinstance(ack, TAck):
            # E08 -> A8: OPEN_IDLE
            self._sequence_awaiting_ack = None
        elif self._rep_count >= MANAGEMENT_MAX_REPETITIONS:
            # E13 -> A6
            self._close(
                ManagementConnectionError(
                    f"Received NAK {ack.sequence_number} after "
                    f"{self._rep_count} repetitions of the telegram."
                )
            )
            return
        # E08 confirms the telegram; E12 -> A9, `send_data()` repeats it
        if self._ack_waiter is not None and not self._ack_waiter.done():
            self._ack_waiter.set_result(ack)

    def process(self, telegram: Telegram) -> None:
        """Process incoming telegrams."""
        if not self._connected:
            # CLOSED - closed by the device or by an error, but not yet
            # unregistered by `disconnect()`
            logger.debug(
                "Ignoring telegram for closed connection to %s: %s",
                self.address,
                telegram,
            )
            return
        if isinstance(telegram.tpci, TDisconnect):
            # KNX v01.02.03 - Transport Layer 03.03.04 - §5.4.1: E02 -> A5
            logger.info("%s disconnected management session.", self.address)
            self._connected = False
            self._sequence_awaiting_ack = None
            self._wake_waiters(
                ManagementConnectionRefused(
                    f"Management connection to {self.address} disconnected by the peer."
                )
            )
            return
        if isinstance(telegram.tpci, TAck | TNak):
            self._process_ack(telegram.tpci)
            return
        if not isinstance(telegram.tpci, TDataConnected):
            logger.warning(
                "Received telegram of unexpected transport layer service for %s: %s",
                self.address,
                telegram,
            )
            return
        # KNX v01.02.03 - Transport Layer 03.03.04 - §5.3: acknowledging is a
        # transport layer duty, so it does not depend on anything waiting for
        # the payload - hence before the `_response_waiter` check below.
        sequence_number = telegram.tpci.sequence_number
        if sequence_number == self._expected_sequence_number:
            self._send_control(TAck(sequence_number=sequence_number))  # A2
            self._expected_sequence_number = sequence_number + 1 & 0xF
        elif sequence_number == self._expected_sequence_number - 1 & 0xF:
            # a repetition of the telegram we processed last - acknowledge it
            # again, the previous acknowledgement apparently did not arrive
            self._send_control(TAck(sequence_number=sequence_number))  # A3
            logger.debug(
                "Received repeated sequence number %s from %s",
                sequence_number,
                self.address,
            )
            return
        else:
            self._send_control(TNak(sequence_number=sequence_number))  # A4
            logger.warning(
                "Received unexpected sequence number: %s (expected: %s)",
                sequence_number,
                self._expected_sequence_number,
            )
            return
        if self._response_waiter.done():
            logger.warning(
                "Received unexpected point-to-point telegram for %s: %s",
                self.address,
                telegram,
            )
            return
        self._response_waiter.set_result(telegram)

    async def send_data(self, payload: APCI, wait_for_ack: bool = True) -> None:
        """
        Send a payload to the KNX device.

        If `wait_for_ack` is True (default), waits for the device to ACK the
        telegram. It is repeated up to `MANAGEMENT_MAX_REPETITIONS` times, each
        after `MANAGEMENT_ACK_TIMEOUT` without an ACK or right after a NAK. The
        response itself still has to be processed by `_receive` before sending
        the next telegram. Set `wait_for_ack=False` for commands the device
        doesn't ACK back - the telegram is not repeated then.

        KNX v01.02.03 - Transport Layer 03.03.04 - §5.4.1: if the device still
        doesn't ACK the telegram after the last repetition (E18), NAKs it after
        the last repetition (E13), or ACKs or NAKs another sequence number (E09,
        E11), the connection is closed (A6): a T_Disconnect is sent to the device
        and this raises `ManagementConnectionTimeout` for the missing ACK,
        `ManagementConnectionError` otherwise. A closed connection raises
        `ManagementConnectionRefused`.
        """
        if not self._connected:
            raise self._closed_error()
        seq_num = next(self.sequence_number)
        telegram = Telegram(
            destination_address=self.address,
            source_address=self.xknx.current_address,
            payload=payload,
            tpci=TDataConnected(sequence_number=seq_num),
        )
        # A7: OPEN_WAIT until the device acknowledges `seq_num`
        self._sequence_awaiting_ack = seq_num
        self._rep_count = 0
        if not wait_for_ack:
            # nothing repeats this telegram, so a NAK for it is E13
            self._rep_count = MANAGEMENT_MAX_REPETITIONS
            await self.xknx.cemi_handler.send_telegram(telegram)
            return

        try:
            while True:
                # on timeout the Future is cancelled so create a new one
                self._ack_waiter = asyncio.get_running_loop().create_future()
                await self.xknx.cemi_handler.send_telegram(telegram)
                try:
                    async with asyncio.timeout(MANAGEMENT_ACK_TIMEOUT):
                        ack = await self._ack_waiter
                except TimeoutError:
                    if self._rep_count >= MANAGEMENT_MAX_REPETITIONS:
                        # E18 -> A6
                        error = ManagementConnectionTimeout(
                            "No ACK received for repeated telegram."
                        )
                        self._close(error)
                        raise error from None
                    # E17 -> A9
                    reason = "timeout while waiting for ACK"
                else:
                    if isinstance(ack, TAck):
                        # E08 -> A8
                        return
                    # telegrams received after the NAK, before the repetition
                    # is sent, may have closed the connection or acknowledged it
                    if not self._connected:
                        raise self._closed_error()
                    if self._sequence_awaiting_ack != seq_num:
                        # E08 -> A8 - no longer awaiting the ACK
                        return
                    # E12 -> A9
                    reason = "received NAK"
                self._rep_count += 1
                logger.info(
                    "%s: %s. Resending Telegram (%s/%s).",
                    self.address,
                    reason,
                    self._rep_count,
                    MANAGEMENT_MAX_REPETITIONS,
                )
        except ConfirmationError as exc:
            raise ManagementConnectionError(
                f"Error while sending Telegram: {exc}"
            ) from exc
        except CommunicationError as exc:
            raise ManagementConnectionError("Error while sending Telegram") from exc
        finally:
            self._ack_waiter = None

    async def _receive(self, expected_payload: type[APCI] | None) -> Telegram:
        """Wait for a telegram from the KNX device."""
        try:
            async with asyncio.timeout(MANAGEMENT_CONNECTION_TIMEOUT):
                telegram = await self._response_waiter
        except TimeoutError:
            raise ManagementConnectionTimeout(
                f"Timeout while waiting for {expected_payload}"
            ) from None
        finally:
            # set up new Future for the next request
            self._response_waiter = asyncio.get_event_loop().create_future()

        if expected_payload and not isinstance(telegram.payload, expected_payload):
            raise ManagementConnectionError(
                f"Received unexpected telegram: {telegram.payload}"
            )
        return telegram

    @overload
    async def request(
        self, payload: APCIRequest[APCIResponseT]
    ) -> Telegram[APCIResponseT]: ...
    @overload
    async def request(self, payload: APCI) -> Telegram: ...
    async def request(self, payload: APCI) -> Telegram:
        """
        Send a payload to the KNX device and wait for the response.

        The response is verified against `type(payload).RESPONSE_TYPE` if the
        payload defines one - see `APCIRequest`. A transport layer error closes
        the connection - see `send_data()`; one while waiting for the response
        raises `ManagementConnectionError`.
        """
        if not self._connected:
            raise self._closed_error()

        if self.rate_limit:
            # time in seconds since the last request operation
            time_diff = time.time() - self._last_response_time
            wait_time = 1 / self.rate_limit
            if time_diff < wait_time:
                await asyncio.sleep(wait_time - time_diff)

        expected = payload.RESPONSE_TYPE if isinstance(payload, APCIRequest) else None
        await self.send_data(payload)
        response = await self._receive(expected)
        self._last_response_time = time.time()
        return response
