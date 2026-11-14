"""
EMI1 and EMI2 messages of KNX USB interfaces without cEMI.

xknx works with cEMI frames, so the data link layer messages of an EMI1 or EMI2
interface are converted: L_Data.req from cEMI, L_Data.con, L_Data.ind and
L_Busmon.ind to cEMI. Only standard frames exist in EMI1 and EMI2.
KNX v01.04.02 - External Message Interface 03.06.03 - §3
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

from xknx.cemi import CEMIMessageCode
from xknx.exceptions import ConversionError

from .const import EMIID

# cEMI additional information types - KNX v01.04.02 - External Message Interface 03.06.03 - §4.1.4.3
_CEMI_BUSMONITOR_STATUS_INFO: Final = 0x03
_CEMI_TIMESTAMP_RELATIVE: Final = 0x04
# the longest APDU of a standard frame
MAX_APDU_LENGTH: Final = 15

# cEMI control field 1 - KNX v01.04.02 - External Message Interface 03.06.03 - §4.1.5.3
_CEMI_STANDARD_FRAME: Final = 0x80
_CEMI_NOT_REPEATED: Final = 0x20
_CEMI_BROADCAST: Final = 0x10
# EMI control field bits a host may interpret - KNX v01.04.02 - External Message
# Interface 03.06.03 - §3.3.4.3, §3.3.4.4; the others ("x") shall not be interpreted
_PRIORITY: Final = 0x0C
_REPEAT: Final = 0x20
_CONFIRM: Final = 0x01


@dataclass(frozen=True, slots=True)
class EMIMessageCode:
    """Message codes of EMI1 or EMI2 - KNX v01.04.02 - External Message Interface 03.06.03 - §2, Table 1."""

    l_data_req: int
    l_data_con: int
    l_data_ind: int
    l_busmon_ind: int
    pc_set_value_req: int
    pc_get_value_req: int
    pc_get_value_con: int


MESSAGE_CODES: Final = {
    EMIID.EMI1: EMIMessageCode(
        l_data_req=0x11,
        l_data_con=0x4E,
        l_data_ind=0x49,
        l_busmon_ind=0x49,
        pc_set_value_req=0x46,
        pc_get_value_req=0x4C,
        pc_get_value_con=0x4B,
    ),
    EMIID.EMI2: EMIMessageCode(
        l_data_req=0x11,
        l_data_con=0x2E,
        l_data_ind=0x29,
        l_busmon_ind=0x2B,
        pc_set_value_req=0xA6,
        pc_get_value_req=0xAC,
        pc_get_value_con=0xAB,
    ),
}

# EMI2 PEI_Switch.req - KNX v01.04.02 - External Message Interface 03.06.03 - §3.1.4
PEI_SWITCH_REQ: Final = 0xA9
# EMI2 PEI_Identify.req/.con - KNX v01.04.02 - External Message Interface 03.06.03 -
# §3.3.9.5, §3.3.9.6, Table 1
PEI_IDENTIFY_REQ: Final = 0xA7
PEI_IDENTIFY_CON: Final = 0xA8
# memory location "system status" - KNX v01.04.02 - External Message Interface
# 03.06.03 - §3.1.3; KNX v01.10.01 - Resources 03.05.01 - §4.26.3.2
SYSTEM_STATUS_ADDRESS: Final = 0x0060
# the local Device Descriptor Type 0 of a BCU 1 or BCU 2 - KNX v01.03.04 - Basic and
# System Components - Couplers 09.03 - §3.5.3.3.3
DEVICE_DESCRIPTOR_ADDRESS: Final = 0x004E
# the individual address: the first entry of the group address table at 0116h -
# KNX v01.10.01 - Resources 03.05.01 - §4.16.3.1, §4.16.3.2
INDIVIDUAL_ADDRESS_ADDRESS: Final = 0x0117


class EMILayer(Enum):
    """The layer an EMI interface gives access to."""

    NORMAL = "normal"
    DATA_LINK_LAYER = "data_link_layer"
    BUSMONITOR = "busmonitor"


# bits of the "system status" - KNX v01.04.02 - External Message Interface 03.06.03 -
# §3.1.3, Figure 1
_STATUS_APPLICATION_LAYER: Final = 0x08
_STATUS_TRANSPORT_LAYER: Final = 0x04
# set: busmonitor mode disabled
_STATUS_NO_BUSMONITOR: Final = 0x02
_OWN_STACK: Final = (
    _STATUS_APPLICATION_LAYER | _STATUS_TRANSPORT_LAYER | _STATUS_NO_BUSMONITOR
)

# the examples of Figure 1
SYSTEM_STATUS: Final = {
    EMILayer.DATA_LINK_LAYER: 0x12,
    EMILayer.BUSMONITOR: 0x90,
}
# written to the "system status" to restart the device into its default -
# DMP_Restart_LEmi1, KNX v02.01.02 - Management Procedures 03.05.02 - §3.7.4
RESTART_SYSTEM_STATUS: Final = 0xC0


def restorable_system_status(status: int | None) -> int | None:
    """
    Return the "system status" read before switching, if the interface can go back to it.

    None when it wasn't read, or when it gives an external user access to a layer
    below the application layer or to the busmonitor (left so by a client that
    didn't switch back, e.g. Figure 1's data link layer 12h): the interface is
    restarted then.
    """
    if status is not None and status & _OWN_STACK == _OWN_STACK:
        return status
    return None


def restart_request(emi: EMIID) -> bytes:
    """
    PC_Set_Value.req restarting the device: C0h to the "system status".

    DMP_Restart_LEmi1 - KNX v02.01.02 - Management Procedures 03.05.02 - §3.7.4. No
    procedure is specified for EMI2; its "system status" is at the same location.
    """
    return pc_set_value(emi, SYSTEM_STATUS_ADDRESS, bytes((RESTART_SYSTEM_STATUS,)))


# EMI2 redirections - KNX v01.04.02 - External Message Interface 03.06.03 - §3.1.4, Figure 2
_REDIRECTIONS: Final = {
    EMILayer.NORMAL: bytes((0x12, 0x34, 0x56, 0x78, 0x9A)),
    EMILayer.DATA_LINK_LAYER: bytes((0x18, 0x34, 0x56, 0x78, 0x0A)),
    EMILayer.BUSMONITOR: bytes((0x18, 0x34, 0x56, 0x78, 0x0A)),
}
# 00h: do not change the "system status"
SYSTEM_STATUS_UNCHANGED: Final = 0x00


def pei_switch(layer: EMILayer, system_status: int | None = None) -> bytes:
    """
    EMI2 PEI_Switch.req to give access to a layer - KNX v01.04.02 - External Message Interface 03.06.03 - §3.1.4.

    Without `system_status` the one of Figure 2 is used: busmonitor 90h, else 00h
    (unchanged).
    """
    if system_status is None:
        system_status = (
            SYSTEM_STATUS[EMILayer.BUSMONITOR]
            if layer is EMILayer.BUSMONITOR
            else SYSTEM_STATUS_UNCHANGED
        )
    return bytes((PEI_SWITCH_REQ, system_status)) + _REDIRECTIONS[layer]


def pc_set_value(emi: EMIID, address: int, data: bytes) -> bytes:
    """PC_Set_Value.req - KNX v01.04.02 - External Message Interface 03.06.03 - §3.3.9.2."""
    return (
        bytes((MESSAGE_CODES[emi].pc_set_value_req, len(data)))
        + address.to_bytes(2, "big")
        + data
    )


def pc_get_value(emi: EMIID, address: int, length: int) -> bytes:
    """PC_Get_Value.req - KNX v01.04.02 - External Message Interface 03.06.03 - §3.3.9.3."""
    return bytes((MESSAGE_CODES[emi].pc_get_value_req, length)) + address.to_bytes(
        2, "big"
    )


def parse_pc_get_value_con(emi: EMIID, raw: bytes) -> tuple[int, bytes] | None:
    """
    Address and data of a PC_Get_Value.con; None for another message.

    KNX v01.04.02 - External Message Interface 03.06.03 - §3.3.9.4
    """
    if len(raw) < 4 or raw[0] != MESSAGE_CODES[emi].pc_get_value_con:
        return None
    return int.from_bytes(raw[2:4], "big"), raw[4 : 4 + raw[1]]


def parse_pei_identify_con(raw: bytes) -> int | None:
    """
    Return the individual address of an EMI2 PEI_Identify.con; None for another message.

    KNX v01.04.02 - External Message Interface 03.06.03 - §3.3.9.6: individual
    address, then KNX serial number.
    """
    if len(raw) < 3 or raw[0] != PEI_IDENTIFY_CON:
        return None
    return int.from_bytes(raw[1:3], "big")


def l_data_req_from_cemi(emi: EMIID, raw_cemi: bytes) -> bytes:
    """
    Convert a cEMI L_Data.req to EMI1/EMI2 - KNX v01.04.02 - External Message Interface 03.06.03 - §3.3.4.2.

    The interface puts in its own source address. Raise ConversionError for
    anything else than a standard frame L_Data.req.
    """
    if len(raw_cemi) < 2 or raw_cemi[0] != CEMIMessageCode.L_DATA_REQ.value:
        raise ConversionError(
            f"Only L_Data.req can be sent to an EMI1/EMI2 interface: {raw_cemi.hex()}"
        )
    service = raw_cemi[2 + raw_cemi[1] :]
    if len(service) < 8:
        raise ConversionError(f"Invalid cEMI L_Data.req: {raw_cemi.hex()}")
    control_1, control_2 = service[0], service[1]
    length = service[6]
    if not control_1 & _CEMI_STANDARD_FRAME or length > MAX_APDU_LENGTH:
        raise ConversionError(
            "EMI1/EMI2 interfaces send standard frames only (APDU of up to 15 "
            "octets); most Data Secure telegrams need an extended frame"
        )
    # priority; the acknowledge is left to the data link layer ("don't care")
    control = control_1 & _PRIORITY
    npci = (control_2 & 0xF0) | length
    return (
        bytes((MESSAGE_CODES[emi].l_data_req, control, 0x00, 0x00))
        + service[4:6]
        + bytes((npci,))
        + service[7:]
    )


def to_cemi(
    emi: EMIID, raw: bytes, *, busmonitor: bool, own_address: int = 0
) -> bytes | None:
    """
    Convert an L_Data.con, L_Data.ind or L_Busmon.ind of an EMI1/EMI2 interface to cEMI.

    Return None for other messages. EMI1 uses the same message code for L_Data.ind
    and L_Busmon.ind, so `busmonitor` tells which one is received. The source of an
    L_Data.con is unused in EMI1/EMI2 - the interface's `own_address` is put in, as
    it sends with that one.
    """
    if not raw:
        return None
    codes = MESSAGE_CODES[emi]
    code = raw[0]
    if busmonitor and code == codes.l_busmon_ind:
        # status, time stamp, raw frame - KNX v01.04.02 - External Message Interface
        # 03.06.03 - §3.3.3.2
        if len(raw) < 4:
            return None
        return (
            bytes(
                (
                    CEMIMessageCode.L_BUSMON_IND.value,
                    7,
                    _CEMI_BUSMONITOR_STATUS_INFO,
                    1,
                    raw[1],
                    _CEMI_TIMESTAMP_RELATIVE,
                    2,
                )
            )
            + raw[2:4]
            + raw[4:]
        )
    # control, source (unused in L_Data.con), destination, AT/NPCI/LG, TPDU -
    # KNX v01.04.02 - External Message Interface 03.06.03 - §3.3.4.3, §3.3.4.4
    if len(raw) < 8:
        return None
    control, npci = raw[1], raw[6]
    if code == codes.l_data_con:
        cemi_code = CEMIMessageCode.L_DATA_CON.value
        control_1 = (
            _CEMI_STANDARD_FRAME
            | _CEMI_BROADCAST
            | (control & (_REPEAT | _PRIORITY | _CONFIRM))
        )
        source = own_address.to_bytes(2, "big")
    elif code == codes.l_data_ind and not busmonitor:
        cemi_code = CEMIMessageCode.L_DATA_IND.value
        control_1 = (
            _CEMI_STANDARD_FRAME
            | _CEMI_NOT_REPEATED
            | _CEMI_BROADCAST
            | (control & _PRIORITY)
        )
        source = raw[2:4]
    else:
        return None
    return (
        bytes((cemi_code, 0x00, control_1, npci & 0xF0))
        + source
        + raw[4:6]
        + bytes((npci & 0x0F,))
        + raw[7:]
    )
