"""Independent valve feedback regression tests."""

from unittest.mock import Mock

import pytest

from xknx import XKNX
from xknx.devices import Climate
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import DeviceIllegalValue
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


def send(
    climate: Climate, address: str, value: DPTArray | DPTBinary, response: bool = False
) -> None:
    """Deliver a real KNX payload via the device registry."""
    climate.xknx.devices.process(
        Telegram(
            destination_address=GroupAddress(address),
            payload=(GroupValueResponse if response else GroupValueWrite)(value),
        )
    )


@pytest.mark.parametrize("response", [False, True])
@pytest.mark.parametrize(
    "heating,cooling", [(False, False), (True, False), (False, True), (True, True)]
)
async def test_binary_matrix(heating: bool, cooling: bool, response: bool) -> None:
    """Preserve all four combinations without depending on controller mode."""
    xknx = XKNX()
    cb = Mock()
    climate = Climate(
        xknx,
        group_address_heating_active_state="1/1/1",
        group_address_cooling_active_state="1/1/2",
        device_updated_cb=cb,
    )
    xknx.devices.async_add(climate)
    assert climate.has_independent_activity
    assert climate.is_heating is None
    assert climate.is_cooling is None
    assert climate.valve_activity_conflict is None
    send(climate, "1/1/1", DPTBinary(heating), response)
    assert climate.is_heating is heating
    assert climate.is_cooling is None
    send(climate, "1/1/2", DPTBinary(cooling), response)
    assert (climate.is_heating, climate.is_cooling) == (heating, cooling)
    assert climate.valve_activity_conflict is (heating and cooling)
    assert cb.call_count == 2
    assert climate.is_active is None  # legacy API remains independent


@pytest.mark.parametrize(
    "threshold,raw,expected",
    [
        (0, 0, False),
        (0, 1, True),
        (20, 50, False),
        (20, 51, False),
        (20, 52, True),
        (20, 255, True),
    ],
)
async def test_scaling_boundary(threshold: float, raw: int, expected: bool) -> None:
    """Use decoded DPT 5.001 percentages and strict greater-than comparison."""
    xknx = XKNX()
    climate = Climate(
        xknx,
        group_address_heating_command_value_state="1/1/1",
        group_address_cooling_command_value_state="1/1/2",
        heating_activity_threshold=threshold,
        cooling_activity_threshold=99,
    )
    xknx.devices.async_add(climate)
    assert climate.is_heating is None
    send(climate, "1/1/1", DPTArray((raw,)))
    send(climate, "1/1/2", DPTArray((255,)))
    assert climate.is_heating is expected
    assert climate.is_cooling is True


async def test_priority_unknown_and_no_shared_fallback() -> None:
    """A configured binary channel owns its valve, even before initialization."""
    xknx = XKNX()
    climate = Climate(
        xknx,
        group_address_active_state="1/1/5",
        group_address_command_value_state="1/1/6",
        group_address_heating_active_state="1/1/1",
        group_address_heating_command_value_state="1/1/2",
        group_address_cooling_command_value_state="1/1/3",
    )
    xknx.devices.async_add(climate)
    send(climate, "1/1/5", DPTBinary(True))
    send(climate, "1/1/6", DPTArray((255,)))
    send(climate, "1/1/2", DPTArray((255,)))
    assert climate.is_heating is None
    assert climate.is_active is True
    send(climate, "1/1/1", DPTBinary(False))
    assert climate.is_heating is False
    send(climate, "1/1/2", DPTArray((255,)))
    assert climate.is_heating is False
    send(climate, "1/1/1", DPTBinary(True))
    send(climate, "1/1/2", DPTArray((0,)))
    assert climate.is_heating is True


@pytest.mark.parametrize(
    "threshold", [-1, 100, 101, float("nan"), float("inf"), -float("inf"), True]
)
def test_invalid_threshold(threshold: float) -> None:
    """Reject nonfinite, boolean and out-of-range thresholds for direct callers."""
    with pytest.raises(DeviceIllegalValue):
        Climate(XKNX(), heating_activity_threshold=threshold)


@pytest.mark.parametrize(
    "key",
    [
        "group_address_heating_active_state",
        "group_address_cooling_active_state",
        "group_address_heating_command_value_state",
        "group_address_cooling_command_value_state",
    ],
)
def test_incomplete_channels(key: str) -> None:
    """Missing instrumentation must not silently imply an inactive valve."""
    with pytest.raises(DeviceIllegalValue):
        Climate(XKNX(), **{key: "1/1/1"})


async def test_sync_passive_addresses_rename_and_no_writes() -> None:
    """All feedback participates in reads, dispatch, naming and callbacks."""
    xknx = XKNX()
    climate = Climate(
        xknx,
        name="before",
        group_address_heating_active_state=["1/1/1", "1/1/3"],
        group_address_cooling_command_value_state="1/1/2",
    )
    xknx.devices.async_add(climate)
    climate.name = "after"
    assert climate.heating_active.device_name == "after"
    assert climate.cooling_command_value.device_name == "after"
    assert climate.has_group_address(GroupAddress("1/1/3"))
    await climate.sync()
    telegrams = []
    while not xknx.telegrams.empty():
        telegrams.append(xknx.telegrams.get_nowait())
    assert {str(t.destination_address) for t in telegrams} == {"1/1/1", "1/1/2"}
    assert all(isinstance(t.payload, GroupValueRead) for t in telegrams)
    send(climate, "1/1/3", DPTBinary(True))
    assert climate.is_heating is True


def test_legacy_without_new_config() -> None:
    """New API does not manufacture missing activity."""
    climate = Climate(XKNX())
    assert not climate.has_independent_activity
    assert climate.is_heating is None
    assert climate.is_cooling is None
    assert climate.is_active is None


async def test_invalid_payload_does_not_manufacture_inactive() -> None:
    """Ignore malformed feedback without replacing unknown or the last valid value."""
    xknx = XKNX()
    climate = Climate(
        xknx,
        group_address_heating_command_value_state="1/1/1",
        group_address_cooling_active_state="1/1/2",
    )
    xknx.devices.async_add(climate)
    send(climate, "1/1/1", DPTBinary(False))
    assert climate.is_heating is None
    send(climate, "1/1/1", DPTArray((255,)))
    assert climate.is_heating is True
    send(climate, "1/1/1", DPTArray((0, 0)))
    assert climate.is_heating is True
