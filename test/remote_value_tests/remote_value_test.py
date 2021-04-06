"""Unit test for RemoveValue objects."""
from unittest.mock import AsyncMock, patch

import pytest
from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.remote_value import RemoteValue, RemoteValueSwitch
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


@pytest.mark.asyncio
@patch.multiple(RemoteValue, __abstractmethods__=set())
class TestRemoteValue:
    """Test class for RemoteValue objects."""

    async def test_info_set_uninitialized(self):
        """Test for info if RemoteValue is not initialized."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch("logging.Logger.info") as mock_info:
            await remote_value.set(23)
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
        with patch("logging.Logger.warning") as mock_info:
            await remote_value.set(23)
            mock_info.assert_called_with(
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

    async def test_process_unsupported_payload(self):
        """Test if exception is raised when processing telegram with unsupported payload."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch("xknx.remote_value.RemoteValue.payload_valid") as patch_valid, patch(
            "xknx.remote_value.RemoteValue.has_group_address"
        ) as patch_has_group_address:
            patch_valid.return_value = False
            patch_has_group_address.return_value = True

            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"), payload=object()
            )
            with pytest.raises(
                CouldNotParseTelegram,
                match=r".*payload not a GroupValueWrite or GroupValueResponse.*",
            ):
                await remote_value.process(telegram)

    async def test_process_invalid_payload(self):
        """Test if exception is raised when processing telegram with invalid payload."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx)
        with patch("xknx.remote_value.RemoteValue.payload_valid") as patch_valid, patch(
            "xknx.remote_value.RemoteValue.has_group_address"
        ) as patch_has_group_address:
            patch_valid.return_value = None
            patch_has_group_address.return_value = True

            telegram = Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTArray((0x01, 0x02))),
            )
            with pytest.raises(CouldNotParseTelegram, match=r".*payload invalid.*"):
                await remote_value.process(telegram)

    async def test_read_state(self):
        """Test read state while waiting for the result."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, group_address_state="1/2/3")

        with patch("xknx.remote_value.RemoteValue.payload_valid") as patch_valid, patch(
            "xknx.core.ValueReader.read", new_callable=AsyncMock
        ) as patch_read:
            patch_valid.return_value = True
            telegram = Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTBinary(1)),
            )
            patch_read.return_value = telegram

            await remote_value.read_state(wait_for_result=True)

            assert remote_value.telegram == telegram
            assert remote_value.value

    async def test_read_state_none(self):
        """Test read state while waiting for the result but got None."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, group_address_state="1/2/3")

        with patch("xknx.remote_value.RemoteValue.payload_valid") as patch_valid, patch(
            "xknx.core.ValueReader.read", new_callable=AsyncMock
        ) as patch_read, patch("logging.Logger.warning") as mock_info:
            patch_valid.return_value = False
            patch_read.return_value = None

            await remote_value.read_state(wait_for_result=True)
            mock_info.assert_called_with(
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
        assert not remote_value_3.has_group_address(GroupAddress("0/0/0"))

    async def test_process_passive_address(self):
        """Test if passive group addresses are processed."""
        xknx = XKNX()
        remote_value = RemoteValue(xknx, group_address=["1/2/3", "1/1/1"])
        assert remote_value.writable
        assert not remote_value.readable
        # RemoteValue is initialized with only passive group address
        assert remote_value.initialized
        with patch("xknx.remote_value.RemoteValue.payload_valid") as patch_always_valid:
            patch_always_valid.side_effect = lambda payload: payload
            test_payload = DPTArray((0x01, 0x02))
            telegram = Telegram(
                destination_address=GroupAddress("1/1/1"),
                payload=GroupValueWrite(test_payload),
            )
            assert await remote_value.process(telegram)
            assert remote_value.telegram.payload.value == test_payload

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
