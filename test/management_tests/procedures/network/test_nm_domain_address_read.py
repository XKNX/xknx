"""Tests for nm_domain_address_read — KNX v02.01.02 - Management Procedures 03.05.02 - §2.7 NM_DomainAddress_Read."""

import asyncio
from unittest.mock import AsyncMock, call

from xknx import XKNX
from xknx.management.procedures.network.nm_domain_address_read import (
    nm_domain_address_read,
)
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, apci, tpci

from ....conftest import EventLoopClockAdvancer

DOMAIN_ADDRESS = bytes.fromhex("00fa12345678")


def _answer(source: str, domain_address: bytes) -> Telegram:
    """Return the answer of a device in programming mode."""
    return Telegram(
        source_address=IndividualAddress(source),
        destination_address=GroupAddress("0/0/0"),
        tpci=tpci.TDataSystemBroadcast(),
        payload=apci.DomainAddressResponse(domain_address=domain_address),
    )


async def test_nm_domain_address_read(time_travel: EventLoopClockAdvancer) -> None:
    """Test the Domain Addresses of the devices in programming mode are collected."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    task = asyncio.create_task(nm_domain_address_read(xknx, timeout=2))
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(
            Telegram(
                GroupAddress("0/0/0"),
                tpci=tpci.TDataSystemBroadcast(),
                payload=apci.DomainAddressRead(),
            )
        )
    ]
    xknx.management.process(_answer("1.1.4", DOMAIN_ADDRESS))
    xknx.management.process(_answer("15.15.255", bytes(6)))
    await time_travel(2)
    assert await task == [
        (IndividualAddress("1.1.4"), DOMAIN_ADDRESS),
        (IndividualAddress("15.15.255"), bytes(6)),
    ]


async def test_nm_domain_address_read_as_broadcast(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test the request is a broadcast without `system_broadcast`."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    task = asyncio.create_task(
        nm_domain_address_read(xknx, timeout=1, system_broadcast=False)
    )
    await asyncio.sleep(0)
    (sent,) = xknx.cemi_handler.send_telegram.call_args_list
    assert sent.args[0].tpci == tpci.TDataBroadcast()
    await time_travel(1)
    assert await task == []
