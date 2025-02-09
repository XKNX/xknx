"""Unit test for Telegram objects."""

from xknx.dpt import DPTBinary
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueRead, GroupValueWrite
from xknx.telegram.tpci import TConnect, TDisconnect


class TestTelegram:
    """Test class for Telegram objects."""

    #
    # EQUALITY
    #
    def test_telegram_equal(self) -> None:
        """Test equals operator."""
        assert Telegram(GroupAddress("1/2/3"), payload=GroupValueRead()) == Telegram(
            GroupAddress("1/2/3"), payload=GroupValueRead()
        )

    def test_telegram_not_equal(self) -> None:
        """Test not equals operator."""
        assert Telegram(GroupAddress("1/2/3"), payload=GroupValueRead()) != Telegram(
            GroupAddress("1/2/4"), payload=GroupValueRead()
        )
        assert Telegram(GroupAddress("1/2/3"), payload=GroupValueRead()) != Telegram(
            GroupAddress("1/2/3"), payload=GroupValueWrite(DPTBinary(1))
        )
        assert Telegram(GroupAddress("1/2/3"), payload=GroupValueRead()) != Telegram(
            GroupAddress("1/2/3"),
            TelegramDirection.INCOMING,
            payload=GroupValueRead(),
        )
        assert Telegram(IndividualAddress(1), tpci=TConnect()) != Telegram(
            IndividualAddress(1), tpci=TDisconnect()
        )
