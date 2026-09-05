"""
Load State Machine states and load events.

The Load State Machine is specified in KNX v01.10.01 - Resources 03.05.01 -
§4.23.2 "Load State Machine - Realisation Type 1 (Property based)": its
states are read from, and its events written to, ``PID_LOAD_STATE_CONTROL``
(property id 5, ``xknx.profile.const.ResourceGenericPropertyId``). The
"Additional Load Controls" event (03h) and its subtypes carry the segment
allocation/task control data a Load Procedure uses; their encoding is
specified in KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3.1-4
(:class:`DMP_LoadStateMachineWrite_RCo_IO`). Every load event is a fixed
10 octet value; unused octets are 0.
"""

from __future__ import annotations

from enum import IntEnum

# Write value width (KNX v01.10.01 - Resources 03.05.01 - §4.2.5
# PID_LOAD_STATE_CONTROL: "The write value shall always be 10 octets.").
LOAD_EVENT_SIZE = 10


class LoadState(IntEnum):
    """
    State reported when reading ``PID_LOAD_STATE_CONTROL``.

    KNX v01.10.01 - Resources 03.05.01 - §4.23.2.3.1, Table 92. ``UNLOADING``
    and ``LOAD_COMPLETING`` are optional intermediate states a device may
    report while an Unload or LoadCompleted transition is still in progress.
    """

    UNLOADED = 0
    LOADED = 1
    LOADING = 2
    ERROR = 3
    UNLOADING = 4
    LOAD_COMPLETING = 5


class _LoadEvent(IntEnum):
    """First octet of a load event (KNX v01.10.01 - Resources 03.05.01 - §4.23.2.3.2, Table 93)."""

    NO_OPERATION = 0x00
    START_LOADING = 0x01
    LOAD_COMPLETED = 0x02
    ADDITIONAL = 0x03
    UNLOAD = 0x04


class SegmentType(IntEnum):
    """Second octet of an ``ADDITIONAL`` load event (KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3.4)."""

    ABS_DATA = 0x00
    ABS_STACK = 0x01
    ABS_TASK = 0x02
    TASK_PTR = 0x03
    TASK_CTRL_1 = 0x04
    TASK_CTRL_2 = 0x05
    RELATIVE_ALLOCATION = 0x0A
    DATA_RELATIVE_ALLOCATION = 0x0B


def _pad(data: bytes) -> bytes:
    """Pad a load event to its fixed 10 octet width."""
    if len(data) > LOAD_EVENT_SIZE:
        raise ValueError(f"load event too long: {len(data)} > {LOAD_EVENT_SIZE}")
    return data + bytes(LOAD_EVENT_SIZE - len(data))


def _uint(value: int, octets: int, name: str) -> bytes:
    """Validate ``value`` fits an unsigned big-endian field, or raise ValueError."""
    maximum = (1 << (octets * 8)) - 1
    if not 0 <= value <= maximum:
        raise ValueError(f"{name} must be 0-{maximum:#x}, got {value:#x}")
    return value.to_bytes(octets, "big")


def no_operation() -> bytes:
    """No Operation load event - has no effect (§3.31.3.6)."""
    return _pad(bytes([_LoadEvent.NO_OPERATION]))


def start_loading() -> bytes:
    """Start Loading load event - Load State Machine transitions to Loading (§3.31.3.2)."""
    return _pad(bytes([_LoadEvent.START_LOADING]))


def load_completed() -> bytes:
    """Load Completed load event - Load State Machine transitions to Loaded (§3.31.3.3)."""
    return _pad(bytes([_LoadEvent.LOAD_COMPLETED]))


def unload() -> bytes:
    """Unload load event - Load State Machine transitions to Unloaded (§3.31.3.1)."""
    return _pad(bytes([_LoadEvent.UNLOAD]))


def _alloc_abs_segment(
    segment_type: SegmentType,
    start_address: int,
    length: int,
    *,
    access_attributes: int,
    memory_type: int,
    memory_attributes: int,
) -> bytes:
    """
    Shared layout of AllocAbsDataSeg/AllocAbsStackSeg (§3.31.3.4).

    Access attributes: bits 0-3 write access level, bits 4-7 read access
    level. Memory type: bits 0-2 (1 = zero page RAM, 2 = RAM, 3 = EEPROM).
    Memory attributes: bit 7 enables checksum control.
    """
    return _pad(
        bytes([_LoadEvent.ADDITIONAL, segment_type])
        + _uint(start_address, 2, "start_address")
        + _uint(length, 2, "length")
        + _uint(access_attributes, 1, "access_attributes")
        + _uint(memory_type, 1, "memory_type")
        + _uint(memory_attributes, 1, "memory_attributes")
    )


