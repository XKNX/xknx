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

Procedures come in up to two forms:

  - ``<spec_name>(conn: P2PConnection, ...)`` operates on an already-open
    connection, so several procedures can be chained over one connection.
    This is the common form, used by every procedure that runs over a
    point-to-point connection unless it also has the wrapper below. Where
    the spec allows connectionless mode too (``_R``, ``_RCl``), it is
    noted in the procedure's docstring that xknx runs it over ``conn``.
  - Optionally, a wrapper ``<spec_name>(xknx: XKNX, individual_address,
    ...)`` that opens (and closes) the connection or broadcast itself via
    ``xknx.management``. A procedure that has this wrapper takes ``conn``
    under ``<spec_name>_conn`` instead - this suffix is an xknx convention,
    not a KNX spec name (e.g. ``dm_function_property_write_r`` /
    ``dm_function_property_write_r_conn``,
    ``nm_individual_address_check`` / ``nm_individual_address_check_conn``).
    ``dm_restart`` / ``dm_restart_r_co`` is the one exception - ``RCo`` is
    the actual KNX v02.01.02 - Management Procedures 03.05.02 - §3.7.3
    procedure name for the connection-based variant of DM_Restart.

Procedures that only use broadcasts (e.g. ``nm_individual_address_read``)
have no connection to share and take ``xknx`` under the bare name.

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
    LoadState,
    MemoryType,
    RunState,
    ScannedInterfaceObject,
    SegmentType,
    dm_function_property_write_r,
    dm_function_property_write_r_conn,
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
    dmp_ext_load_state_machine_write_r_co_io,
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
    dmp_mem_read_r_co,
    dmp_mem_verify_r_co,
    dmp_mem_write_r_co,
    dmp_run_state_machine_read_r_io,
    dmp_run_state_machine_verify_r_io,
    dmp_run_state_machine_write_r_io,
    dmp_user_mem_read_r_co,
    dmp_user_mem_verify_r_co,
    dmp_user_mem_write_r_co,
    load_state,
    run_state,
)
from .network import (
    nm_individual_address_check,
    nm_individual_address_check_conn,
    nm_individual_address_read,
    nm_individual_address_serial_number_read,
    nm_individual_address_serial_number_write,
    nm_individual_address_write,
)
