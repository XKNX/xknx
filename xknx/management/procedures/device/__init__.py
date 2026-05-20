"""KNX 03.05.02 Device Management (DM_*) procedures."""

# ruff: noqa: F401
from .dm_authorize import FREE_ACCESS_KEY, dmp_authorize2_r_co, dmp_authorize_r_co
from .dm_connect import dm_connect
from .dm_restart_r_co import dm_restart
from .legacy import dm_restart_legacy
