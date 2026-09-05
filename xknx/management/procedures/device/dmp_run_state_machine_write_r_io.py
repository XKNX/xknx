"""DMP_RunStateMachineWrite_R_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.34.3."""

from __future__ import annotations

import asyncio
import time

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceGenericPropertyId

from .dmp_interface_object_read_r import dmp_interface_object_read_r
from .dmp_interface_object_write_r import dmp_interface_object_write_r
from .run_state import RUN_EVENT_SIZE, RunState, decode_run_state

__all__ = ["dmp_run_state_machine_write_r_io"]

# KNX v01.10.01 - Resources 03.05.01 - §4.24.2.1: "The transitions between
# the states shall be less than 30 seconds." Unlike the Load State Machine's
# own §4.23.2.1, this isn't framed as a minimum client wait, but the same
# bound is the only one the spec gives for how long a transition may take.
_DEFAULT_POLL_TIMEOUT = 30.0
_DEFAULT_POLL_INTERVAL = 1.0


async def dmp_run_state_machine_write_r_io(
    conn: P2PConnection,
    object_index: int,
    event_data: bytes,
    *,
    expected_state: RunState | None = None,
    poll_timeout: float = _DEFAULT_POLL_TIMEOUT,
    poll_interval: float = _DEFAULT_POLL_INTERVAL,
) -> RunState:
    """
    Write a run event to an interface object's Run State Machine.

    DMP_RunStateMachineWrite_R_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.34.3. Requires an established connection (DM_Connect must
    be executed first). ``event_data`` is the 10 octet run event (see
    :mod:`xknx.management.procedures.device.run_state` for builders such as
    :func:`~.run_state.restart` or :func:`~.run_state.stop`).

    The property carrying the Run State Machine (``PID_RUN_STATE_CONTROL``)
    is always known by definition here, so the spec's optional
    ``A_PropertyDescription_Read`` step - "if Property... is unknown to the
    Management Client" - never applies, matching
    :func:`~.dmp_load_state_machine_write_r_co_io.dmp_load_state_machine_write_r_co_io`'s
    own reasoning for the same step.

    The write's own response already carries the resulting Run State (the
    spec's sequence: ``A_PropertyValue_Response-PDU (..., data = runstate)``),
    which is returned when ``expected_state`` is not given. When it is given,
    this additionally polls (re-reading the property) until the state
    matches or ``poll_timeout`` elapses - covering the optional intermediate
    ``STARTING``/``SHUTTING_DOWN`` states a device may report while starting
    up or shutting down (KNX v01.10.01 - Resources 03.05.01 - §4.24.2.3.1,
    Table 95), the Pythonic equivalent of DM_RunStateMachineWrite's own
    "verify the resulting state" flag bit (KNX v02.01.02 - Management
    Procedures 03.05.02 - §3.34.1).

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param event_data: The 10 octet run event
    :param expected_state: If given, poll until the Run State Machine
        reaches this state (or ``poll_timeout`` elapses)
    :param poll_timeout: Seconds to poll for ``expected_state`` before giving
        up
    :param poll_interval: Seconds to wait between polls
    :return: The resulting Run State
    :raises ValueError: If ``event_data`` is not exactly 10 octets
    :raises ManagementConnectionError: If the Run State Machine does not
        reach ``expected_state`` within ``poll_timeout``
    """
    if len(event_data) != RUN_EVENT_SIZE:
        raise ValueError(
            f"event_data must be {RUN_EVENT_SIZE} octets, got {len(event_data)}"
        )
    response = await dmp_interface_object_write_r(
        conn,
        object_index,
        ResourceGenericPropertyId.PID_RUN_STATE_CONTROL,
        event_data,
        count=1,
        start_index=1,
    )
    state = decode_run_state(response, f"object {object_index}")
    if expected_state is None or state == expected_state:
        return state
    return await _poll_for_state(
        conn, object_index, expected_state, poll_timeout, poll_interval, state
    )


async def _poll_for_state(
    conn: P2PConnection,
    object_index: int,
    expected_state: RunState,
    poll_timeout: float,
    poll_interval: float,
    state: RunState,
) -> RunState:
    """Re-read the Run State until it matches ``expected_state`` or times out."""
    deadline = time.monotonic() + poll_timeout
    while state != expected_state:
        if time.monotonic() >= deadline:
            raise ManagementConnectionError(
                f"object {object_index} Run State Machine did not reach "
                f"{expected_state.name} within {poll_timeout}s, "
                f"last state {state.name}"
            )
        await asyncio.sleep(poll_interval)
        data = await dmp_interface_object_read_r(
            conn,
            object_index,
            ResourceGenericPropertyId.PID_RUN_STATE_CONTROL,
            count=1,
            start_index=1,
        )
        state = decode_run_state(data, f"object {object_index}")
    return state
