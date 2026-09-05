"""DMP_DownloadLoadablePart_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.4."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection

from .dmp_load_state_machine_write_r_co_io import dmp_load_state_machine_write_r_co_io
from .load_state import LoadState, load_completed, start_loading, unload

__all__ = ["dmp_download_loadable_part_r_co_io"]

# KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.4.1: "Retry read
# Property for 30 Seconds" - the only step of this procedure the spec has
# poll/retry semantics for. Same defaults as
# dmp_load_state_machine_write_r_co_io's own expected_state polling.
_DEFAULT_UNLOAD_POLL_TIMEOUT = 30.0
_DEFAULT_UNLOAD_POLL_INTERVAL = 1.0


async def dmp_download_loadable_part_r_co_io(
    conn: P2PConnection,
    object_index: int,
    load_data: Callable[[], Awaitable[None]],
    *,
    additional_load_controls: Sequence[bytes] = (),
    unload_poll_timeout: float = _DEFAULT_UNLOAD_POLL_TIMEOUT,
    unload_poll_interval: float = _DEFAULT_UNLOAD_POLL_INTERVAL,
) -> None:
    """
    Download one loadable part into an interface object.

    DMP_DownloadLoadablePart_RCo_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.31.4. Requires an established connection (DM_Connect must
    be executed first). Drives the interface object's Load State Machine
    through its full download sequence, built entirely from
    :func:`~.dmp_load_state_machine_write_r_co_io.dmp_load_state_machine_write_r_co_io`
    and the load event builders in
    :mod:`xknx.management.procedures.device.load_state`:

    1. ``unload()`` - polled up to ``unload_poll_timeout`` (30 seconds by
       default, the spec's own "Retry read Property for 30 Seconds") until
       the Load State Machine reaches ``LoadState.UNLOADED``. This is the
       only step the spec describes with retry/poll semantics; every step
       below checks the write's own immediate response once and raises
       rather than retrying.
    2. ``start_loading()`` - the response must be ``LoadState.LOADING``.
    3. Each event in ``additional_load_controls``, in order (segment/task
       allocation events built with :func:`~.load_state.alloc_abs_data_seg`
       and siblings) - the response must stay ``LoadState.LOADING`` after
       every one. Empty by default; not every device needs them.
    4. ``load_data()`` - the actual loadable part data. The spec leaves the
       transport for this step open ("via Property access or memory
       access"), so it isn't one of the fixed load events and isn't
       prescribed here either: pass a callback that writes the data however
       this device expects it - typically
       :func:`~.dmp_interface_object_write_r.dmp_interface_object_write_r`
       or :func:`~.dmp_mem_write_r_co.dmp_mem_write_r_co` against the
       already-open ``conn``.
    5. ``load_completed()`` - the response must be ``LoadState.LOADED``.

    Any step failing its own check leaves the Load State Machine wherever
    the device put it - this procedure does not attempt to unload or
    otherwise recover on error, matching the spec's own "break with error"
    for every step but the first.

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param load_data: Awaited after Start Loading and any
        ``additional_load_controls`` succeed, before Load Completed is sent.
        Writes the actual loadable part data using whatever mechanism this
        device's loadable part is mapped to.
    :param additional_load_controls: Segment/task allocation events to send,
        in order, after Start Loading and before ``load_data``
    :param unload_poll_timeout: Seconds to poll for ``LoadState.UNLOADED``
        after the Unload event before giving up
    :param unload_poll_interval: Seconds to wait between polls
    :raises ManagementConnectionError: If Unload does not reach
        ``LoadState.UNLOADED`` within ``unload_poll_timeout``, or any other
        step's response doesn't carry the state the spec mandates for it
    """
    await dmp_load_state_machine_write_r_co_io(
        conn,
        object_index,
        unload(),
        expected_state=LoadState.UNLOADED,
        poll_timeout=unload_poll_timeout,
        poll_interval=unload_poll_interval,
    )

    await _write_and_expect(
        conn, object_index, start_loading(), LoadState.LOADING, "Start Loading"
    )
    for event_data in additional_load_controls:
        await _write_and_expect(
            conn, object_index, event_data, LoadState.LOADING, "Additional Load Control"
        )

    await load_data()

    await _write_and_expect(
        conn, object_index, load_completed(), LoadState.LOADED, "Load Completed"
    )


async def _write_and_expect(
    conn: P2PConnection,
    object_index: int,
    event_data: bytes,
    expected_state: LoadState,
    step_name: str,
) -> None:
    """Write a load event and raise unless the immediate response matches expected_state."""
    state = await dmp_load_state_machine_write_r_co_io(conn, object_index, event_data)
    if state != expected_state:
        raise ManagementConnectionError(
            f"object {object_index} Load State Machine {step_name} failed: "
            f"expected {expected_state.name}, got {state.name}"
        )
