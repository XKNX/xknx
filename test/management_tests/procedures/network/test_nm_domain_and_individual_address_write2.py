"""Tests for nm_domain_and_individual_address_write2 — KNX v02.01.02 - Management Procedures 03.05.02 - §2.10 NM_DomainAndIndividualAddress_Write2."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import MANAGEMENT_CONNECTION_TIMEOUT
from xknx.management.procedures.network.nm_domain_and_individual_address_write2 import (
    nm_domain_and_individual_address_write2,
)
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, apci, tpci

from ....conftest import EventLoopClockAdvancer

DOMAIN_ADDRESS = bytes.fromhex("00fa12345678")
NEW_ADDRESS = IndividualAddress("1.2.20")


def _in_programming_mode(source: str) -> Telegram:
    """Return the answer of a device in programming mode."""
    return Telegram(
        source_address=IndividualAddress(source),
        destination_address=GroupAddress("0/0/0"),
        tpci=tpci.TDataSystemBroadcast(),
        payload=apci.IndividualAddressResponse(),
    )


def _descriptor() -> Telegram:
    """Return the answer of the device at its new address."""
    return Telegram(
        source_address=NEW_ADDRESS,
        destination_address=IndividualAddress(0),
        tpci=tpci.TDataIndividual(),
        payload=apci.DeviceDescriptorResponse(descriptor=0, value=0x2705),
    )


def _sent(xknx: XKNX) -> list[Telegram]:
    """Return the telegrams sent."""
    return [call.args[0] for call in xknx.cemi_handler.send_telegram.call_args_list]


async def test_write(time_travel: EventLoopClockAdvancer) -> None:
    """Test the Domain Address and the individual address are written and verified."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    task = asyncio.create_task(
        nm_domain_and_individual_address_write2(xknx, DOMAIN_ADDRESS, NEW_ADDRESS)
    )
    await asyncio.sleep(0)
    xknx.management.process(_in_programming_mode("15.15.255"))
    await time_travel(3)
    xknx.management.process(_descriptor())
    assert await task == IndividualAddress("15.15.255")
    sent = _sent(xknx)
    assert [telegram.payload for telegram in sent] == [
        apci.IndividualAddressRead(),
        apci.DomainAddressWrite(domain_address=DOMAIN_ADDRESS),
        apci.IndividualAddressWrite(address=NEW_ADDRESS),
        apci.DeviceDescriptorRead(descriptor=0),
        apci.Restart(),
    ]
    # the broadcast services as system broadcast, then connectionless to the device
    assert [telegram.tpci for telegram in sent[:3]] == [tpci.TDataSystemBroadcast()] * 3
    assert all(telegram.destination_address == NEW_ADDRESS for telegram in sent[3:])
    assert [telegram.tpci for telegram in sent[3:]] == [tpci.TDataIndividual()] * 2


async def test_same_address_as_broadcast(time_travel: EventLoopClockAdvancer) -> None:
    """Test an address the device has is not written again, broadcasts without `system_broadcast`."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    task = asyncio.create_task(
        nm_domain_and_individual_address_write2(
            xknx, DOMAIN_ADDRESS, NEW_ADDRESS, timeout=1, system_broadcast=False
        )
    )
    await asyncio.sleep(0)
    xknx.management.process(_in_programming_mode(str(NEW_ADDRESS)))
    await time_travel(1)
    xknx.management.process(_descriptor())
    assert await task == NEW_ADDRESS
    sent = _sent(xknx)
    assert [type(telegram.payload) for telegram in sent] == [
        apci.IndividualAddressRead,
        apci.DomainAddressWrite,
        apci.DeviceDescriptorRead,
        apci.Restart,
    ]
    assert [telegram.tpci for telegram in sent[:2]] == [tpci.TDataBroadcast()] * 2


@pytest.mark.parametrize("devices", [[], ["1.1.4", "15.15.255"]])
async def test_not_one_device_in_programming_mode(
    time_travel: EventLoopClockAdvancer, devices: list[str]
) -> None:
    """Test nothing is written without exactly one device in programming mode."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    task = asyncio.create_task(
        nm_domain_and_individual_address_write2(xknx, DOMAIN_ADDRESS, NEW_ADDRESS)
    )
    await asyncio.sleep(0)
    for device in devices:
        xknx.management.process(_in_programming_mode(device))
    await time_travel(3)
    with pytest.raises(ManagementConnectionError, match="programming mode"):
        await task
    assert len(_sent(xknx)) == 1


async def test_no_answer_at_the_new_address(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test the procedure fails when the device does not answer at its new address."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    task = asyncio.create_task(
        nm_domain_and_individual_address_write2(xknx, DOMAIN_ADDRESS, NEW_ADDRESS)
    )
    await asyncio.sleep(0)
    xknx.management.process(_in_programming_mode("15.15.255"))
    await time_travel(3)
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)
    with pytest.raises(
        ManagementConnectionError, match=r"No device answered at 1\.2\.20"
    ):
        await task
    assert not any(isinstance(t.payload, apci.Restart) for t in _sent(xknx))
