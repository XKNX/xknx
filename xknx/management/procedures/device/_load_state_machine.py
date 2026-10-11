"""Helpers shared by the DM_LoadStateMachine* procedures."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.profile.const import LoadEvent, LoadState, ResourceObjectType

# The value written to PID_LOAD_STATE_CONTROL is always 10 octets: the event,
# then additional information for it - KNX v01.10.01 - Resources 03.05.01 -
# §4.2.5 and KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3.
LOAD_CONTROL_LENGTH = 10

# State reached after a successful event - KNX v01.10.01 - Resources 03.05.01 -
# §4.23.2.3.3, Table 94. No Operation leaves the state unchanged.
EXPECTED_STATE = {
    LoadEvent.START_LOADING: LoadState.LOADING,
    LoadEvent.LOAD_COMPLETED: LoadState.LOADED,
    LoadEvent.ADDITIONAL_LOAD_CONTROLS: LoadState.LOADING,
    LoadEvent.UNLOAD: LoadState.UNLOADED,
}
# Optional intermediate state a Load State Machine may report on the way to
# the expected one - KNX v01.10.01 - Resources 03.05.01 - §4.23.2.3.2.
INTERMEDIATE_STATE = {
    LoadEvent.LOAD_COMPLETED: LoadState.LOAD_COMPLETING,
    LoadEvent.UNLOAD: LoadState.UNLOADING,
}
# KNX v01.10.01 - Resources 03.05.01 - §4.23.2.1: "The transitions between the
# states shall be less than 30 seconds. This time shall be the minimum delay
# during which a MaC shall wait after sending a load event until
# interpretation of the load event with the expected state transition to be
# failed."
TRANSITION_TIMEOUT = 30.0

# Memory mapped Load State Machines of mask version 070nh (BIM M112) - KNX
# v02.01.02 - Management Procedures 03.05.02 - §3.31.2, §3.32.2 and §3.33.2.
MEM_MANAGEMENT_CONTROL_ADDRESS = 0x0104
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


def mem_load_state_address(state_machine: ResourceObjectType) -> int:
    """Return the memory address of a BIM M112 Load State Machine's state."""
    try:
        return MEM_LOAD_STATE_ADDRESS[state_machine]
    except KeyError:
        raise ValueError(
            f"No memory mapped Load State Machine for {state_machine!r}"
        ) from None


def check_state(state: LoadState, expected: LoadState) -> None:
    """Raise VerificationError if `state` is not `expected`."""
    if state is not expected:
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
    or the intermediate state lasts longer than `timeout` seconds.
    """
    expected = EXPECTED_STATE.get(event)
    if expected is None:
        return state
    intermediate = INTERMEDIATE_STATE.get(event)
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while state is intermediate and loop.time() < deadline:
        await asyncio.sleep(poll_interval)
        state = await read_state()
    check_state(state, expected)
    return state
