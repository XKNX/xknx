"""Test for group address dpt."""

from unittest.mock import patch

from xknx.dpt import DPTArray, DPTHumidity, DPTScaling, DPTTemperature
from xknx.telegram import GroupAddress, Telegram, TelegramDirection, apci


async def test_group_address_dpt_in_telegram_queue(xknx_no_interface):
    """Test group address dpt."""
    telegrams = 0
    test_telegram: Telegram = None

    async def _telegram_callback(telegram: Telegram):
        nonlocal telegrams
        nonlocal test_telegram
        telegrams += 1
        test_telegram = telegram

    xknx = xknx_no_interface
    telegram = Telegram(
        destination_address=GroupAddress("1/2/3"),
        direction=TelegramDirection.INCOMING,
        payload=apci.GroupValueWrite(DPTArray((0x7F,))),
    )
    xknx.telegram_queue.register_telegram_received_cb(_telegram_callback)
    async with xknx:
        await xknx.telegrams.put(telegram)
        await xknx.telegrams.join()
        assert telegrams == 1
        assert test_telegram.decoded_data is None

        xknx.group_address_dpt.set_dpts({GroupAddress("1/2/3"): {"main": 5, "sub": 1}})
        await xknx.telegrams.put(telegram)
        await xknx.telegrams.join()
        assert telegrams == 2
        assert test_telegram.decoded_data is not None
        assert test_telegram.decoded_data.transcoder is DPTScaling
        assert test_telegram.decoded_data.value == 50


def test_set_dpts(xknx_no_interface):
    """Test set_dpts."""
    xknx = xknx_no_interface
    xknx.group_address_dpt.set_dpts(
        {
            GroupAddress("1/2/3"): {"main": 5, "sub": 1},
            1: "temperature",
            "i-internal": "9.007",
        }
    )
    assert xknx.group_address_dpt._ga_dpts == {
        2563: DPTScaling,
        1: DPTTemperature,
        "i-internal": DPTHumidity,
    }
    assert (
        xknx.group_address_dpt.get_transcoder(GroupAddress("0/0/1")) is DPTTemperature
    )


@patch("logging.Logger.warning")
@patch("logging.Logger.debug")
def test_set_dpts_invalid(logger_debug_mock, logger_warning_mock, xknx_no_interface):
    """Test set invalid dpts."""
    xknx = xknx_no_interface
    xknx.group_address_dpt.set_dpts(
        {
            GroupAddress("0/0/1"): {"main": None},
            2: "invalid",
            0: "temperature",  # 0 is not a valid GA
        }
    )
    assert logger_warning_mock.call_count == 1
    assert "Invalid group address" in logger_warning_mock.call_args[0][0]
    assert logger_debug_mock.call_count == 1
    assert "No transcoder found for DPTs" in logger_debug_mock.call_args[0][0]
    assert not xknx.group_address_dpt._ga_dpts
