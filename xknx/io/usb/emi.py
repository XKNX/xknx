"""
EMI1 and EMI2 messages of KNX USB interfaces without cEMI.

xknx works with cEMI frames, so the data link layer messages of an EMI1 or EMI2
interface are converted: L_Data.req from cEMI, L_Data.con, L_Data.ind and
L_Busmon.ind to cEMI. Only standard frames exist in EMI1 and EMI2.
KNX v01.04.02 - External Message Interface 03.06.03 - §3
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from xknx.exceptions import ConversionError

from .const import EMIID

_CEMI_L_DATA_REQ: Final = 0x11
_CEMI_L_DATA_CON: Final = 0x2E
_CEMI_L_DATA_IND: Final = 0x29
_CEMI_L_BUSMON_IND: Final = 0x2B
# cEMI additional information types - KNX v01.04.02 - External Message Interface 03.06.03 - §4.1.4.3
_CEMI_BUSMONITOR_STATUS_INFO: Final = 0x03
_CEMI_TIMESTAMP_RELATIVE: Final = 0x04
# the longest APDU of a standard frame
MAX_APDU_LENGTH: Final = 15


class EMIMessageCode:
    """Message codes of EMI1 and EMI2 - KNX v01.04.02 - External Message Interface 03.06.03 - §2, Table 1."""

    def __init__(
        self,
        *,
        l_data_con: int,
        l_data_ind: int,
        l_busmon_ind: int,
        pc_set_value_req: int,
        pc_get_value_req: int,
        pc_get_value_con: int,
    ) -> None:
        """Initialize EMIMessageCode."""
        self.l_data_req = _CEMI_L_DATA_REQ
        self.l_data_con = l_data_con
        self.l_data_ind = l_data_ind
        self.l_busmon_ind = l_busmon_ind
        self.pc_set_value_req = pc_set_value_req
        self.pc_get_value_req = pc_get_value_req
        self.pc_get_value_con = pc_get_value_con


MESSAGE_CODES: Final = {
    EMIID.EMI1: EMIMessageCode(
        l_data_con=0x4E,
        l_data_ind=0x49,
        l_busmon_ind=0x49,
        pc_set_value_req=0x46,
        pc_get_value_req=0x4C,
        pc_get_value_con=0x4B,
    ),
    EMIID.EMI2: EMIMessageCode(
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
# memory location "system status" of EMI1 - KNX v01.04.02 - External Message Interface
# 03.06.03 - §3.1.3; KNX v01.10.01 - Resources 03.05.01 - §4.26.3.2
SYSTEM_STATUS_ADDRESS: Final = 0x0060
# the individual address: the first entry of the group address table at 0116h -
# KNX v01.10.01 - Resources 03.05.01 - §4.16.3.1, §4.16.3.2
INDIVIDUAL_ADDRESS_ADDRESS: Final = 0x0117


class EMILayer(Enum):
    """The layer an EMI interface gives access to."""

    NORMAL = "normal"
    DATA_LINK_LAYER = "data_link_layer"
    BUSMONITOR = "busmonitor"


# EMI1 "system status" values - KNX v01.04.02 - External Message Interface 03.06.03 - §3.1.3
SYSTEM_STATUS: Final = {
    EMILayer.NORMAL: 0x1E,
    EMILayer.DATA_LINK_LAYER: 0x12,
    EMILayer.BUSMONITOR: 0x90,
}
# EMI2 system status and redirections - KNX v01.04.02 - External Message Interface
# 03.06.03 - §3.1.4, Figure 2. Normal mode writes the system status 1Eh (all layers and
# the user program enabled) instead of 00h (unchanged), so a bus monitor mode is left too.
_PEI_SWITCH: Final = {
    EMILayer.NORMAL: bytes((0x1E, 0x12, 0x34, 0x56, 0x78, 0x9A)),
    EMILayer.DATA_LINK_LAYER: bytes((0x00, 0x18, 0x34, 0x56, 0x78, 0x0A)),
    EMILayer.BUSMONITOR: bytes((0x90, 0x18, 0x34, 0x56, 0x78, 0x0A)),
}


def pei_switch(layer: EMILayer) -> bytes:
    """EMI2 PEI_Switch.req to give access to a layer."""
    return bytes((PEI_SWITCH_REQ,)) + _PEI_SWITCH[layer]


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


def l_data_req_from_cemi(raw_cemi: bytes) -> bytes:
    """
    Convert a cEMI L_Data.req to EMI1/EMI2 - KNX v01.04.02 - External Message Interface 03.06.03 - §3.3.4.2.

    The interface puts in its own source address. Raise ConversionError for
    anything else than a standard frame L_Data.req.
    """
    if len(raw_cemi) < 2 or raw_cemi[0] != _CEMI_L_DATA_REQ:
        raise ConversionError(
            f"Only L_Data.req can be sent to an EMI1/EMI2 interface: {raw_cemi.hex()}"
        )
    service = raw_cemi[2 + raw_cemi[1] :]
    if len(service) < 8:
        raise ConversionError(f"Invalid cEMI L_Data.req: {raw_cemi.hex()}")
    control_1, control_2 = service[0], service[1]
    length = service[6]
    if not control_1 & 0x80 or length > MAX_APDU_LENGTH:
        raise ConversionError(
            "EMI1/EMI2 interfaces send standard frames only (APDU of up to 15 octets)"
        )
    # priority; the acknowledge is left to the data link layer ("don't care")
    control = control_1 & 0x0C
    npci = (control_2 & 0xF0) | length
    return (
        bytes((_CEMI_L_DATA_REQ, control, 0x00, 0x00))
        + service[4:6]
        + bytes((npci,))
        + service[7:]
    )


def to_cemi(emi: EMIID, raw: bytes, busmonitor: bool) -> bytes | None:
    """
    Convert an L_Data.con, L_Data.ind or L_Busmon.ind of an EMI1/EMI2 interface to cEMI.

    Return None for other messages. EMI1 uses the same message code for L_Data.ind
    and L_Busmon.ind, so `busmonitor` tells which one is received.
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
                    _CEMI_L_BUSMON_IND,
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
    if code == codes.l_data_con:
        cemi_code = _CEMI_L_DATA_CON
    elif code == codes.l_data_ind and not busmonitor:
        cemi_code = _CEMI_L_DATA_IND
    else:
        return None
    # control, source, destination, AT/NPCI/LG, TPDU - KNX v01.04.02 - External
    # Message Interface 03.06.03 - §3.3.4.3, §3.3.4.4
    if len(raw) < 8:
        return None
    control, npci = raw[1], raw[6]
    return (
        bytes((cemi_code, 0x00, control, npci & 0xF0))
        + raw[2:6]
        + bytes((npci & 0x0F,))
        + raw[7:]
    )
