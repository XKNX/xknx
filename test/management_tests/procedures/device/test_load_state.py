"""Tests for load_state — KNX v01.10.01 - Resources 03.05.01 - §4.23.2, KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3."""

import pytest

from xknx.management.procedures.device import load_state


def test_no_operation() -> None:
    """Test no_operation() encodes 00h + 9 reserved octets."""
    assert load_state.no_operation() == bytes(10)


def test_start_loading() -> None:
    """Test start_loading() encodes 01h + 9 reserved octets."""
    assert load_state.start_loading() == bytes([0x01]) + bytes(9)


def test_load_completed() -> None:
    """Test load_completed() encodes 02h + 9 reserved octets."""
    assert load_state.load_completed() == bytes([0x02]) + bytes(9)


def test_unload() -> None:
    """Test unload() encodes 04h + 9 reserved octets."""
    assert load_state.unload() == bytes([0x04]) + bytes(9)


def test_alloc_abs_data_seg() -> None:
    """Test alloc_abs_data_seg() encodes 03h 00h SSSS EEEE AA TT MM 00h."""
    result = load_state.alloc_abs_data_seg(
        0x1234, 0x0100, access_attributes=0x12, memory_type=3, memory_attributes=0x80
    )
    assert result == bytes([0x03, 0x00, 0x12, 0x34, 0x01, 0x00, 0x12, 0x03, 0x80, 0x00])


def test_alloc_abs_data_seg_defaults() -> None:
    """Test alloc_abs_data_seg() defaults access/memory fields to 0."""
    result = load_state.alloc_abs_data_seg(0x0010, 0x0020)
    assert result == bytes([0x03, 0x00, 0x00, 0x10, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00])


def test_alloc_abs_stack_seg() -> None:
    """Test alloc_abs_stack_seg() encodes 03h 01h SSSS EEEE AA TT MM 00h."""
    result = load_state.alloc_abs_stack_seg(
        0x2000, 0x0080, access_attributes=0xFF, memory_type=2, memory_attributes=0
    )
    assert result == bytes([0x03, 0x01, 0x20, 0x00, 0x00, 0x80, 0xFF, 0x02, 0x00, 0x00])


def test_alloc_abs_task_seg() -> None:
    """Test alloc_abs_task_seg() encodes 03h 02h SSSS PP MMMMTTTTVV."""
    application_id = bytes([0x00, 0x01, 0x00, 0x02, 0x03])
    result = load_state.alloc_abs_task_seg(0x4000, 0x05, application_id)
    assert result == bytes([0x03, 0x02, 0x40, 0x00, 0x05]) + application_id


def test_alloc_abs_task_seg_wrong_application_id_length() -> None:
    """Test alloc_abs_task_seg() raises ValueError for a non-5-octet application_id."""
    with pytest.raises(ValueError, match=r"application_id must be 5 octets"):
        load_state.alloc_abs_task_seg(0x4000, 0x05, b"\x00\x01")


def test_task_ptr() -> None:
    """Test task_ptr() encodes 03h 03h IIII SSSS PPPP 0000h."""
    result = load_state.task_ptr(0x1111, 0x2222, 0x3333)
    assert result == bytes([0x03, 0x03, 0x11, 0x11, 0x22, 0x22, 0x33, 0x33, 0x00, 0x00])


def test_task_ctrl_1() -> None:
    """Test task_ctrl_1() encodes 03h 04h AAAA NN + 5 reserved octets."""
    result = load_state.task_ctrl_1(0xABCD, 0x07)
    assert result == bytes([0x03, 0x04, 0xAB, 0xCD, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00])


def test_task_ctrl_2() -> None:
    """Test task_ctrl_2() encodes 03h 05h CCCC OOOO seg_ptr1 seg_ptr2."""
    result = load_state.task_ctrl_2(0x1111, 0x2222, 0x3333, 0x4444)
    assert result == bytes([0x03, 0x05, 0x11, 0x11, 0x22, 0x22, 0x33, 0x33, 0x44, 0x44])


