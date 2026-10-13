"""DMP_DownloadLoadablePart_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.4."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from functools import partial

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceGenericPropertyId

from ._state_machine import check_event_size, check_load_poll_interval, poll_for_state
from .dmp_load_state_machine_write_r_co_io import dmp_load_state_machine_write_r_co_io
from .load_state import (
    LoadState,
    decode_load_state,
    load_completed,
    start_loading,
    unload,
)

__all__ = ["dmp_download_loadable_part_r_co_io"]

# KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.4.1: "Retry read
# Property for 30 Seconds"; KNX v01.10.01 - Resources 03.05.01 - §4.23.2.1
# gives the same 30 seconds as the minimum wait for any transition, which
# covers polling through LoadCompleting after Load Completed.
_DEFAULT_POLL_TIMEOUT = 30.0
_DEFAULT_POLL_INTERVAL = 1.0

# First octet of an Additional Load Controls event (KNX v01.10.01 -
# Resources 03.05.01 - §4.23.2.3.2, Table 93; MP §3.31.4 "data = 03 … …").
_ADDITIONAL_LOAD_CONTROLS = 0x03


async def dmp_download_loadable_part_r_co_io(
    conn: P2PConnection,
    object_index: int,
    load_data: Callable[[], Awaitable[None]],
    *,
    additional_load_controls: Sequence[bytes] = (),
    unload_first: bool = True,
    poll_timeout: float = _DEFAULT_POLL_TIMEOUT,
    poll_interval: float = _DEFAULT_POLL_INTERVAL,
) -> None:
    """
    Download one loadable part into an interface object.

    DMP_DownloadLoadablePart_RCo_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.31.4. Requires an established connection (DM_Connect must
    be executed first). Drives the interface object's Load State Machine
    through the single-part download sequence of §3.31.4, built from
    :func:`~.dmp_load_state_machine_write_r_co_io.dmp_load_state_machine_write_r_co_io`
    and the load event builders in
    :mod:`xknx.management.procedures.device.load_state`:

    1. ``unload()`` - optional ("This part is optional"), skipped with
       ``unload_first=False``. If the response is ``LoadState.UNLOADING``
       the state is re-read, for up to ``poll_timeout`` (the spec's "Retry
       read Property for 30 Seconds"), while it stays UNLOADING; the
       download continues once it is ``LoadState.UNLOADED`` and breaks with
       an error on any other state, as the spec's step table says.
    2. ``start_loading()`` - the response must be ``LoadState.LOADING``.
    3. Each event in ``additional_load_controls``, in order (segment/task
       allocation events built with :func:`~.load_state.alloc_abs_data_seg`
       and siblings) - the response must stay ``LoadState.LOADING`` after
       every one. Empty by default; not every device needs them. Every
       event must be an Additional Load Controls event (first octet 03h);
       this is checked before anything is sent.
    4. ``load_data()`` - the actual loadable part data. The spec leaves the
       transport for this step open ("via Property access or memory
       access"), so it isn't one of the fixed load events and isn't
       prescribed here either: pass a callback that writes the data however
       this device expects it - typically
       :func:`~.dmp_interface_object_write_r.dmp_interface_object_write_r`
       or :func:`~.dmp_mem_write_r_co.dmp_mem_write_r_co` against the
       already-open ``conn``.
    5. ``load_completed()`` - the response must be ``LoadState.LOADED``, or
       ``LoadState.LOAD_COMPLETING``: a device whose transition takes more
       than 2 seconds (e.g. a checksum) reports that first, and the client
       "shall control the load state by repeated reading" (KNX v01.10.01 -
       Resources 03.05.01 - Table 93, §4.23.2.4.1). It is then re-read
       every ``poll_interval`` (at most 3 seconds, half the TL-timeout) for
       up to ``poll_timeout`` until it is LOADED. §3.31.4's own "if data is
       not equal 01 break with error" predates LoadCompleting; Resources is
       the more specific text. "A device may be offline during state
       LoadCompleting" (NOTE 86) and the client "shall try to re-establish
       the connection periodically" - this procedure works on ``conn`` and
       can't reconnect, so a dropped connection raises and re-establishing
       it is left to the caller.

    Any step failing its own check leaves the Load State Machine wherever
    the device put it - this procedure does not attempt to unload or
    otherwise recover on error ("The general exception handling shall
    apply").

    This is the single-part sequence of §3.31.4. ETS downloads several
    parts interleaved instead - unloading every Load State Machine first,
    then Start Loading and allocation for each, all data, and Load Completed
    for each last - which this procedure can't express; compose
    :func:`~.dmp_load_state_machine_write_r_co_io.dmp_load_state_machine_write_r_co_io`
    and the ``load_state`` builders directly for that.

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param load_data: Awaited after Start Loading and any
        ``additional_load_controls`` succeed, before Load Completed is sent.
        Writes the actual loadable part data using whatever mechanism this
        device's loadable part is mapped to.
    :param additional_load_controls: Additional Load Controls events to
        send, in order, after Start Loading and before ``load_data``
    :param unload_first: Send the optional Unload step first
    :param poll_timeout: Seconds to poll for ``LoadState.UNLOADED`` after
        Unload, and for ``LoadState.LOADED`` after Load Completed
    :param poll_interval: Seconds to wait between polls, more than 0 and at
        most 3
    :raises ValueError: If an ``additional_load_controls`` event isn't a 10
        octet Additional Load Controls event, or ``poll_interval`` is
        outside (0, 3]
    :raises ManagementConnectionError: If a polled step doesn't reach its
        state within ``poll_timeout``, or any step's response doesn't carry
        the state the spec mandates for it
    """
    for event_data in additional_load_controls:
        check_event_size(event_data)
        if event_data[0] != _ADDITIONAL_LOAD_CONTROLS:
            raise ValueError(
                "additional_load_controls must only contain Additional Load "
                f"Controls events (first octet 03h), got {event_data[0]:02X}h"
            )
    check_load_poll_interval(poll_interval)

    async def step(
        event_data: bytes,
        expected: LoadState,
        name: str,
        transient: LoadState | None = None,
    ) -> None:
        state = await dmp_load_state_machine_write_r_co_io(
            conn, object_index, event_data
        )
        if transient is not None and state == transient:
            context = f"object {object_index}"
            state = await poll_for_state(
                conn,
                object_index,
                ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
                partial(decode_load_state, context=context),
                expected=frozenset([expected]),
                state=state,
                poll_timeout=poll_timeout,
                poll_interval=poll_interval,
                error_state=None,
                context=context,
                machine="Load State Machine",
                transient=frozenset([transient]),
            )
        if state != expected:
            raise ManagementConnectionError(
                f"object {object_index} Load State Machine {name} failed: "
                f"expected {expected.name}, got {state.name}"
            )

    if unload_first:
        await step(unload(), LoadState.UNLOADED, "Unload", LoadState.UNLOADING)
    await step(start_loading(), LoadState.LOADING, "Start Loading")
    for event_data in additional_load_controls:
        await step(event_data, LoadState.LOADING, "Additional Load Control")

    await load_data()

    await step(
        load_completed(), LoadState.LOADED, "Load Completed", LoadState.LOAD_COMPLETING
    )
