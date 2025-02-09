"""Test for group address dpt."""

from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.dpt import DPTArray, DPTHumidity, DPTScaling, DPTTemperature
from xknx.telegram import GroupAddress, Telegram, TelegramDirection, apci


async def test_group_address_dpt_in_telegram_queue(xknx_no_interface: XKNX) -> None:
    """Test group address dpt."""
    xknx = xknx_no_interface
    telegram = Telegram(
        destination_address=GroupAddress("1/2/3"),
        direction=TelegramDirection.INCOMING,
        payload=apci.GroupValueWrite(DPTArray((0x7F,))),
    )
    read_telegram = Telegram(
        destination_address=GroupAddress("1/2/3"),
        direction=TelegramDirection.INCOMING,
        payload=apci.GroupValueRead(),
    )
    telegram_callback = Mock()
    xknx.telegram_queue.register_telegram_received_cb(telegram_callback)
    async with xknx:
        xknx.telegrams.put_nowait(telegram)
        await xknx.telegrams.join()
        assert telegram_callback.call_count == 1
        test_telegram = telegram_callback.call_args[0][0]
        assert test_telegram.decoded_data is None

        xknx.group_address_dpt.set({GroupAddress("1/2/3"): {"main": 5, "sub": 1}})
        xknx.telegrams.put_nowait(telegram)
        await xknx.telegrams.join()
        assert telegram_callback.call_count == 2
        test_telegram = telegram_callback.call_args[0][0]
        assert test_telegram.decoded_data is not None
        assert test_telegram.decoded_data.transcoder is DPTScaling
        assert test_telegram.decoded_data.value == 50
        # do nothing for read-telegrams
        xknx.telegrams.put_nowait(read_telegram)
        await xknx.telegrams.join()
        assert telegram_callback.call_count == 3
        test_telegram = telegram_callback.call_args[0][0]
        assert test_telegram.decoded_data is None


@patch("logging.Logger.warning")
async def test_get_invalid_payload(
    logger_warning_mock: Mock, xknx_no_interface: XKNX
) -> None:
    """Test processing when DPT doesn't fit payload."""
    xknx = xknx_no_interface
    xknx.group_address_dpt.set({GroupAddress("1/2/3"): {"main": 5}})
    telegram_callback = Mock()
    xknx.telegram_queue.register_telegram_received_cb(telegram_callback)

    telegram = Telegram(
        destination_address=GroupAddress("1/2/3"),
        direction=TelegramDirection.INCOMING,
        payload=apci.GroupValueWrite(DPTArray((0x01, 0x02))),  # wrong payload size
    )
    async with xknx:
        xknx.telegrams.put_nowait(telegram)
        await xknx.telegrams.join()
        assert telegram_callback.call_count == 1
        test_telegram = telegram_callback.call_args[0][0]
        assert test_telegram.decoded_data is None
        assert logger_warning_mock.call_count == 1
        assert "DPT decoding error" in logger_warning_mock.call_args[0][0]


def test_set(xknx_no_interface: XKNX) -> None:
    """Test set."""
    xknx = xknx_no_interface
    xknx.group_address_dpt.set(
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
    assert xknx.group_address_dpt.get(GroupAddress("0/0/1")) is DPTTemperature


@patch("logging.Logger.warning")
@patch("logging.Logger.debug")
def test_set_invalid(
    logger_debug_mock: Mock, logger_warning_mock: Mock, xknx_no_interface: XKNX
) -> None:
    """Test set invalid dpts."""
    xknx = xknx_no_interface
    xknx.group_address_dpt.set(
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


def test_clear(xknx_no_interface: XKNX) -> None:
    """Test clear."""
    xknx = xknx_no_interface
    xknx.group_address_dpt.set(
        {
            GroupAddress("1/2/3"): {"main": 5, "sub": 1},
            1: "temperature",
        }
    )
    assert len(xknx.group_address_dpt._ga_dpts) == 2
    xknx.group_address_dpt.clear()
    assert len(xknx.group_address_dpt._ga_dpts) == 0