def test_relative_allocation() -> None:
    """Test relative_allocation() encodes 03h 0Ah + 2 octet count + 6 reserved octets."""
    result = load_state.relative_allocation(0x0100)
    assert result == bytes([0x03, 0x0A, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])


def test_data_relative_allocation() -> None:
    """Test data_relative_allocation() encodes 03h 0Bh + 4 octet size + mode + fill + 2 reserved."""
    result = load_state.data_relative_allocation(0x00010000, mode=1, fill=0xFF)
    assert result == bytes([0x03, 0x0B, 0x00, 0x01, 0x00, 0x00, 0x01, 0xFF, 0x00, 0x00])


def test_data_relative_allocation_defaults() -> None:
    """Test data_relative_allocation() defaults mode/fill to 0."""
    result = load_state.data_relative_allocation(0x10)
    assert result == bytes([0x03, 0x0B, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00])


def test_pad_rejects_oversized_event() -> None:
    """Test _pad() raises ValueError for a payload longer than the 10 octet width."""
    with pytest.raises(ValueError, match=r"load event too long: 11 > 10"):
        load_state._pad(bytes(11))


def test_alloc_abs_data_seg_start_address_out_of_range() -> None:
    """Test alloc_abs_data_seg() raises ValueError for a start_address above 0xFFFF."""
    with pytest.raises(ValueError, match=r"start_address must be 0-0xffff"):
        load_state.alloc_abs_data_seg(0x10000, 1)


def test_alloc_abs_data_seg_memory_type_out_of_range() -> None:
    """Test alloc_abs_data_seg() raises ValueError for a memory_type above 0xFF."""
    with pytest.raises(ValueError, match=r"memory_type must be 0-0xff"):
        load_state.alloc_abs_data_seg(0, 1, memory_type=0x100)


def test_task_ctrl_2_field_out_of_range() -> None:
    """Test task_ctrl_2() raises ValueError for a field above 0xFFFF."""
    with pytest.raises(ValueError, match=r"comm_obj_seg_ptr_2 must be 0-0xffff"):
        load_state.task_ctrl_2(0, 0, 0, 0x10000)


def test_relative_allocation_out_of_range() -> None:
    """Test relative_allocation() raises ValueError for a count above 0xFFFF."""
    with pytest.raises(ValueError, match=r"number_of_octets must be 0-0xffff"):
        load_state.relative_allocation(0x10000)


def test_data_relative_allocation_size_out_of_range() -> None:
    """Test data_relative_allocation() raises ValueError for a size above 0xFFFFFFFF."""
    with pytest.raises(ValueError, match=r"requested_memory_size must be 0-0xffffffff"):
        load_state.data_relative_allocation(0x100000000)


def test_negative_value_out_of_range() -> None:
    """Test _uint() raises ValueError for a negative value."""
    with pytest.raises(ValueError, match=r"init_addr must be 0-0xffff, got -0x1"):
        load_state.task_ptr(-1, 0, 0)


def test_all_events_are_ten_octets() -> None:
    """Test every load event builder produces exactly the fixed 10 octet width."""
    events = [
        load_state.no_operation(),
        load_state.start_loading(),
        load_state.load_completed(),
        load_state.unload(),
        load_state.alloc_abs_data_seg(0, 0),
        load_state.alloc_abs_stack_seg(0, 0),
        load_state.alloc_abs_task_seg(0, 0, b"\x00" * 5),
        load_state.task_ptr(0, 0, 0),
        load_state.task_ctrl_1(0, 0),
        load_state.task_ctrl_2(0, 0, 0, 0),
        load_state.relative_allocation(0),
        load_state.data_relative_allocation(0),
    ]
    assert all(len(event) == load_state.LOAD_EVENT_SIZE for event in events)
