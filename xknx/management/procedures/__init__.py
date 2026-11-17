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
function, together with helpers specific to it. This package re-exports every
implemented procedure so callers can import ``procedures`` via
``from xknx.management import procedures``, import individual functions via
``from xknx.management.procedures import <func>``, or access them as
attributes such as ``procedures.<func>``.

Most procedures come in two forms:

  - ``<spec_name>(xknx: XKNX, ...)`` opens (and closes) whatever P2P
    connections or broadcasts it needs on its own, via ``xknx.management``.
  - ``<spec_name>_conn(conn: P2PConnection, ...)`` operates on an
    already-open connection, for chaining several procedures over one
    connection. This suffix is an xknx convention, not a KNX spec name.

Where the spec itself names a procedure's variants by how they reach the
device, xknx keeps that spec name instead of ``_conn``: ``_r_co`` for RCo
(connection-oriented, e.g. ``dm_restart_r_co``, ``dmp_mem_read_r_co``,
``dmp_prog_mode_switch_r_co``), ``_r`` for R (e.g.
``dmp_interface_object_read_r``), and ``_r_io``, ``_r_co_io`` and
``_r_co_mem`` for R_IO, RCo_IO and RCo_Mem, as in KNX v02.01.02 - Management
Procedures 03.05.02 - §3.7.3 for DM_Restart_RCo or §3.31.3 for
DMP_LoadStateMachineWrite_RCo_IO (``dmp_load_state_machine_write_r_co_io``).
Most of these only exist in the connection-based form. A plain
``<spec_name>(xknx, ...)`` beside one of them (``dm_restart``,
``dm_prog_mode_switch``) opens and closes the connection around it.

A function that does what no spec procedure does gets a name without the
``nm_``/``dm_``/``dmp_`` prefix, lives in its own module and says "Not in
spec" in its docstring, e.g. ``prog_mode_switch``, which picks the
Programming Mode location by mask version. On an already-open connection it
takes the ``_conn`` suffix, e.g. ``prog_mode_property_switch_conn``.

When adding a new procedure follow the workflow:

  1. Create ``procedures/<family>/<spec_name>.py`` with the spec text embedded
     in the module docstring and ``raise NotImplementedError`` until impl lands.
  2. Mirror under ``test/management_tests/procedures/<family>/test_<name>.py``.
  3. Replace ``NotImplementedError`` with the implementation and un-skip tests.
"""

# ruff: noqa: F401
from .device import (
    FREE_ACCESS_KEY,
    ScannedInterfaceObject,
    dm_load_state_machine_verify_r_co_mem,
    dm_load_state_machine_verify_r_io,
    dm_prog_mode_switch,
    dm_restart,
    dm_restart_r_co,
    dmp_authorize2_r_co,
    dmp_authorize_r_co,
    dmp_connect_r_co,
    dmp_download_loadable_part_r_co_io,
    dmp_ext_load_state_machine_read_r_co_io,
    dmp_ext_load_state_machine_verify_r_co_io,
    dmp_ext_load_state_machine_write_r_co_io,
    dmp_interface_object_read_r,
    dmp_interface_object_scan_r,
    dmp_interface_object_verify_r,
    dmp_interface_object_write_r,
    dmp_load_state_machine_read_r_co_mem,
    dmp_load_state_machine_read_r_io,
    dmp_load_state_machine_write_r_co_io,
    dmp_load_state_machine_write_r_co_mem,
    dmp_mem_read_r_co,
    dmp_mem_verify_r_co,
    dmp_mem_write_r_co,
    dmp_prog_mode_switch_r_co,
    dmp_user_mem_read_r_co,
    dmp_user_mem_verify_r_co,
    dmp_user_mem_write_r_co,
    load_event_data_relative_allocation,
    load_event_relative_allocation,
    prog_mode_property_switch_conn,
    prog_mode_switch,
)
from .network import (
    nm_individual_address_check,
    nm_individual_address_check_conn,
    nm_individual_address_read,
    nm_individual_address_serial_number_read,
    nm_individual_address_serial_number_write,
    nm_individual_address_write,
)
