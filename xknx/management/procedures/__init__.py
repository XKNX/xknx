"""
Management procedures grouped by KNX spec family.

Subpackages are created when their first procedure lands. Naming mirrors
the KNX spec prefix:

  - ``network/`` for NM_* procedures (KNX v02.01.02 - Management Procedures
    03.05.02 - Network Management)
  - ``device/`` for DM_* procedures (KNX v02.01.02 - Management Procedures
    03.05.02 - Device Management)
  - ``ftp/`` for FTP_* procedures (KNX v02.01.02 - Management Procedures
    03.05.02 - §8 File Transfer)

Per-procedure files inside each subpackage host a single public ``async def``
function. This package re-exports every implemented procedure so callers can
import ``procedures`` via ``from xknx.management import procedures``, import
individual functions via ``from xknx.management.procedures import <func>``, or
access them as attributes such as ``procedures.<func>``.

Most procedures come in two forms:

  - ``<spec_name>(xknx: XKNX, ...)`` opens (and closes) whatever P2P
    connections or broadcasts it needs on its own, via ``xknx.management``.
  - ``<spec_name>_conn(conn: P2PConnection, ...)`` operates on an
    already-open connection, for chaining several procedures over one
    connection. This suffix is an xknx convention, not a KNX spec name.
    ``dm_restart_r_co`` is the one exception — ``RCo`` is the actual KNX
    v02.01.02 - Management Procedures 03.05.02 - §3.7.3 procedure name for
    the connection-based variant of DM_Restart, not the xknx convention.

When adding a new procedure follow the workflow:

  1. Create ``procedures/<family>/<spec_name>.py`` with the spec text embedded
     in the module docstring and ``raise NotImplementedError`` until impl lands.
  2. Mirror under ``test/management_tests/procedures/<family>/test_<name>.py``.
  3. Replace ``NotImplementedError`` with the implementation and un-skip tests.
"""

# ruff: noqa: F401
from .device import (
    FREE_ACCESS_KEY,
    LOAD_EVENT_SIZE,
    RUN_EVENT_SIZE,
    GroupObjectLink,
    LoadState,
    RunState,
    ScannedInterfaceObject,
    SegmentType,
    alloc_abs_data_seg,
    alloc_abs_stack_seg,
    alloc_abs_task_seg,
    data_relative_allocation,
    dm_function_property_write_r,
    dm_function_property_write_r_conn,
    dm_group_object_link_read_r_cl,
    dm_group_object_link_write_r_cl,
    dm_restart,
    dm_restart_r_co,
    dmp_authorize2_r_co,
    dmp_authorize_r_co,
    dmp_connect_r_co,
    dmp_download_loadable_part_r_co_io,
    dmp_ext_function_property_write_r,
    dmp_ext_function_property_write_r_conn,
    dmp_ext_load_state_machine_read_r_co_io,
    dmp_ext_load_state_machine_verify_r_co_io,
    dmp_ext_run_state_machine_read_r_co_io,
    dmp_ext_run_state_machine_verify_r_co_io,
    dmp_ext_run_state_machine_write_r_co_io,
    dmp_interface_object_read_r,
    dmp_interface_object_scan_r,
    dmp_interface_object_verify_r,
    dmp_interface_object_write_r,
    dmp_load_state_machine_read_r_io,
    dmp_load_state_machine_verify_r_io,
    dmp_load_state_machine_write_r_co_io,
    dmp_mem_read_extended_r,
    dmp_mem_read_r_co,
    dmp_mem_verify_extended_r,
    dmp_mem_verify_r_co,
    dmp_mem_write_extended_r,
    dmp_mem_write_r_co,
    dmp_prog_mode_switch_r_co,
    dmp_run_state_machine_read_r_io,
    dmp_run_state_machine_verify_r_io,
    dmp_run_state_machine_write_r_io,
    dmp_user_mem_read_r_co,
    dmp_user_mem_verify_r_co,
    dmp_user_mem_write_r_co,
    load_completed,
    no_operation,
    relative_allocation,
    start_loading,
    task_ctrl_1,
    task_ctrl_2,
    task_ptr,
    unload,
)
from .network import (
    nm_individual_address_check,
    nm_individual_address_check_conn,
    nm_individual_address_read,
    nm_individual_address_serial_number_read,
    nm_individual_address_serial_number_write,
    nm_individual_address_write,
)
