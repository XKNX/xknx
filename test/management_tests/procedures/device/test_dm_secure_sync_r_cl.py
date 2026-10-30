"""Tests for dm_secure_sync_r_cl — KNX v02.01.02 - Management Procedures 03.05.02 - §4.2."""

import asyncio
from unittest.mock import AsyncMock, call, patch

import pytest

from xknx import XKNX
from xknx.cemi import CEMILData
from xknx.exceptions import DataSecureError, ManagementConnectionTimeout
from xknx.management.procedures.device.dm_secure_sync_r_cl import (
    dm_secure_sync_r_cl,
    dm_secure_sync_r_cl_conn,
)
from xknx.secure.data_secure import DataSecure
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

from ....conftest import EventLoopClockAdvancer

DEVICE = IndividualAddress("15.15.0")
TOOL_KEY = bytes(range(16))
# KNX v02.01.01 - Application Layer 03.03.07 - Annex C.1.4 S-A_Sync.res (Challenge 3)
SYNC_RES = apci.SecureAPDU.from_knx(
    bytes.fromhex("03F193aaaaaaaaaaa99c023ad25e146470693e638d5b70cac4")
)


def _setup() -> tuple[XKNX, DataSecure]:
    xknx = XKNX()
    xknx.current_address = IndividualAddress("15.15.103")
    data_secure = DataSecure(
        group_key_table={},
        individual_address_table={},
        last_sequence_number_sending=1,
        tool_key_table={DEVICE: TOOL_KEY},
    )
    xknx.cemi_handler = AsyncMock()
    xknx.cemi_handler.data_secure = data_secure
    return xknx, data_secure


def _respond(xknx: XKNX, conn_tpci: tpci.TPCI, payload: apci.APCI | None) -> None:
    """Feed an incoming frame of the device through the CEMI handler's Data Secure."""
    telegram = Telegram(
        source_address=DEVICE,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=conn_tpci,
        payload=payload,
    )
    if payload is not None:
        assert xknx.cemi_handler.data_secure is not None
        cemi = xknx.cemi_handler.data_secure.received_cemi(
            CEMILData.init_from_telegram(telegram)
        )
        telegram = cemi.telegram(TelegramDirection.INCOMING)
    xknx.management.process(telegram)


async def test_dm_secure_sync_r_cl_conn() -> None:
    """The response of the device synchronizes the Sequence Numbers."""
    xknx, data_secure = _setup()
    conn = await xknx.management.connect(DEVICE)
    with patch("secrets.token_bytes", return_value=bytes.fromhex("000000000003")):
        task = asyncio.create_task(dm_secure_sync_r_cl_conn(conn))
        await asyncio.sleep(0)
    request = xknx.cemi_handler.send_telegram.call_args_list[-1].args[0]
    assert isinstance(request.payload, apci.SecureAPDU)
    assert request.tpci == tpci.TDataConnected(sequence_number=0)

    _respond(xknx, tpci.TAck(sequence_number=0), None)
    _respond(xknx, tpci.TDataConnected(sequence_number=0), SYNC_RES)
    await task
    assert data_secure.tool_access_synchronized(DEVICE)
    # the device expects SeqNr 4 next
    assert data_secure.get_sequence_number() == 4


async def test_dm_secure_sync_r_cl(time_travel: EventLoopClockAdvancer) -> None:
    """Without a response the request is repeated once, then the procedure fails."""
    xknx, data_secure = _setup()
    task = asyncio.create_task(dm_secure_sync_r_cl(xknx, DEVICE))
    for sequence_number in (0, 1):
        await asyncio.sleep(0)
        _respond(xknx, tpci.TAck(sequence_number=sequence_number), None)
        await time_travel(6)
    with pytest.raises(ManagementConnectionTimeout):
        await task
    assert not data_secure.tool_access_synchronized(DEVICE)
    payloads = [
        type(c.args[0].payload)
        for c in xknx.cemi_handler.send_telegram.call_args_list
        if c.args[0].payload is not None
    ]
    assert payloads == [apci.SecureAPDU, apci.SecureAPDU]


async def test_dm_secure_sync_r_cl_without_data_secure() -> None:
    """Tool Access needs a DataSecure with the Tool Key."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    xknx.cemi_handler.data_secure = None
    conn = await xknx.management.connect(DEVICE)
    with pytest.raises(DataSecureError):
        await dm_secure_sync_r_cl_conn(conn)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(Telegram(destination_address=DEVICE, tpci=tpci.TConnect()))
    ]


async def test_dm_secure_sync_r_cl_without_tool_key() -> None:
    """A device without a Tool Key cannot be synchronized."""
    xknx, data_secure = _setup()
    data_secure.remove_tool_key(DEVICE)
    conn = await xknx.management.connect(DEVICE)
    with pytest.raises(DataSecureError, match="No Tool Key"):
        await dm_secure_sync_r_cl_conn(conn)
