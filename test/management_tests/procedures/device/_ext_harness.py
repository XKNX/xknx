"""Shared helpers for the DMP_Ext* interface object procedure tests."""

import asyncio

from xknx import XKNX
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

RESPONDER_TIMEOUT = 1
IA = IndividualAddress("4.0.10")


def request(seq: int, payload: apci.APCI) -> Telegram:
    """Build the outgoing telegram for a given sequence number."""
    return Telegram(
        destination_address=IA, tpci=tpci.TDataConnected(seq), payload=payload
    )


def ack(seq: int) -> Telegram:
    """Build the outgoing ACK of a received response."""
    return Telegram(destination_address=IA, tpci=tpci.TAck(seq))


def process_ack(xknx: XKNX, seq: int) -> None:
    """Inject the ACK of a sent telegram into the management layer."""
    xknx.management.process(
        Telegram(
            source_address=IA,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(seq),
        )
    )


def process_response(xknx: XKNX, seq: int, payload: apci.APCI) -> None:
    """Inject ACK + TDataConnected response into the management layer."""
    process_ack(xknx, seq)
    xknx.management.process(
        Telegram(
            source_address=IA,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(seq),
            payload=payload,
        )
    )


async def wait_for_sent(xknx: XKNX, number: int) -> None:
    """Wait until `number` telegrams have been sent."""
    async with asyncio.timeout(RESPONDER_TIMEOUT):
        while xknx.cemi_handler.send_telegram.call_count < number:  # noqa: ASYNC110
            await asyncio.sleep(0)


def sent(xknx: XKNX) -> list[Telegram]:
    """Return the telegrams sent so far."""
    return [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list]
