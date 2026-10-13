"""
Shared implementation of the Load and Run State Machine procedures.

Both state machines work the same way (KNX v01.10.01 - Resources 03.05.01 -
§4.23.2 and §4.24.2): a ``PDT_CONTROL`` property that takes a fixed 10 octet
event on write and reads back as a 1 octet state. Only the property id, the
state enum and the error handling differ, so decoding, event padding,
polling for an expected state and the extended read live here once.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Collection
from enum import IntEnum
import time
from typing import TypeVar

from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from ._pdt_control import check_ext_echo, pdt_control_state_data
from .dmp_interface_object_read_r import dmp_interface_object_read_r

# Load and run events are both "always 10 octets" (KNX v01.10.01 -
# Resources 03.05.01 - §4.2.5 and §4.2.6).
EVENT_SIZE = 10

StateT = TypeVar("StateT", bound=IntEnum)


def pad_event(data: bytes, kind: str) -> bytes:
    """Pad an event to its fixed 10 octet width."""
    if len(data) > EVENT_SIZE:
        raise ValueError(f"{kind} event too long: {len(data)} > {EVENT_SIZE}")
    return data + bytes(EVENT_SIZE - len(data))


def check_event_size(event_data: bytes) -> None:
    """Raise ValueError if ``event_data`` isn't exactly 10 octets."""
    if len(event_data) != EVENT_SIZE:
        raise ValueError(
            f"event_data must be {EVENT_SIZE} octets, got {len(event_data)}"
        )


def decode_state(
    data: bytes, state_type: type[StateT], context: str, machine: str
) -> StateT:
    """
    Map the 1 octet state read back from a state machine to ``state_type``.

    The control property reads back as exactly 1 octet; the 10 octet width
    is a write-only value. A length other than 1 is rejected rather than
    just indexing ``data[0]`` - ``dmp_interface_object_read_r``/``_write_r``
    only check ``nr_of_elem``, not the octet count, so a device echoing back
    its 10 octet write event (an event *type*, not a *state*) would
    otherwise be silently decoded as a state.

    :param context: What was read, e.g. ``"object 3"``
    :param machine: ``"Load State Machine"`` or ``"Run State Machine"``
    """
    if len(data) != 1:
        raise ManagementConnectionError(
            f"{context} {machine} returned {len(data)} octets, expected 1"
        )
    try:
        return state_type(data[0])
    except ValueError as exc:
        raise ManagementConnectionError(
            f"{context} {machine} reported unknown state {data[0]:#04x}"
        ) from exc


def expected_states(
    expected_state: StateT | Collection[StateT] | None,
) -> frozenset[StateT] | None:
    """Normalize a single expected state or a collection of them to a set."""
    if expected_state is None:
        return None
    if isinstance(expected_state, IntEnum):
        return frozenset([expected_state])
    states = frozenset(expected_state)
    if not states:
        raise ValueError("expected_state must not be empty")
    return states


def _names(states: frozenset[StateT]) -> str:
    return "/".join(sorted(state.name for state in states))


async def poll_for_state(
    conn: P2PConnection,
    object_index: int,
    property_id: int,
    decode: Callable[[bytes], StateT],
    *,
    expected: frozenset[StateT],
    state: StateT,
    poll_timeout: float,
    poll_interval: float,
    error_state: StateT | None,
    context: str,
    machine: str,
) -> StateT:
    """
    Re-read the state until it is one of ``expected`` or ``poll_timeout`` elapses.

    :param state: The state the write's own response reported
    :param error_state: A state that ends polling with an error right away
    """
    deadline = time.monotonic() + poll_timeout
    while state not in expected:
        if state == error_state:
            raise ManagementConnectionError(
                f"{context} {machine} entered {state.name} "
                f"(expected {_names(expected)})"
            )
        if time.monotonic() >= deadline:
            raise ManagementConnectionError(
                f"{context} {machine} did not reach {_names(expected)} "
                f"within {poll_timeout}s, last state {state.name}"
            )
        await asyncio.sleep(poll_interval)
        data = await dmp_interface_object_read_r(
            conn, object_index, property_id, count=1, start_index=1
        )
        state = decode(data)
    return state


async def ext_read_state(
    conn: P2PConnection,
    interface_object_type: int,
    object_instance: int,
    property_id: int,
    decode: Callable[[bytes], StateT],
    machine: str,
) -> StateT:
    """
    Read an extended-addressed state machine via A_FunctionPropertyExtState_Read.

    Checks that the response echoes the requested Interface Object Type,
    Object Instance and PID, and raises on a negative return code (KNX
    v02.01.01 - Application Layer 03.03.07 - §3.4.8.4).
    """
    response = await conn.request(
        apci.FunctionPropertyExtStateRead(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
        )
    )
    check_ext_echo(
        response.payload, interface_object_type, object_instance, property_id
    )
    context = ext_context(interface_object_type, object_instance)
    return decode(pdt_control_state_data(response.payload, f"{context} {machine} read"))


def ext_context(interface_object_type: int, object_instance: int) -> str:
    """Describe an extended-addressed state machine for error messages."""
    return f"interface object type {interface_object_type} instance {object_instance}"


def check_verified(
    state: StateT, expected_state: StateT, context: str, machine: str
) -> None:
    """Raise VerificationError if ``state`` isn't ``expected_state``."""
    if state != expected_state:
        raise VerificationError(
            f"{context} {machine} verify failed: "
            f"expected {expected_state.name}, got {state.name}"
        )
