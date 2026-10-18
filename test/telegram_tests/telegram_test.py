"""Unit test for Telegram objects."""

from xknx.dpt import DPTBinary, DPTSwitch
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDecodedData,
    TelegramDirection,
    telegram_context,
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
        telegram_1.context = object()
        assert test == telegram_1

    def test_telegram_context(self) -> None:
        """Test outgoing telegrams carry the context of the active telegram_context."""
        context = object()
        assert Telegram(GroupAddress("1/2/3")).context is None
        with telegram_context(context):
            assert Telegram(GroupAddress("1/2/3")).context is context
            explicit = object()
            assert Telegram(GroupAddress("1/2/3"), context=explicit).context is explicit
            # incoming telegrams are not created by the application
            assert (
                Telegram(GroupAddress("1/2/3"), TelegramDirection.INCOMING).context
                is None
            )
            with telegram_context(None):
                assert Telegram(GroupAddress("1/2/3")).context is None
            assert Telegram(GroupAddress("1/2/3")).context is context
        assert Telegram(GroupAddress("1/2/3")).context is None
        assert "context" not in repr(Telegram(GroupAddress("1/2/3"), context=context))

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
