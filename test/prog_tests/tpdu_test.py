"""Unit test for tpdu class."""
import asyncio
from unittest.mock import patch

import pytest
from xknx import XKNX
from xknx.prog.management import NM_EXISTS, NM_OK, NetworkManagement
from xknx.telegram import (
    IndividualAddress, 
    Telegram, 
    TelegramDirection, 
    TPDUType,
    )
from xknx.knxip.tpdu import TPDU


@pytest.mark.asyncio
class TestTpdu:
    """Test class for tpdu test."""

    async def test_tpdu(self):
        # test standard constructor
        xknx = XKNX()
        tpdu = TPDU(xknx, IndividualAddress("1.2.3"));
        # add data from knx
        in_bytes = bytes((0x11,0,0xB0,0x60,0,0,0,0x80,0,0x80))
        tpdu.from_knx(in_bytes) 
        # check serialzation result
        o_bytes = tpdu.to_knx()
        assert o_bytes == in_bytes
        # test telegram property
        telegram = Telegram(
            IndividualAddress("1.2.3"), TelegramDirection.OUTGOING, None, None, TPDUType.T_CONNECT
        )
        tpdu.telegram = telegram
        telegram_out = tpdu.telegram
        assert telegram.destination_address == telegram_out.destination_address
        # test constructor from telegram
        tpdu = TPDU.init_from_telegram(xknx, telegram, IndividualAddress("1.2.3"));
        # check serialzation result
        o_bytes = tpdu.to_knx()
        assert o_bytes == bytes((0x11,0,0xB0,0x60,0,0,0x12,0x03,0,0x80))
        # test calculated length
        assert tpdu.calculated_length() == 10
        # test string representation
        assert str(tpdu) == '<TPDUFrame DestinationAddress="IndividualAddress("1.2.3")"'
