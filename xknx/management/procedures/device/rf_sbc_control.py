"""Set the routing of system broadcast services in a KNX TP1/RF Media Coupler. Not in spec."""

from __future__ import annotations

from enum import IntEnum
import logging
from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.network.nm_object_index_read import (
    nm_object_index_read,
)
from xknx.profile.const import ResourceObjectType, ResourceRouterPropertyId
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

from .dm_function_property_write_r import dm_function_property_write_r

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


class RFSBCMode(IntEnum):
    """
    Routing of system broadcast services onto KNX RF.

    KNX v01.10.01 - Resources 03.05.01 - §4.5.15.1 PID_RF_SBC_CONTROL, Table 27.
    """

    DISABLED = 0
    BROADCAST = 1
    SYSTEM_BROADCAST = 2


async def rf_sbc_control_write(
    xknx: XKNX, coupler: IndividualAddressableType, mode: RFSBCMode
) -> RFSBCMode:
    """
    Set PID_RF_SBC_CONTROL of a KNX TP1/RF Media Coupler (mask 2920h) and return the mode it has now.

    Not in spec: it combines the steps of KNX v02.01.01 - Configuration
    Procedures 03.05.03 - §2.3.1.3/§2.3.1.4: NM_ObjectIndex_Read of the second
    Router Object (the Secondary Side, the RF one) and DM_FunctionProperty_Write_R
    of PID_RF_SBC_CONTROL in it. Before an RF device in another RF domain gets its
    Domain and individual address, the Media Coupler towards it is set to
    `SYSTEM_BROADCAST` and every other one to `DISABLED`; afterwards it is set to
    `DISABLED` again. A mode other than `DISABLED` ends after 10 minutes by itself.

    :raises ManagementConnectionError: when the coupler has no second Router Object
        or refuses the mode (its return code is in the message)
    """
    address = IndividualAddress(coupler)
    indexes = await nm_object_index_read(
        xknx, address, ResourceObjectType.OBJECT_ROUTER, start_instance=2
    )
    if not indexes:
        raise ManagementConnectionError(
            f"{address} has no Router Object for an RF Secondary Side"
        )
    async with xknx.management.connection(address) as conn:
        response = await dm_function_property_write_r(
            conn,
            indexes[0],
            ResourceRouterPropertyId.PID_RF_SBC_CONTROL,
            bytes((mode,)),
        )
    if response.return_code != 0:
        raise ManagementConnectionError(
            f"{address} refused system broadcast routing {mode.name}: "
            f"return code {response.return_code}"
        )
    current = RFSBCMode(response.data[0]) if response.data else mode
    logger.debug("System broadcast routing of %s: %s", address, current.name)
    return current
