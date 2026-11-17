"""Helpers shared by the DM_LoadStateMachine* procedures."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.profile.const import LoadEvent, LoadState, ResourceObjectType

from .const import LOAD_CONTROL_LENGTH, LOAD_STATE_MAX_POLL_INTERVAL

# State reached after a successful event - KNX v01.10.01 - Resources 03.05.01 -
# §4.23.2.3.3, Table 94. No Operation leaves the state unchanged.
EXPECTED_STATE = {
    LoadEvent.START_LOADING: LoadState.LOADING,
    LoadEvent.LOAD_COMPLETED: LoadState.LOADED,
    LoadEvent.ADDITIONAL_LOAD_CONTROLS: LoadState.LOADING,
    LoadEvent.UNLOAD: LoadState.UNLOADED,
}
# Optional intermediate states a Load State Machine may report on the way to
# the final one - KNX v01.10.01 - Resources 03.05.01 - §4.23.2.3.3, Table 94.
# A device still in LoadCompleting may answer any event with LoadCompleting and
# ignore it; Unload may also pass through Unloading.
INTERMEDIATE_STATES = {
    LoadEvent.START_LOADING: frozenset({LoadState.LOAD_COMPLETING}),
    LoadEvent.LOAD_COMPLETED: frozenset({LoadState.LOAD_COMPLETING}),
    LoadEvent.ADDITIONAL_LOAD_CONTROLS: frozenset({LoadState.LOAD_COMPLETING}),
    LoadEvent.UNLOAD: frozenset({LoadState.UNLOADING, LoadState.LOAD_COMPLETING}),
}

# Fixed address of the load state of each memory mapped Load State Machine of
# mask version 070nh (BIM M112) - KNX v02.01.02 - Management Procedures
# 03.05.02 - §3.31.2, §3.32.2 and §3.33.2.
MEM_LOAD_STATE_ADDRESS = {
    ResourceObjectType.OBJECT_ADDRESS_TABLE: 0xB6EA,
    ResourceObjectType.OBJECT_ASSOCIATION_TABLE: 0xB6EB,
    ResourceObjectType.OBJECT_APPLICATION_PROGRAM: 0xB6EC,
    ResourceObjectType.OBJECT_INTERFACE_PROGRAM: 0xB6ED,
}


def decode_load_state(data: bytes) -> LoadState:
    """Return the Load State of the first octet of a response."""
    if not data:
        raise ManagementConnectionError("Load State Machine returned no data")
    try:
        return LoadState(data[0])
    except ValueError:
        raise ManagementConnectionError(
            f"Load State Machine returned an unknown state {data[0]:#04x}"
        ) from None


def load_control_data(event: LoadEvent, event_data: bytes) -> bytes:
    """Return the 10 octets of a load control: the event, its data and fill octets."""
    if len(event_data) > LOAD_CONTROL_LENGTH - 1:
        raise ValueError(
            f"event_data must be at most {LOAD_CONTROL_LENGTH - 1} octets, "
            f"got {len(event_data)}"
        )
    return bytes([event]) + event_data.ljust(LOAD_CONTROL_LENGTH - 1, b"\x00")


def check_poll_interval(poll_interval: float) -> None:
    """Raise ValueError if `poll_interval` exceeds the allowed reading period."""
    if poll_interval > LOAD_STATE_MAX_POLL_INTERVAL:
        raise ValueError(
            f"poll_interval must be at most {LOAD_STATE_MAX_POLL_INTERVAL:g} "
            f"seconds, got {poll_interval:g}"
        )


def check_mem_state_machine(state_machine: ResourceObjectType) -> None:
    """Raise ValueError if `state_machine` has no memory mapped Load State Machine."""
    if state_machine not in MEM_LOAD_STATE_ADDRESS:
        raise ValueError(f"No memory mapped Load State Machine for {state_machine!r}")


def check_state(state: LoadState, expected: LoadState) -> None:
    """Raise VerificationError if `state` is not `expected`."""
    if state != expected:
        raise VerificationError(
            f"Load State Machine is in state {state.name}, expected {expected.name}"
        )


async def await_expected_state(
    state: LoadState,
    event: LoadEvent,
    read_state: Callable[[], Awaitable[LoadState]],
    timeout: float,
    poll_interval: float,
) -> LoadState:
    """
    Return the state reached by `event`, reading again while it is intermediate.

    Raises VerificationError if the state is not the expected one for `event`,
    or an intermediate state lasts longer than `timeout` seconds.
    """
    expected = EXPECTED_STATE.get(event)
    if expected is None:
        return state
    intermediate = INTERMEDIATE_STATES[event]
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while state in intermediate:
        if loop.time() >= deadline:
            raise VerificationError(
                f"Load State Machine is still in state {state.name} after the "
                f"{timeout:g} s timeout, expected {expected.name}"
            )
        await asyncio.sleep(poll_interval)
        state = await read_state()
    check_state(state, expected)
    return state
