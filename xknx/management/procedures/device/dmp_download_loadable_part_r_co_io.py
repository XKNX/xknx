"""DMP_DownloadLoadablePart_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.4."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence

from xknx.management.management import P2PConnection
from xknx.profile.const import LoadEvent

from ._load_state_machine import TRANSITION_TIMEOUT
from .dmp_load_state_machine_write_r_co_io import dmp_load_state_machine_write_r_co_io

__all__ = ["dmp_download_loadable_part_r_co_io"]


async def dmp_download_loadable_part_r_co_io(
    conn: P2PConnection,
    object_index: int,
    load: Callable[[], Awaitable[None]],
    additional_load_controls: Sequence[bytes] = (),
    unload: bool = True,
    timeout: float = TRANSITION_TIMEOUT,
    poll_interval: float = 1.0,
) -> None:
    """
    Download one loadable part through its property based Load State Machine.

    DMP_DownloadLoadablePart_RCo_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.31.4.1, the complete download sequence of one loadable part:

    1. Unload (optional) - the state shall become Unloaded; Unloading is read
       again for up to `timeout` seconds.
    2. Start Loading - the state shall become Loading.
    3. Additional Load Controls (optional, repeatable) - the state shall stay
       Loading.
    4. Load the data of the loadable part, via Property or memory access -
       done by `load`.
    5. Load Completed - the state shall become Loaded; the optional
       intermediate state LoadCompleting (KNX v01.10.01 - Resources 03.05.01 -
       §4.23.2.3.2) is read again for up to `timeout` seconds.

    Every step uses dmp_load_state_machine_write_r_co_io with verify enabled.
    Requires an established connection (DM_Connect must be executed first).

    :param conn: Active P2P connection to the device
    :param object_index: Index of the Interface Object hosting the Load State
        Machine of the loadable part
    :param load: Called in state Loading to transfer the data of the loadable
        part - eg. with dmp_mem_write_r_co or dmp_interface_object_write_r on
        the same connection
    :param additional_load_controls: Event data of each Additional Load Control
        to send after Start Loading - the sub type followed by its data, at most
        9 octets each (§3.31.3.4), eg. a Load Event Relative Allocation
    :param unload: Unload the part first
    :param timeout: Seconds to wait for an intermediate state to end - KNX
        v01.10.01 - Resources 03.05.01 - §4.23.2.1 makes 30 seconds the minimum
    :param poll_interval: Seconds between reads of an intermediate state
    :raises ValueError: If an additional load control is longer than 9 octets
    :raises VerificationError: If a step does not lead to the expected state
    :raises ManagementConnectionError: If the device returns no data or an
        unknown state
    """
    for control in additional_load_controls:
        if len(control) > 9:
            raise ValueError(
                f"Additional load control must be at most 9 octets, got {len(control)}"
            )

    async def write(event: LoadEvent, event_data: bytes = b"") -> None:
        await dmp_load_state_machine_write_r_co_io(
            conn,
            object_index,
            event,
            event_data,
            verify=True,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    if unload:
        await write(LoadEvent.UNLOAD)
    await write(LoadEvent.START_LOADING)
    for control in additional_load_controls:
        await write(LoadEvent.ADDITIONAL_LOAD_CONTROLS, control)
    await load()
    await write(LoadEvent.LOAD_COMPLETED)
