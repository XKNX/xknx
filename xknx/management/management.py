"""Package for management communication."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import aclosing, asynccontextmanager
import logging
import time
from typing import TYPE_CHECKING, NoReturn, overload

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

# KNX v01.02.03 - Transport Layer 03.03.04 - §4 Parameters of Transport Layer
MANAGEMENT_ACK_TIMEOUT = 3
MANAGEMENT_CONNECTION_TIMEOUT = 6
# repetitions of an unacknowledged T_Data_Connected before the connection is closed
MANAGEMENT_MAX_REP_COUNT = 3
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

        def remove_connection_hook() -> None:
            """Remove connection from management."""
            if self._connections.get(address) is p2p_connection:
                del self._connections[address]

        p2p_connection.disconnect_hook = remove_connection_hook
        # register before the T_Connect is sent so that a concurrent `connect()`
        # to the same address is refused and a T_Disconnect the device answers
        # with right away reaches the connection
        self._connections[address] = p2p_connection
        try:
            await p2p_connection.connect()
        except ManagementConnectionError as exc:
            remove_connection_hook()
            logger.error("Establishing connection to %s failed: %s", address, exc)
            raise
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
            # the transport layer may have closed it already, e.g. after a timeout
            if self._connections.get(address) is conn:
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
                time_diff = time.monotonic() - self._last_response_time
                wait_time = 1 / self.rate_limit
                if time_diff < wait_time:
                    await asyncio.sleep(wait_time - time_diff)

            expected = (
                payload.RESPONSE_TYPE if isinstance(payload, APCIRequest) else None
            )
            await self.send(payload)
            async with aclosing(self.receive(expected, timeout=timeout)) as telegrams:
                async for telegram in telegrams:
                    self._last_response_time = time.monotonic()
                    return telegram
            raise ManagementConnectionTimeout(f"Timeout while waiting for {expected}")


class P2PConnection:
    """
    Class to manage a point-to-point connection with a KNX device.

    Implements the client side of the connection-oriented Transport Layer state
    machine, KNX v01.02.03 - Transport Layer 03.03.04 - §5 (Style 3, §5.4.3, as
    amended by KNX AN210 v02 TL Style 3 Rework - §2.2.1). The events (E..) and
    actions (A..) named in the comments are the ones of its §5.2 and §5.3.
    Timing per its §4 and §5.5.1.9: a sent T_Data_Connected is repeated up to
    `MANAGEMENT_MAX_REP_COUNT` times when it is not acknowledged within
    `MANAGEMENT_ACK_TIMEOUT` seconds, and the connection is closed when nothing
    is sent or received for `MANAGEMENT_CONNECTION_TIMEOUT` seconds.

    The Transport Layer allows no parallel services on a connection, so
    `send_data()` and `request()` calls are serialized.
    """

    __slots__ = (
        "_ack_waiter",
        "_closed_by_peer",
        "_connected",
        "_connection_timer",
        "_expected_sequence_number",
        "_last_response_time",
        "_lock",
        "_response_waiter",
        "_sequence_number_send",
        "address",
        "disconnect_hook",
        "rate_limit",
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

        # SeqNoSend / SeqNoRcv of the Transport Layer state machine
        self._sequence_number_send = 0
        self._expected_sequence_number = 0
        self._connected = False
        self._closed_by_peer = False
        self._connection_timer: asyncio.TimerHandle | None = None
        self._lock = asyncio.Lock()

        self._last_response_time: float = 0

        # the T_ACK / T_NAK for the T_Data_Connected `_send_data` is waiting
        # for, or None when the acknowledge timeout elapsed
        self._ack_waiter: asyncio.Future[TAck | TNak | None] | None = None
        # the response `request` is waiting for - only set while one is pending
        self._response_waiter: asyncio.Future[Telegram] | None = None

    def _telegram(self, tpci: TConnect | TDisconnect | TAck | TNak) -> Telegram:
        """Build a Transport Layer control telegram to the device."""
        return Telegram(
            destination_address=self.address,
            source_address=self.xknx.current_address,
            tpci=tpci,
        )

    async def connect(self) -> None:
        """
        Connect to the KNX device.

        Sends T_Connect-PDU (= A_Connect at wire level). KNX v02.01.01 - Application Layer
        03.03.07 - §3.5.1: "T_Connect.ind and T_Disconnect.ind are mapped transparently to
        A_Connect.ind and A_Disconnect.ind service and passed to the user of Application Layer."
        """
        # E25 -> CONNECTING, A12. A T_Disconnect received while the T_Connect is
        # on its way (E02 -> A5) clears `_connected` again.
        self._connected = True
        try:
            await self.xknx.cemi_handler.send_telegram(self._telegram(TConnect()))
        except ConfirmationError as exc:
            self._connected = False
            raise ManagementConnectionError(
                f"Connection to {self.address} failed: {exc}"
            ) from exc
        except CommunicationError as exc:
            self._connected = False
            raise ManagementConnectionError("Error while sending Telegram") from exc
        if not self._connected:
            raise ManagementConnectionRefused(
                f"Connection to {self.address} refused by the device."
            )
        self._restart_connection_timer()

    async def disconnect(self) -> None:
        """Disconnect from the KNX device. Sends T_Disconnect-PDU (= A_Disconnect, see connect())."""
        if not self._connected:
            self.disconnect_hook()  # remove connection from management class
            if self._closed_by_peer:
                raise ManagementConnectionRefused(
                    "Management connection disconnected by the peer."
                )
            return  # closed by us before - the T_Disconnect was sent then
        # E26 -> A14
        self._close(ManagementConnectionError("Management connection closed."))
        try:
            await self.xknx.cemi_handler.send_telegram(self._telegram(TDisconnect()))
        except ConfirmationError as exc:
            raise ManagementConnectionError(
                f"Disconnect from {self.address} failed: {exc}"
            ) from exc
        except CommunicationError as exc:
            raise ManagementConnectionError("Error while sending Telegram") from exc
        finally:
            self.disconnect_hook()  # remove connection from management class

    def _close(self, exc: ManagementConnectionError) -> None:
        """
        Mark the connection closed and fail whatever is waiting on it with `exc`.

        This is the local part of A5 / A6 / A14: state CLOSED, timers stopped,
        T_Disconnect.ind to the user. Sending a T_Disconnect-PDU (A6, A14) and
        removing the connection from `Management` is up to the caller.
        """
        self._connected = False
        self._closed_by_peer = isinstance(exc, ManagementConnectionRefused)
        self._stop_connection_timer()
        for waiter in (self._ack_waiter, self._response_waiter):
            if waiter is not None and not waiter.done():
                waiter.set_exception(exc)

    async def _abort(self, exc: ManagementConnectionError) -> NoReturn:
        """
        Close the connection on an error (A6): send T_Disconnect-PDU and raise `exc`.

        The connection is removed from `Management` before, so a late telegram
        of the device is not handed to it anymore.
        """
        self._close(exc)
        self.disconnect_hook()
        try:
            await self.xknx.cemi_handler.send_telegram(self._telegram(TDisconnect()))
        except (ConfirmationError, CommunicationError) as send_exc:
            logger.warning(
                "%s: sending T_Disconnect while closing failed: %s",
                self.address,
                send_exc,
            )
        raise exc

    def _restart_connection_timer(self) -> None:
        """
        (Re)start the connection timeout timer.

        KNX v01.02.03 - Transport Layer 03.03.04 - §5: it is started when the
        connection is opened and restarted whenever a T_Data_Connected is sent
        or a telegram of the connection is received (A2, A3, A4, A7, A8, A9).
        """
        self._stop_connection_timer()
        self._connection_timer = asyncio.get_running_loop().call_later(
            MANAGEMENT_CONNECTION_TIMEOUT, self._connection_timeout
        )

    def _stop_connection_timer(self) -> None:
        """Stop the connection timeout timer."""
        if self._connection_timer is not None:
            self._connection_timer.cancel()
            self._connection_timer = None

    def _connection_timeout(self) -> None:
        """Close the connection after `MANAGEMENT_CONNECTION_TIMEOUT` without traffic (E16 -> A6)."""
        self._connection_timer = None
        logger.info(
            "%s: connection timed out - nothing received for %s seconds.",
            self.address,
            MANAGEMENT_CONNECTION_TIMEOUT,
        )
        self._close(
            ManagementConnectionTimeout(
                f"Connection to {self.address} timed out - nothing received for "
                f"{MANAGEMENT_CONNECTION_TIMEOUT} seconds."
            )
        )
        self.disconnect_hook()
        self.xknx.task_registry.background(
            self.xknx.cemi_handler.send_telegram(self._telegram(TDisconnect()))
        )

    def _ack_timeout(self) -> None:
        """Acknowledge timeout (E17 / E18) - wake `_send_data` to repeat the telegram or close."""
        if self._ack_waiter is not None and not self._ack_waiter.done():
            self._ack_waiter.set_result(None)
        # the repetition (A9) restarts the connection timer - do it right away
        # so it can not expire before `_send_data` gets to run, e.g. when the
        # event loop was stalled and both timers are due at once
        self._restart_connection_timer()

    def _send_control(self, tpci: TAck | TNak) -> None:
        """Acknowledge a received telegram - sent in the background."""
        self.xknx.task_registry.background(
            self.xknx.cemi_handler.send_telegram(self._telegram(tpci))
        )

    def process(self, telegram: Telegram) -> None:
        """Process incoming telegrams."""
        if isinstance(telegram.tpci, TDisconnect):
            # E02 -> A5. The connection stays registered in `Management` until
            # `disconnect()` is called, which raises to tell the peer closed it.
            logger.info("%s disconnected management session.", self.address)
            self._close(
                ManagementConnectionRefused(
                    "Management connection disconnected by the peer."
                )
            )
            return
        if isinstance(telegram.tpci, TAck | TNak):
            if telegram.tpci.sequence_number != self._sequence_number_send:
                # E09 / E11 -> A0: KNX AN210 v02 TL Style 3 Rework - §2.2.1
                # a T_ACK with a wrong sequence number is ignored like a T_NAK
                # with one - it is most probably a repetition on the medium
                logger.warning(
                    "Received %s with unexpected sequence number from %s: %s (expected: %s)",
                    type(telegram.tpci).__name__,
                    self.address,
                    telegram.tpci.sequence_number,
                    self._sequence_number_send,
                )
                return
            if self._ack_waiter is None or self._ack_waiter.done():
                logger.warning("Received unexpected ACK/NAK: %s", telegram)
                return
            self._ack_waiter.set_result(telegram.tpci)
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
            self._restart_connection_timer()
        elif sequence_number == self._expected_sequence_number - 1 & 0xF:
            # a repetition of the telegram we processed last - acknowledge it
            # again, the previous acknowledgement apparently did not arrive
            self._send_control(TAck(sequence_number=sequence_number))  # A3
            self._restart_connection_timer()
            logger.debug(
                "Received repeated sequence number %s from %s",
                sequence_number,
                self.address,
            )
            return
        else:
            self._send_control(TNak(sequence_number=sequence_number))  # A4
            self._restart_connection_timer()
            logger.warning(
                "Received unexpected sequence number: %s (expected: %s)",
                sequence_number,
                self._expected_sequence_number,
            )
            return
        if self._response_waiter is None or self._response_waiter.done():
            # nothing is waiting for it - e.g. a response arriving after its
            # request timed out. It must not be taken for the next one's.
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
        telegram, repeating it up to `MANAGEMENT_MAX_REP_COUNT` times when no
        ACK or a NAK arrives within `MANAGEMENT_ACK_TIMEOUT` seconds. If it is
        still not acknowledged, the connection is closed with a T_Disconnect
        and `ManagementConnectionTimeout` (no ACK) or `ManagementConnectionError`
        (NAK) is raised. The response itself still has to be processed by
        `request()`. Set `wait_for_ack=False` for commands the device doesn't
        ACK back.

        Concurrent calls, and `request()` calls, are serialized.
        """
        async with self._lock:
            await self._send_data(payload, wait_for_ack)

    async def _send_data(self, payload: APCI, wait_for_ack: bool) -> None:
        """Send a payload to the KNX device - the caller holds `_lock`."""
        if not self._connected:
            raise ManagementConnectionRefused(
                "Management connection disconnected by the peer."
            )
        seq_num = self._sequence_number_send
        telegram = Telegram(
            destination_address=self.address,
            source_address=self.xknx.current_address,
            payload=payload,
            tpci=TDataConnected(sequence_number=seq_num),
        )
        if not wait_for_ack:
            await self.xknx.cemi_handler.send_telegram(telegram)
            # A7 and, as if acknowledged, A8
            self._sequence_number_send = seq_num + 1 & 0xF
            self._restart_connection_timer()
            return

        loop = asyncio.get_running_loop()
        ack: TAck | TNak | None = None
        try:
            # A7, then A9 for each repetition
            for rep_count in range(MANAGEMENT_MAX_REP_COUNT + 1):
                if rep_count:
                    logger.info(
                        "%s: %s for %s. Repeating Telegram (%s/%s).",
                        self.address,
                        "no ACK received" if ack is None else "NAK received",
                        telegram,
                        rep_count,
                        MANAGEMENT_MAX_REP_COUNT,
                    )
                # create it before sending so an ACK arriving while the send is
                # confirmed, or a disconnect, is not missed
                self._ack_waiter = loop.create_future()
                await self.xknx.cemi_handler.send_telegram(telegram)
                self._restart_connection_timer()
                ack_timer = loop.call_later(MANAGEMENT_ACK_TIMEOUT, self._ack_timeout)
                try:
                    ack = await self._ack_waiter
                finally:
                    ack_timer.cancel()
                if isinstance(ack, TAck):
                    break  # E08
                # E17 / E18 (ack is None) or E12 / E13 (NAK)
            else:
                # E18 / E13 -> A6
                if ack is None:
                    await self._abort(
                        ManagementConnectionTimeout(
                            f"No ACK received for repeated telegram: {telegram}"
                        )
                    )
                await self._abort(
                    ManagementConnectionError(
                        f"Received NAK for repeated telegram: {telegram}"
                    )
                )
        except ConfirmationError as exc:
            raise ManagementConnectionError(
                f"Error while sending Telegram: {exc}"
            ) from exc
        except CommunicationError as exc:
            raise ManagementConnectionError("Error while sending Telegram") from exc
        finally:
            self._ack_waiter = None
        # A8
        self._sequence_number_send = seq_num + 1 & 0xF
        self._restart_connection_timer()

    async def _receive(self, expected_payload: type[APCI] | None) -> Telegram:
        """
        Wait for the response to the pending request.

        The response waiter is failed by `_close()` when the connection is
        closed meanwhile - with `ManagementConnectionTimeout` when nothing was
        received for `MANAGEMENT_CONNECTION_TIMEOUT` seconds.
        """
        assert self._response_waiter is not None
        telegram = await self._response_waiter
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
        payload defines one - see `APCIRequest`. Raises
        `ManagementConnectionTimeout` when no response arrives within
        `MANAGEMENT_CONNECTION_TIMEOUT` seconds - the connection is closed then.

        Concurrent calls, and `send_data()` calls, are serialized.
        """
        async with self._lock:
            if not self._connected:
                raise ManagementConnectionRefused(
                    "Management connection disconnected by the peer."
                )

            if self.rate_limit:
                # time in seconds since the last request operation
                time_diff = time.monotonic() - self._last_response_time
                wait_time = 1 / self.rate_limit
                if time_diff < wait_time:
                    await asyncio.sleep(wait_time - time_diff)

            expected = (
                payload.RESPONSE_TYPE if isinstance(payload, APCIRequest) else None
            )
            # accept a response from now on - it may even arrive before the ACK
            self._response_waiter = asyncio.get_running_loop().create_future()
            try:
                await self._send_data(payload, wait_for_ack=True)
                response = await self._receive(expected)
            finally:
                waiter, self._response_waiter = self._response_waiter, None
                if waiter.done() and not waiter.cancelled():
                    # `_close()` may have failed it while `_send_data` raised -
                    # retrieve it so asyncio doesn't log it as never retrieved
                    waiter.exception()
            self._last_response_time = time.monotonic()
            return response
