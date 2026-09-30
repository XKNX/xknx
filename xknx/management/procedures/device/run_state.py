"""
Run State Machine states and run events.

The Run State Machine is specified in KNX v01.10.01 - Resources 03.05.01 -
§4.24.2 "Run State Machine - Realisation Type 1 (Property based)": its
states are read from, and its events written to, ``PID_RUN_STATE_CONTROL``
(property id 6, ``xknx.profile.const.ResourceGenericPropertyId``). Every run
event is a fixed 10 octet value; unused octets are 0 (KNX v02.01.02 -
Management Procedures 03.05.02 - §3.34.3.1-3).

Like :mod:`~.load_state`, the builders are exported as the ``run_state``
module (``procedures.run_state.restart()``), not as top-level procedures -
``no_operation`` would collide with ``load_state.no_operation``, and
``restart``/``stop`` read confusingly next to the unrelated
``dm_restart``/``dm_restart_r_co`` device-restart procedures.

Bare ``§3.34.3.x`` references in this module are to KNX v02.01.02 -
Management Procedures 03.05.02; Resources references are cited in full.
"""

from __future__ import annotations

from enum import IntEnum

from ._state_machine import EVENT_SIZE, decode_state, pad_event

# Write value width (KNX v02.01.02 - Management Procedures 03.05.02 -
# §3.34.3.1-3: each Run Control event is 1 octet of event code followed by
# 9 reserved octets).
RUN_EVENT_SIZE = EVENT_SIZE


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
    Map the 1 octet Run State read back from ``PID_RUN_STATE_CONTROL``.

    It reads back as exactly 1 octet (KNX v01.10.01 - Resources 03.05.01 -
    §4.24.2.3.1, Table 95 "8 bit"); see :func:`~._state_machine.decode_state`.

    :param context: A short description of what was read, for error
        messages - e.g. ``"object 3"`` or ``"interface object type 343
        instance 1"``.
    """
    return decode_state(data, RunState, context, "Run State Machine")


def _pad(data: bytes) -> bytes:
    """Pad a run event to its fixed 10 octet width."""
    return pad_event(data, "run")


def no_operation() -> bytes:
    """No Operation run event - has no effect (§3.34.3.3)."""
    return _pad(bytes([_RunEvent.NO_OPERATION]))


def restart() -> bytes:
    """Restart run event - requests the executable part to restart (§3.34.3.1)."""
    return _pad(bytes([_RunEvent.RESTART]))


def stop() -> bytes:
    """Stop run event - requests the executable part to stop (§3.34.3.2)."""
    return _pad(bytes([_RunEvent.STOP]))
