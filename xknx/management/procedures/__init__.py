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

Procedures whose KNX name already ends in ``_R`` or in a communication mode
suffix such as ``_RCo`` (KNX v02.01.02 - Management Procedures 03.05.02 -
§1.2, Table 1) take ``conn`` under that name, without the ``_conn`` suffix, e.g.
``dm_restart_r_co`` or ``dmp_interface_object_read_r``. ``conn`` is an open
``P2PConnection``. Where the spec allows the connectionless communication
mode as well, it may also be a ``ConnectionlessP2P`` from
``xknx.management.connectionless()``, e.g. for ``dm_function_property_write_r``
(§3.30.1) and ``dmp_ext_function_property_write_r`` (§3.30.2).

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
    dm_function_property_write_r,
    dm_restart,
    dm_restart_r_co,
    dmp_authorize2_r_co,
    dmp_authorize_r_co,
    dmp_connect_r_co,
    dmp_ext_function_property_write_r,
    dmp_interface_object_read_r,
    dmp_interface_object_scan_r,
    dmp_interface_object_verify_r,
    dmp_interface_object_write_r,
    dmp_mem_read_r_co,
    dmp_mem_verify_r_co,
    dmp_mem_write_r_co,
    dmp_user_mem_read_r_co,
    dmp_user_mem_verify_r_co,
    dmp_user_mem_write_r_co,
)
from .network import (
    nm_individual_address_check,
    nm_individual_address_check_conn,
    nm_individual_address_read,
    nm_individual_address_serial_number_read,
    nm_individual_address_serial_number_write,
    nm_individual_address_write,
)
