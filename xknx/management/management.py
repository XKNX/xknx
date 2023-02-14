"""Package for management communication."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
import logging
from typing import TYPE_CHECKING, Callable

from xknx.exceptions import (
    CommunicationError,
    ConfirmationError,
    ManagementConnectionError,
    ManagementConnectionRefused,
    ManagementConnectionTimeout,
)
from xknx.telegram import IndividualAddress, Telegram
from xknx.telegram.apci import APCI
from xknx.telegram.tpci import TAck, TConnect, TDataConnected, TDisconnect, TNak

if TYPE_CHECKING:
    from xknx.xknx import XKNX
logger = logging.getLogger("xknx.management")

MANAGAMENT_ACK_TIMEOUT = 3
MANAGAMENT_CONNECTION_TIMEOUT = 6


class Management:
    """Class for management procedures as described in KNX-Standard 3.5.2."""

    def __init__(self, xknx: XKNX) -> None:
        """Initialize Management class."""
        self.xknx = xknx
        self._connections: dict[IndividualAddress, P2PConnection] = {}

    def process(self, telegram: Telegram) -> None:
        """Process incoming telegrams."""
        if isinstance(telegram.tpci, TDataConnected):
            ack = Telegram(
                destination_address=telegram.source_address,
                tpci=TAck(sequence_number=telegram.tpci.sequence_number),
            )
            self.xknx.task_registry.background(
                self.xknx.cemi_handler.send_telegram(ack)
            )
        if conn := self._connections.get(telegram.source_address):
            conn.process(telegram)
            return
        if telegram.tpci.numbered:
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
        logger.warning("Unhandled management telegram: %r", telegram)
        return

    async def connect(self, address: IndividualAddress) -> P2PConnection:
        """Open a point-to-point connection to a KNX device."""
        if address in self._connections:
            raise ManagementConnectionError(f"Connection to {address} already exists.")
        p2p_connection = P2PConnection(self.xknx, address)
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
        self, address: IndividualAddress
    ) -> AsyncIterator[P2PConnection]:
        """Provide a point-to-point connection to a KNX device."""
        conn = await self.connect(address)
        try:
            yield conn
        finally:
            await self.disconnect(address)


class P2PConnection:
    """Class to manage a point-to-point connection with a KNX device."""

    def __init__(self, xknx: XKNX, address: IndividualAddress) -> None:
        """Initialize P2PConnection class."""
        self.xknx = xknx
        self.address = address
        self.disconnect_hook: Callable[[], None]

        self.sequence_number = self._sequence_number_generator()
        self._expected_sequence_number = 0
        self._connected = False

        self._ack_waiter: asyncio.Future[TAck | TNak] | None = None
        self._response_waiter: asyncio.Future[
            Telegram
        ] = asyncio.get_event_loop().create_future()

    @staticmethod
    def _sequence_number_generator() -> Generator[int, None, None]:
        """Generate sequence numbers."""
        seq_num = 0
        while True:
            yield seq_num
            seq_num = seq_num + 1 & 0xF

    async def connect(self) -> None:
        """Connect to the KNX device."""
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
        """Disconnect from the KNX device."""
        if not self._connected:
            self.disconnect_hook()  # remove connection from management class
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

    def process(self, telegram: Telegram) -> None:
        """Process incoming telegrams."""
        if isinstance(telegram.tpci, TDisconnect):
            logger.info("%s disconnected management session.", self.address)
            self._connected = False
            if self._ack_waiter:
                self._response_waiter.set_exception(ManagementConnectionRefused())
            if not self._response_waiter.done():
                self._response_waiter.set_exception(ManagementConnectionRefused())
            return
        if isinstance(telegram.tpci, (TAck, TNak)):
            if not self._ack_waiter:
                logger.warning("Received unexpected ACK/NAK: %s", telegram)
                return
            self._ack_waiter.set_result(telegram.tpci)
            return
        if self._response_waiter.done():
            logger.warning(
                "Received unexpected point-to-point telegram for %s: %s",
                self.address,
                telegram,
            )
            return
        if telegram.tpci.sequence_number != self._expected_sequence_number:
            logger.warning(
                "Received unexpected sequence number: %s (expected: %s)",
                telegram.tpci.sequence_number,
                self._expected_sequence_number,
            )
            return
        self._response_waiter.set_result(telegram)
        self._expected_sequence_number = self._expected_sequence_number + 1 & 0xF

    async def _send_data(self, payload: APCI) -> None:
        """
        Send a payload to the KNX device.

        A response has to be processed by `_receive` before sending the next telegram.
        """
        if not self._connected:
            raise ManagementConnectionRefused(
                "Management connection disconnected by the peer."
            )
        self._ack_waiter = asyncio.get_event_loop().create_future()
        seq_num = next(self.sequence_number)
        telegram = Telegram(
            destination_address=self.address,
            source_address=self.xknx.current_address,
            payload=payload,
            tpci=TDataConnected(sequence_number=seq_num),
        )
        try:
            await self.xknx.cemi_handler.send_telegram(telegram)
            ack = await asyncio.wait_for(self._ack_waiter, MANAGAMENT_ACK_TIMEOUT)
        except asyncio.TimeoutError:
            logger.debug(
                "%s: timeout while waiting for ACK. Resending Telegram.", self.address
            )
            # resend once after 3 seconds without ACK
            # on timeout the Future is cancelled so create a new
            self._ack_waiter = asyncio.get_event_loop().create_future()
            await self.xknx.cemi_handler.send_telegram(telegram)
            try:
                ack = await asyncio.wait_for(self._ack_waiter, MANAGAMENT_ACK_TIMEOUT)
            except asyncio.TimeoutError:
                raise ManagementConnectionTimeout(
                    "No ACK received for repeated telegram."
                ) from None
        except ConfirmationError as exc:
            raise ManagementConnectionError(
                f"Error while sending Telegram: {exc}"
            ) from exc
        except CommunicationError as exc:
            raise ManagementConnectionError("Error while sending Telegram") from exc
        finally:
            self._ack_waiter = None

        if isinstance(ack, TNak):
            raise ManagementConnectionError(
                f"Received no_ack from sending Telegram: {telegram}"
            )
        if ack.sequence_number != seq_num:
            raise ManagementConnectionError(
                f"Ack sequence number {ack.sequence_number} does not match request sequence number of {telegram}"
            )

    async def _receive(self, expected_payload: type[APCI] | None) -> Telegram:
        """Wait for a telegram from the KNX device."""
        try:
            telegram = await asyncio.wait_for(
                self._response_waiter, timeout=MANAGAMENT_CONNECTION_TIMEOUT
            )
        except asyncio.TimeoutError:
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

    async def request(self, payload: APCI, expected: type[APCI] | None) -> Telegram:
        """Send a payload to the KNX device and wait for the response."""
        if not self._connected:
            raise ManagementConnectionRefused(
                "Management connection disconnected by the peer."
            )
        await self._send_data(payload)
        return await self._receive(expected)
