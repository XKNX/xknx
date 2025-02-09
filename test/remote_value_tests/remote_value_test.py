"""Unit test for RemoveValue objects."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from xknx import XKNX
from xknx.dpt import DPT2ByteFloat, DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValue, RemoteValueSwitch
from xknx.telegram import GroupAddress, Telegram, TelegramDecodedData
from xknx.telegram.apci import GroupValueWrite


@patch.multiple(RemoteValue, __abstractmethods__=set())
class TestRemoteValue:
    """Test class for RemoteValue objects."""

    async def test_get_set_value(self):
        """Test value getter and setter."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        remote_value.to_knx = DPT2ByteFloat.to_knx
        remote_value.after_update_cb = Mock()

        assert remote_value.value is None
        remote_value.value = 2.2
        assert remote_value.value == 2.2
        # invalid value raises ConversionError
        with pytest.raises(ConversionError):
            remote_value.value = "a"
        # new value is used in response Telegram
        test_payload = remote_value.to_knx(2.2)
        remote_value._send = Mock()
        remote_value.respond()
        remote_value._send.assert_called_with(test_payload, response=True)
        # callback is not called when setting value programmatically
        remote_value.after_update_cb.assert_not_called()
        # no Telegram was sent to the queue
        assert xknx.telegrams.qsize() == 0

    def test_set_value(self):
        """Test set_value awaitable."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        remote_value.to_knx = DPT2ByteFloat.to_knx
        remote_value.after_update_cb = Mock()

        remote_value.update_value(3.3)
        assert remote_value.value == 3.3
        remote_value.after_update_cb.assert_called_once()
        assert xknx.telegrams.qsize() == 0
        # invalid value raises ConversionError
        with pytest.raises(ConversionError):
            remote_value.update_value("a")
        assert remote_value.value == 3.3

    async def test_info_set_uninitialized(self):
        """Test for info if RemoteValue is not initialized."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch("logging.Logger.info") as mock_info:
            remote_value.set(23)
            mock_info.assert_called_with(
                "Setting value of uninitialized device: %s - %s (value: %s)",
                "Unknown",
                "Unknown",
                23,
            )

    async def test_info_set_unwritable(self):
        """Test for warning if RemoteValue is read only."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx, group_address_state=GroupAddress("1/2/3"))
        with patch("logging.Logger.warning") as mock_warning:
            remote_value.set(23)
            mock_warning.assert_called_with(
                "Attempted to set value for non-writable device: %s - %s (value: %s)",
                "Unknown",
                "Unknown",
                23,
            )

    def test_default_value_unit(self):
        """Test for the default value of unit_of_measurement."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        assert remote_value.unit_of_measurement is None

    async def test_process_unsupported_payload_type(self):
        """Test if exception is raised when processing telegram with unsupported payload type."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch(
            "xknx.remote_value.RemoteValue.has_group_address"
        ) as patch_has_group_address:
            patch_has_group_address.return_value = True

            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"), payload=object()
            )
            with pytest.raises(
                CouldNotParseTelegram,
                match=r".*payload not a GroupValueWrite or GroupValueResponse.*",
            ):
                remote_value.process(telegram)

    def test_process_unsupported_payload(self):
        """Test warning is logged when processing telegram with unsupported payload."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        telegram = Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTArray((0x01, 0x02))),
        )
        with (
            patch(
                "xknx.remote_value.RemoteValue.has_group_address"
            ) as patch_has_group_address,
            patch("xknx.remote_value.RemoteValue.from_knx") as patch_from,
            patch("logging.Logger.warning") as mock_warning,
        ):
            patch_has_group_address.return_value = True
            patch_from.side_effect = ConversionError("TestError")

            assert remote_value.process(telegram) is False
            mock_warning.assert_called_once_with(
                "Can not process %s for %s - %s: %s",
                telegram,
                "Unknown",
                "Unknown",
                ConversionError("TestError"),
            )

    async def test_read_state(self):
        """Test read state while waiting for the result."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, group_address_state="1/2/3")

        with patch("xknx.core.ValueReader.read", new_callable=AsyncMock) as patch_read:
            telegram = Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTBinary(1)),
            )
            patch_read.return_value = telegram

            await remote_value.read_state(wait_for_result=True)
            patch_read.assert_called_once()
            # RemoteValue.value is updated by RemoteValue.process called from Device / TelegramQueue

    async def test_read_state_none(self):
        """Test read state while waiting for the result but got None."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, group_address_state="1/2/3")

        with (
            patch("xknx.core.ValueReader.read", new_callable=AsyncMock) as patch_read,
            patch("logging.Logger.warning") as mock_warning,
        ):
            patch_read.return_value = None

            await remote_value.read_state(wait_for_result=True)
            patch_read.assert_called_once()
            mock_warning.assert_called_once_with(
                "Could not sync group address '%s' (%s - %s)",
                GroupAddress("1/2/3"),
                "Unknown",
                "State",
            )

    def test_unpacking_passive_address(self):
        """Test if passive group addresses are properly unpacked."""
        xknx = XKNX()

        remote_value_1 = RemoteValue(xknx, group_address=["1/2/3", "1/1/1"])
        assert remote_value_1.group_address == GroupAddress("1/2/3")
        assert remote_value_1.group_address_state is None
        assert remote_value_1.passive_group_addresses == [GroupAddress("1/1/1")]
        assert remote_value_1.has_group_address(GroupAddress("1/2/3"))
        assert remote_value_1.has_group_address(GroupAddress("1/1/1"))

        remote_value_2 = RemoteValue(xknx, group_address_state=["1/2/3", "1/1/1"])
        assert remote_value_2.group_address is None
        assert remote_value_2.group_address_state == GroupAddress("1/2/3")
        assert remote_value_2.passive_group_addresses == [GroupAddress("1/1/1")]
        assert remote_value_2.has_group_address(GroupAddress("1/2/3"))
        assert remote_value_2.has_group_address(GroupAddress("1/1/1"))

        remote_value_3 = RemoteValue(
            xknx,
            group_address=["1/2/3", "1/1/1", "1/1/10"],
            group_address_state=["2/3/4", "2/2/2", "2/2/20"],
        )
        assert remote_value_3.group_address == GroupAddress("1/2/3")
        assert remote_value_3.group_address_state == GroupAddress("2/3/4")
        assert remote_value_3.passive_group_addresses == [
            GroupAddress("1/1/1"),
            GroupAddress("1/1/10"),
            GroupAddress("2/2/2"),
            GroupAddress("2/2/20"),
        ]
        assert remote_value_3.has_group_address(GroupAddress("1/2/3"))
        assert remote_value_3.has_group_address(GroupAddress("1/1/1"))
        assert remote_value_3.has_group_address(GroupAddress("1/1/10"))
        assert remote_value_3.has_group_address(GroupAddress("2/3/4"))
        assert remote_value_3.has_group_address(GroupAddress("2/2/2"))
        assert remote_value_3.has_group_address(GroupAddress("2/2/20"))
        assert not remote_value_3.has_group_address(GroupAddress("0/0/1"))
        # test empty list
        remote_value_4 = RemoteValue(xknx, group_address=[])
        assert remote_value_4.group_address is None
        # test None in list
        remote_value_5 = RemoteValue(
            xknx,
            group_address=["1/2/3", "1/1/1", "1/1/10"],
            group_address_state=[None, "2/2/2", "2/2/20"],
        )
        assert remote_value_5.group_address == GroupAddress("1/2/3")
        assert remote_value_5.group_address_state is None
        assert remote_value_5.passive_group_addresses == [
            GroupAddress("1/1/1"),
            GroupAddress("1/1/10"),
            GroupAddress("2/2/2"),
            GroupAddress("2/2/20"),
        ]
        remote_value_6 = RemoteValue(
            xknx,
            group_address=None,
            group_address_state=["1/1/1", None, "2/2/2", "2/2/20"],
        )
        assert remote_value_6.group_address is None
        assert remote_value_6.group_address_state == GroupAddress("1/1/1")
        assert remote_value_6.passive_group_addresses == [
            GroupAddress("2/2/2"),
            GroupAddress("2/2/20"),
        ]

    def test_process_passive_address(self):
        """Test if passive group addresses are processed."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx, group_address=["1/2/3", "1/1/1"])
        remote_value.dpt_class = DPT2ByteFloat

        assert remote_value.writable
        assert not remote_value.readable
        # RemoteValue is initialized with only passive group address
        assert remote_value.initialized

        test_payload = DPTArray((0x01, 0x02))
        telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            payload=GroupValueWrite(test_payload),
        )
        assert remote_value.process(telegram)
        assert remote_value.telegram.payload.value == test_payload

    def test_to_from_knx(self):
        """Test to_knx and from_knx raises when not set properly."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx, group_address="1/1/1")
        with pytest.raises(NotImplementedError):
            remote_value.value = 3.3  # without to_knx method

        test_payload = DPTArray((0x01, 0x02))
        telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            payload=GroupValueWrite(test_payload),
        )
        with pytest.raises(NotImplementedError):
            remote_value.process(telegram)

        # doesn't raise with `dpt_class` set
        remote_value.dpt_class = DPT2ByteFloat
        remote_value.value = 3.3
        remote_value.process(telegram)

    def test_pre_decoded_telegram(self):
        """Test if pre-decoded Telegram is processed."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx, group_address="1/1/1")
        remote_value.dpt_class = DPT2ByteFloat

        test_payload = "invalid for testing"
        telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            payload=GroupValueWrite(test_payload),
            decoded_data=TelegramDecodedData(transcoder=DPT2ByteFloat, value=3.3),
        )
        assert remote_value.process(telegram)
        assert remote_value.value == 3.3

    def test_eq(self):
        """Test __eq__ operator."""
        xknx = XKNX()
        remote_value1 = RemoteValue(xknx, group_address=GroupAddress("1/1/1"))
        remote_value2 = RemoteValue(xknx, group_address=GroupAddress("1/1/1"))
        remote_value3 = RemoteValue(xknx, group_address=GroupAddress("1/1/2"))
        remote_value4 = RemoteValue(xknx, group_address=GroupAddress("1/1/1"))
        remote_value4.fnord = "fnord"

        def _callback():
            pass

        remote_value5 = RemoteValue(
            xknx, group_address=GroupAddress("1/1/1"), after_update_cb=_callback()
        )

        assert remote_value1 == remote_value2
        assert remote_value2 == remote_value1
        assert remote_value1 != remote_value3
        assert remote_value3 != remote_value1
        assert remote_value1 != remote_value4
        assert remote_value4 != remote_value1
        assert remote_value1 == remote_value5
        assert remote_value5 == remote_value1
