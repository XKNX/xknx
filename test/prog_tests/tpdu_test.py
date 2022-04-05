"""Unit test for tpdu class."""
import pytest

from xknx import XKNX
from xknx.knxip.tpdu import TPDU
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, TPDUType


@pytest.mark.asyncio
class TestTpdu:
    """Test class for tpdu test."""

    async def test_tpdu(self):
        # test standard constructor
        xknx = XKNX()
        tpdu = TPDU(xknx, IndividualAddress("1.2.3"))
        # add data from knx
        in_bytes = bytes.fromhex("1100b060000012010080")
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
        tpdu = TPDU.init_from_telegram(xknx, telegram, IndividualAddress("1.2.3"))
        # check serialzation result
        o_bytes = tpdu.to_knx()
        assert o_bytes == bytes.fromhex("1100B060000012030080")
        # test calculated length
        assert tpdu.calculated_length() == 10
        # test string representation
        assert str(tpdu) == '<TPDUFrame DestinationAddress="IndividualAddress("1.2.3")"'
