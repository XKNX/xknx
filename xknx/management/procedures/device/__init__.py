"""KNX 03.05.02 Device Management (DM_*) procedures."""

# ruff: noqa: F401
from .dm_restart_r_co import dm_restart
from .dmp_interface_object_read_r import dmp_interface_object_read_r
from .dmp_interface_object_write_r import dmp_interface_object_write_r
from .legacy import dm_restart_legacy
