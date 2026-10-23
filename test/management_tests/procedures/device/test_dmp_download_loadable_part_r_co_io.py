"""Tests for dmp_download_loadable_part_r_co_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.4."""

from functools import partial
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import VerificationError
from xknx.management.procedures.device.dmp_download_loadable_part_r_co_io import (
    dmp_download_loadable_part_r_co_io,
)
from xknx.management.procedures.device.dmp_load_state_machine_write_r_co_io import (
    load_event_relative_allocation,
)
from xknx.management.procedures.device.dmp_mem_write_r_co import dmp_mem_write_r_co
from xknx.telegram import apci

from .load_state_machine_helpers import (
    connect,
    property_read,
    property_response,
    property_write,
    sent_requests,
)


@pytest.fixture(name="xknx")
def fixture_xknx() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


async def test_dmp_download_loadable_part_r_co_io(xknx: XKNX) -> None:
    """Test the complete download sequence of one loadable part."""
    conn = await connect(
        xknx,
        [
            property_response(b"\x00"),  # Unload -> Unloaded
            property_response(b"\x02"),  # Start Loading -> Loading
            property_response(b"\x02"),  # Additional Load Control -> Loading
            None,  # data written by `load`
            property_response(b"\x01"),  # Load Completed -> Loaded
        ],
    )
    await dmp_download_loadable_part_r_co_io(
        conn,
        3,
        partial(dmp_mem_write_r_co, address=0x4000, data=b"\x01\x02"),
        additional_load_controls=[load_event_relative_allocation(0x20)],
    )
    assert sent_requests(xknx) == [
        property_write(0x04),
        property_write(0x01),
        property_write(0x03, b"\x0a\x00\x20"),
        apci.MemoryWrite(address=0x4000, data=b"\x01\x02"),
        property_write(0x02),
    ]


async def test_dmp_download_loadable_part_r_co_io_intermediate_states(
    xknx: XKNX,
) -> None:
    """Test that Unloading and LoadCompleting are read again until they end."""
    conn = await connect(
        xknx,
        [
            property_response(b"\x04"),  # Unload -> Unloading
            property_response(b"\x00"),  # read -> Unloaded
            property_response(b"\x02"),  # Start Loading -> Loading
            property_response(b"\x05"),  # Load Completed -> LoadCompleting
            property_response(b"\x01"),  # read -> Loaded
        ],
    )
    load = AsyncMock()
    await dmp_download_loadable_part_r_co_io(conn, 3, load, poll_interval=0)
    load.assert_awaited_once_with(conn)
    assert sent_requests(xknx) == [
        property_write(0x04),
        property_read(),
        property_write(0x01),
        property_write(0x02),
        property_read(),
    ]


async def test_dmp_download_loadable_part_r_co_io_property_id(xknx: XKNX) -> None:
    """Test that every step uses the given Property."""
    conn = await connect(xknx, [property_response(b"\x02"), property_response(b"\x01")])
    await dmp_download_loadable_part_r_co_io(
        conn, 3, AsyncMock(), unload=False, property_id=60
    )
    assert [request.property_id for request in sent_requests(xknx)] == [60, 60]


async def test_dmp_download_loadable_part_r_co_io_without_unload(xknx: XKNX) -> None:
    """Test that the Unload step is optional."""
    conn = await connect(xknx, [property_response(b"\x02"), property_response(b"\x01")])
    await dmp_download_loadable_part_r_co_io(conn, 3, AsyncMock(), unload=False)
    assert sent_requests(xknx) == [property_write(0x01), property_write(0x02)]


async def test_dmp_download_loadable_part_r_co_io_stops_on_wrong_state(
    xknx: XKNX,
) -> None:
    """Test that a step not leading to the expected state stops the download."""
    conn = await connect(xknx, [property_response(b"\x00"), property_response(b"\x03")])
    load = AsyncMock()
    with pytest.raises(VerificationError):
        await dmp_download_loadable_part_r_co_io(conn, 3, load)
    load.assert_not_awaited()


@pytest.mark.parametrize(
    ("additional_load_controls", "poll_interval"),
    [([bytes(10)], 1.0), ([], 3.1)],
)
async def test_dmp_download_loadable_part_r_co_io_invalid(
    xknx: XKNX, additional_load_controls: list[bytes], poll_interval: float
) -> None:
    """Test that a too long load control or poll interval is rejected first."""
    conn = await connect(xknx, [])
    with pytest.raises(ValueError):
        await dmp_download_loadable_part_r_co_io(
            conn,
            3,
            AsyncMock(),
            additional_load_controls=additional_load_controls,
            poll_interval=poll_interval,
        )
    assert sent_requests(xknx) == []
