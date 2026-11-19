"""NM_ObjectIndex_Read — KNX v02.01.02 - Management Procedures 03.05.02 - §2.23.4."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionError, ManagementConnectionTimeout
from xknx.management.management import MANAGEMENT_CONNECTION_TIMEOUT
from xknx.profile.const import ResourceGenericPropertyId
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


async def nm_object_index_read(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
    object_type: int,
    start_instance: int = 1,
    number_of_instances: int = 1,
) -> list[int]:
    """
    Read the Object Indexes of the instances of an Interface Object Type in one device.

    A connectionless A_NetworkParameter_Read of PID_OBJECT_INDEX with
    `start_instance` (counted from 1) and `number_of_instances`. Returns the Object
    Indexes the device answered with, in ascending order: as many as it has from
    `start_instance` on, up to `number_of_instances`. With both 0 the device answers
    with no index; use `start_instance=1` and a larger count to read them. Ask for 9
    or less at once unless the device takes long frames (§2.23.4.2).

    Raises ManagementConnectionTimeout when the device doesn't answer.

    :param xknx: the XKNX object
    :param individual_address: the device
    :param object_type: the Interface Object Type, e.g. 6 for the Router Object
    :param start_instance: the first instance to return the index of
    :param number_of_instances: how many instances to return the indexes of
    """
    address = IndividualAddress(individual_address)
    request = apci.NetworkParameterRead(
        object_type=object_type,
        property_id=ResourceGenericPropertyId.PID_OBJECT_INDEX,
        test_info=bytes((start_instance, number_of_instances)),
    )
    async with xknx.management.connectionless(address) as connectionless:
        await connectionless.send(request)
        async for telegram in connectionless.receive(
            apci.NetworkParameterResponse, timeout=MANAGEMENT_CONNECTION_TIMEOUT
        ):
            response = telegram.payload
            if (
                response.object_type == object_type
                and response.property_id == ResourceGenericPropertyId.PID_OBJECT_INDEX
            ):
                result = response.test_info_and_result
                if len(result) < 2:
                    raise ManagementConnectionError(
                        f"Invalid object index response from {address}: {result.hex()}"
                    )
                indexes = list(result[2:])
                logger.debug(
                    "Object indexes of object type %s in %s: %s",
                    object_type,
                    address,
                    indexes,
                )
                return indexes
    raise ManagementConnectionTimeout(f"No object index response from {address}")