def alloc_abs_data_seg(
    start_address: int,
    length: int,
    *,
    access_attributes: int = 0,
    memory_type: int = 0,
    memory_attributes: int = 0,
) -> bytes:
    """AllocAbsDataSeg load event: absolute allocation of data (segment type 0, §3.31.3.4)."""
    return _alloc_abs_segment(
        SegmentType.ABS_DATA,
        start_address,
        length,
        access_attributes=access_attributes,
        memory_type=memory_type,
        memory_attributes=memory_attributes,
    )


def alloc_abs_stack_seg(
    start_address: int,
    length: int,
    *,
    access_attributes: int = 0,
    memory_type: int = 0,
    memory_attributes: int = 0,
) -> bytes:
    """AllocAbsStackSeg load event: absolute allocation of a stack (segment type 1, §3.31.3.4)."""
    return _alloc_abs_segment(
        SegmentType.ABS_STACK,
        start_address,
        length,
        access_attributes=access_attributes,
        memory_type=memory_type,
        memory_attributes=memory_attributes,
    )


def alloc_abs_task_seg(
    start_address: int,
    pei_type: int,
    application_id: bytes,
) -> bytes:
    """
    AllocAbsTaskSeg load event: absolute task segment allocation (segment type 2, §3.31.3.4).

    ``application_id`` is the 5 octet Application ID / Table ID: Software
    Manufacturer ID (2), Manufacturer Specific Application Software ID (2)
    and Version of the Application Software (1).
    """
    if len(application_id) != 5:
        raise ValueError("application_id must be 5 octets")
    return _pad(
        bytes([_LoadEvent.ADDITIONAL, SegmentType.ABS_TASK])
        + _uint(start_address, 2, "start_address")
        + _uint(pei_type, 1, "pei_type")
        + application_id
    )


def task_ptr(init_addr: int, save_addr: int, pei_handler: int) -> bytes:
    """TaskPtr load event (segment type 3, §3.31.3.4)."""
    return _pad(
        bytes([_LoadEvent.ADDITIONAL, SegmentType.TASK_PTR])
        + _uint(init_addr, 2, "init_addr")
        + _uint(save_addr, 2, "save_addr")
        + _uint(pei_handler, 2, "pei_handler")
    )


def task_ctrl_1(interface_object_address: int, nr_of_interface_objects: int) -> bytes:
    """TaskCtrl1 load event (segment type 4, §3.31.3.4)."""
    return _pad(
        bytes([_LoadEvent.ADDITIONAL, SegmentType.TASK_CTRL_1])
        + _uint(interface_object_address, 2, "interface_object_address")
        + _uint(nr_of_interface_objects, 1, "nr_of_interface_objects")
    )


def task_ctrl_2(
    callback_addr: int,
    comm_obj_ptr: int,
    comm_obj_seg_ptr_1: int,
    comm_obj_seg_ptr_2: int,
) -> bytes:
    """TaskCtrl2 load event (segment type 5, §3.31.3.4)."""
    return _pad(
        bytes([_LoadEvent.ADDITIONAL, SegmentType.TASK_CTRL_2])
        + _uint(callback_addr, 2, "callback_addr")
        + _uint(comm_obj_ptr, 2, "comm_obj_ptr")
        + _uint(comm_obj_seg_ptr_1, 2, "comm_obj_seg_ptr_1")
        + _uint(comm_obj_seg_ptr_2, 2, "comm_obj_seg_ptr_2")
    )


def relative_allocation(number_of_octets: int) -> bytes:
    """
    Relative Allocation load event (subtype 0Ah, §3.31.3.4).

    Sets the maximum size (in octets) of the loadable part being loaded; the
    Load State Machine changes to Error if the device does not support the
    requested size.
    """
    return _pad(
        bytes([_LoadEvent.ADDITIONAL, SegmentType.RELATIVE_ALLOCATION])
        + _uint(number_of_octets, 2, "number_of_octets")
    )


def data_relative_allocation(
    requested_memory_size: int, *, mode: int = 0, fill: int = 0
) -> bytes:
    """
    Build the Data Relative Allocation load event (subtype 0Bh, §3.31.3.4).

    ``mode`` bit 0 set fills the allocated memory with ``fill``; clear keeps
    the existing memory contents unchanged. Other bits are reserved.
    """
    return _pad(
        bytes([_LoadEvent.ADDITIONAL, SegmentType.DATA_RELATIVE_ALLOCATION])
        + _uint(requested_memory_size, 4, "requested_memory_size")
        + _uint(mode, 1, "mode")
        + _uint(fill, 1, "fill")
    )
