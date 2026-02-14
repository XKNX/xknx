"""Unit test for Telegram objects."""

from xknx.dpt import DPTBinary, DPTSwitch
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDecodedData,
    TelegramDirection,
)
from xknx.telegram.apci import GroupValueRead, GroupValueWrite
from xknx.telegram.tpci import TConnect, TDisconnect


class TestTelegram:
    """Test class for Telegram objects."""

    #
    # EQUALITY
    #
    def test_telegram_equal(self) -> None:
        """Test equals operator."""
        test = Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())
        telegram_1 = Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())
        assert test == telegram_1
        # decoded_data and data_secure should not be considered for equality (although
        # decoded_data doesn't make sense for a GroupValueRead, this is just for testing the equality operator)
        telegram_1.decoded_data = TelegramDecodedData(transcoder=DPTSwitch, value=False)
        telegram_1.data_secure = True
        assert test == telegram_1

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
