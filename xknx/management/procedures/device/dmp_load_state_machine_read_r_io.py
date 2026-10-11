"""DMP_LoadStateMachineRead_R_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.33.3."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import LoadState, ResourceGenericPropertyId
from xknx.telegram import apci

from ._load_state_machine import decode_load_state

__all__ = ["dmp_load_state_machine_read_r_io"]


async def dmp_load_state_machine_read_r_io(
    conn: P2PConnection, object_index: int
) -> LoadState:
    """
    Read the state of a property based Load State Machine.

    DMP_LoadStateMachineRead_R_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.33.3. Reads PID_LOAD_STATE_CONTROL of the Interface Object
    hosting the Load State Machine. Requires an established connection
    (DM_Connect must be executed first).

    :param conn: Active P2P connection to the device
    :param object_index: Index of the Interface Object hosting the Load State
        Machine - eg. found with dmp_interface_object_scan_r
    :return: The current Load State
    :raises ManagementConnectionError: If the device returns no data (the
        Property does not exist) or an unknown state
    """
    response = await conn.request(
        payload=apci.PropertyValueRead(
            object_index=object_index,
            property_id=ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
            count=1,
            start_index=1,
        ),
    )
    if response.payload.count == 0:
        raise ManagementConnectionError(
            f"Load State Machine read failed: object {object_index} returned "
            "nr_of_elem=0"
        )
    return decode_load_state(response.payload.data)
