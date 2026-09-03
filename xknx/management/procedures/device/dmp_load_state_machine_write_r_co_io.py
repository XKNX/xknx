"""DMP_LoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3."""

from __future__ import annotations

import asyncio
import time

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceGenericPropertyId

from .dmp_interface_object_read_r import dmp_interface_object_read_r
from .dmp_interface_object_write_r import dmp_interface_object_write_r
from .load_state import LOAD_EVENT_SIZE, LoadState

__all__ = ["dmp_load_state_machine_write_r_co_io"]

# KNX v01.10.01 - Resources 03.05.01 - §4.23.2.1: "The transitions between
# the states shall be less than 30 seconds. This time shall be the minimum
# delay during which a MaC shall wait after sending a load event until
# interpretation of the load event with the expected state transition to be
# failed."
_DEFAULT_POLL_TIMEOUT = 30.0
_DEFAULT_POLL_INTERVAL = 1.0


async def dmp_load_state_machine_write_r_co_io(
    conn: P2PConnection,
    object_index: int,
    event_data: bytes,
    *,
    expected_state: LoadState | None = None,
    poll_timeout: float = _DEFAULT_POLL_TIMEOUT,
    poll_interval: float = _DEFAULT_POLL_INTERVAL,
) -> LoadState:
    """
    Write a load event to an interface object's Load State Machine.

    DMP_LoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.31.3. Requires an established connection (DM_Connect must
    be executed first). ``event_data`` is the 10 octet load event (see
    :mod:`xknx.management.procedures.device.load_state` for builders such as
    :func:`~.load_state.start_loading` or :func:`~.load_state.alloc_abs_data_seg`).

    The property carrying the Load State Machine (``PID_LOAD_STATE_CONTROL``)
    is always known by definition here, so the spec's optional
    ``A_PropertyDescription_Read`` step - "if Property... is unknown to the
    Management Client" - never applies, matching
    :func:`~.dmp_interface_object_write_r.dmp_interface_object_write_r`'s own
    reasoning for the same step.

    The write's own response already carries the resulting Load State (the
    spec's sequence: ``A_PropertyValue_Response-PDU (..., data = loadstate)``),
    which is returned when ``expected_state`` is not given. When it is given,
    this additionally polls (re-reading the property) until the state matches
    or ``poll_timeout`` elapses - covering both the ``LoadCompleted``
    transition's optional intermediate ``LoadCompleting`` state and DM_Load-
    StateMachineWrite's own "verify resulting state" flag (KNX v01.10.01 -
    Resources 03.05.01 - §4.23.2.3.1 Table 92; KNX v02.01.02 - Management
    Procedures 03.05.02 - §3.31.1). ``poll_timeout`` defaults to 30 seconds,
    the spec's own minimum wait before a state transition may be considered
    failed (§4.23.2.1).

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param event_data: The 10 octet load event
    :param expected_state: If given, poll until the Load State Machine
        reaches this state (or ``LoadState.ERROR``, or ``poll_timeout``
        elapses)
    :param poll_timeout: Seconds to poll for ``expected_state`` before giving
        up
    :param poll_interval: Seconds to wait between polls
    :return: The resulting Load State
    :raises ValueError: If ``event_data`` is not exactly 10 octets
    :raises ManagementConnectionError: If the Load State Machine reaches
        ``LoadState.ERROR``, or does not reach ``expected_state`` within
        ``poll_timeout``
    """
    if len(event_data) != LOAD_EVENT_SIZE:
        raise ValueError(
            f"event_data must be {LOAD_EVENT_SIZE} octets, got {len(event_data)}"
        )
    response = await dmp_interface_object_write_r(
        conn,
        object_index,
        ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
        event_data,
        count=1,
        start_index=1,
    )
    state = _decode(response, object_index)
    if expected_state is None or state == expected_state:
        return state
    return await _poll_for_state(
        conn, object_index, expected_state, poll_timeout, poll_interval, state
    )


async def _poll_for_state(
    conn: P2PConnection,
    object_index: int,
    expected_state: LoadState,
    poll_timeout: float,
    poll_interval: float,
    state: LoadState,
) -> LoadState:
    """Re-read the Load State until it matches ``expected_state`` or times out."""
    deadline = time.monotonic() + poll_timeout
    while state != expected_state:
        if state == LoadState.ERROR:
            raise ManagementConnectionError(
                f"object {object_index} Load State Machine entered ERROR "
                f"(expected {expected_state.name})"
            )
        if time.monotonic() >= deadline:
            raise ManagementConnectionError(
                f"object {object_index} Load State Machine did not reach "
                f"{expected_state.name} within {poll_timeout}s, "
                f"last state {state.name}"
            )
        await asyncio.sleep(poll_interval)
        data = await dmp_interface_object_read_r(
            conn,
            object_index,
            ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
            count=1,
            start_index=1,
        )
        state = _decode(data, object_index)
    return state


def _decode(data: bytes, object_index: int) -> LoadState:
    """Map the Load State octet to :class:`LoadState`, erroring on unknowns."""
    if not data:
        raise ManagementConnectionError(
            f"object {object_index} Load State Machine returned no data"
        )
    try:
        return LoadState(data[0])
    except ValueError as exc:
        raise ManagementConnectionError(
            f"object {object_index} Load State Machine reported unknown "
            f"state {data[0]:#04x}"
        ) from exc
