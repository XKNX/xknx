"""
Run State Machine states and run events.

The Run State Machine is specified in KNX v01.10.01 - Resources 03.05.01 -
§4.24.2 "Run State Machine - Realisation Type 1 (Property based)": its
states are read from, and its events written to, ``PID_RUN_STATE_CONTROL``
(property id 6, ``xknx.profile.const.ResourceGenericPropertyId``). Every run
event is a fixed 10 octet value; unused octets are 0 (KNX v02.01.02 -
Management Procedures 03.05.02 - §3.34.3.1-3).

Unlike :mod:`~.load_state`'s dozen builders, ``restart()``/``stop()``/
``no_operation()`` are not re-exported from ``xknx.management.procedures`` -
``no_operation`` would collide with ``load_state.no_operation``, and
``restart``/``stop`` read confusingly next to the unrelated
``dm_restart``/``dm_restart_r_co`` device-restart procedures. Import this
module instead: ``from xknx.management.procedures.device import run_state``.
"""

from __future__ import annotations

from enum import IntEnum

from xknx.exceptions import ManagementConnectionError

# Write value width (KNX v02.01.02 - Management Procedures 03.05.02 -
# §3.34.3.1-3: each Run Control event is 1 octet of event code followed by
# 9 reserved octets).
RUN_EVENT_SIZE = 10


class RunState(IntEnum):
    """
    State reported when reading ``PID_RUN_STATE_CONTROL``.

    KNX v01.10.01 - Resources 03.05.01 - §4.24.2.3.1, Table 95. ``TERMINATED``
    is optional; ``STARTING`` and ``SHUTTING_DOWN`` are only mandatory for an
    executable part whose startup/shutdown takes more than 2 seconds.
    """

    HALTED = 0
    RUNNING = 1
    READY = 2
    TERMINATED = 3
    STARTING = 4
    SHUTTING_DOWN = 5


class _RunEvent(IntEnum):
    """First octet of a run event (KNX v01.10.01 - Resources 03.05.01 - §4.24.2.3.2, Table 96)."""

    NO_OPERATION = 0x00
    RESTART = 0x01
    STOP = 0x02


def decode_run_state(data: bytes, context: str) -> RunState:
    """
    Map the Run State octet to :class:`RunState`, erroring on unknowns.

    ``PID_RUN_STATE_CONTROL`` reads back as exactly 1 octet (KNX v01.10.01 -
    Resources 03.05.01 - §4.24.2.3.1, Table 95 "8 bit"); the 10 octet width
    is a write-only value. A length other than 1 is rejected here rather
    than just indexing ``data[0]`` - a caller reading via
    ``dmp_interface_object_read_r`` only checks ``nr_of_elem``, not the
    octet count, so a device echoing back its 10 octet write event (a run
    event *type*, not a run *state*) would otherwise be silently decoded as
    a state.

    :param context: A short description of what was read, for error
        messages - e.g. ``"object 3"`` or ``"interface object type 343
        instance 1"``, since callers address a Run State Machine either way.
    """
    if len(data) != 1:
        raise ManagementConnectionError(
            f"{context} Run State Machine returned {len(data)} octets, expected 1"
        )
    try:
        return RunState(data[0])
    except ValueError as exc:
        raise ManagementConnectionError(
            f"{context} Run State Machine reported unknown state {data[0]:#04x}"
        ) from exc


def _pad(data: bytes) -> bytes:
    """Pad a run event to its fixed 10 octet width."""
    if len(data) > RUN_EVENT_SIZE:
        raise ValueError(f"run event too long: {len(data)} > {RUN_EVENT_SIZE}")
    return data + bytes(RUN_EVENT_SIZE - len(data))


def no_operation() -> bytes:
    """No Operation run event - has no effect (§3.34.3.3)."""
    return _pad(bytes([_RunEvent.NO_OPERATION]))


def restart() -> bytes:
    """Restart run event - requests the executable part to restart (§3.34.3.1)."""
    return _pad(bytes([_RunEvent.RESTART]))


def stop() -> bytes:
    """Stop run event - requests the executable part to stop (§3.34.3.2)."""
    return _pad(bytes([_RunEvent.STOP]))
