"""DMP_LoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3."""

from __future__ import annotations

from collections.abc import Collection
from functools import partial

from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceGenericPropertyId

from ._state_machine import check_event_size, expected_states, poll_for_state
from .dmp_interface_object_write_r import dmp_interface_object_write_r
from .load_state import LoadState, decode_load_state

__all__ = ["dmp_load_state_machine_write_r_co_io"]

# KNX v01.10.01 - Resources 03.05.01 - §4.23.2.1: "The transitions between
# the states shall be less than 30 seconds. This time shall be the minimum
# delay during which a MaC shall wait after sending a load event until
# interpretation of the load event with the expected state transition to be
# failed."
_DEFAULT_POLL_TIMEOUT = 30.0
_DEFAULT_POLL_INTERVAL = 1.0
# KNX v01.10.01 - Resources 03.05.01 - §4.23.2.4.1: "The period for reading
# shall not exceed half the TL-timeout, i.e. 3 seconds."
_MAX_POLL_INTERVAL = 3.0


async def dmp_load_state_machine_write_r_co_io(
    conn: P2PConnection,
    object_index: int,
    event_data: bytes,
    *,
    expected_state: LoadState | Collection[LoadState] | None = None,
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

    While polling through LoadCompleting, KNX v01.10.01 - Resources 03.05.01
    - §4.23.2.4.1 limits the read period to half the TL-timeout (3 seconds),
    so ``poll_interval`` is capped there. The same clause says the MaC
    "shall try to re-establish the connection periodically" if the device
    drops it during that transition (NOTE 86: "A device may be offline
    during state LoadCompleting"); this function works on the given
    ``conn`` and can't reconnect, so that is left to the caller - a dropped
    connection surfaces as ``ManagementConnectionError``.

    Note that a 10 octet ``event_data`` reaches
    ``dmp_interface_object_write_r`` as a single ``PDT_CONTROL`` element,
    whose ``A_PropertyValue_Write``-PDU overhead is
    ``const.PROPERTY_VALUE_HEADER_OCTETS`` (5) - together exactly the 15
    octets an L_Data_Standard frame carries after its TPCI octet
    (``cemi.const.STANDARD_FRAME_MAX_NPDU_LENGTH``, this function's implicit
    default via ``dmp_interface_object_write_r``). That a load event always
    fits with nothing to spare is load-bearing, not coincidental - it is why
    this function needs no ``max_apdu_length`` parameter of its own.

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param event_data: The 10 octet load event
    :param expected_state: If given, poll until the Load State Machine
        reaches this state - or any of them, if a collection is given - (or
        ``LoadState.ERROR``, or ``poll_timeout`` elapses). KNX v01.10.01 - Resources 03.05.01 - §4.23.2.3.2: "Illegal
        additional events... shall be ignored and shall not lead to a change
        of state" and "Unknown events shall be ignored" - a rejected event is
        otherwise indistinguishable from one that is just slow to take
        effect, so ``expected_state`` is the only way to detect it (as a
        ``poll_timeout`` instead of a state change).
    :param poll_timeout: Seconds to poll for ``expected_state`` before giving
        up
    :param poll_interval: Seconds to wait between polls, more than 0 and at
        most 3
    :return: The resulting Load State
    :raises ValueError: If ``event_data`` is not exactly 10 octets,
        ``poll_interval`` is outside (0, 3], or ``expected_state`` is an
        empty collection
    :raises ManagementConnectionError: If the Load State Machine reaches
        ``LoadState.ERROR``, or does not reach ``expected_state`` within
        ``poll_timeout``
    """
    check_event_size(event_data)
    if not 0 < poll_interval <= _MAX_POLL_INTERVAL:
        raise ValueError(
            f"poll_interval must be more than 0 and at most {_MAX_POLL_INTERVAL}s, "
            f"got {poll_interval}"
        )
    expected = expected_states(expected_state)
    property_id = ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL
    context = f"object {object_index}"
    response = await dmp_interface_object_write_r(
        conn, object_index, property_id, event_data, count=1, start_index=1
    )
    state = decode_load_state(response, context)
    if expected is None:
        return state
    return await poll_for_state(
        conn,
        object_index,
        property_id,
        partial(decode_load_state, context=context),
        expected=expected,
        state=state,
        poll_timeout=poll_timeout,
        poll_interval=poll_interval,
        error_state=LoadState.ERROR,
        context=context,
        machine="Load State Machine",
    )
