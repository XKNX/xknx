"""
KNX RF through a KNX USB RF interface (mask 2311h).

The medium of an interface is the one of its mask version (Device Descriptor Type 0) -
KNX v02.01.01 - Configuration Procedures 03.05.03 - §3.13.2.2. On KNX RF every cEMI
L_Data frame carries the RF medium information. A frame is sent with this information
left void: the interface then inserts its own Domain Address (or its own KNX Serial
Number for a system broadcast) and its own frame number - KNX v01.04.02 - External
Message Interface 03.06.03 - §4.1.4.3.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from xknx.cemi import CEMIMessageCode
from xknx.knxip.knxip_enum import KNXMedium

# cEMI additional information type "RF medium information" and its length
RF_MEDIUM_INFO_TYPE = 0x02
RF_MEDIUM_INFO_LENGTH = 8
# KNX Serial Number / Domain Address: void, the interface inserts its own
VOID_SERIAL_NUMBER_OR_DOMAIN_ADDRESS = bytes(6)
# Data Link Layer frame number: void, the interface inserts its own
VOID_FRAME_NUMBER = 0xFF

# the Medium Type digit of a mask version - KNX v01.10.01 - Resources 03.05.01 - §4.1.2.1
_MASK_MEDIA = {
    0x0: KNXMedium.TP1,
    0x1: KNXMedium.PL110,
    0x2: KNXMedium.RF,
    0x5: KNXMedium.KNX_IP,
}
_L_DATA_CODES = frozenset(
    {
        CEMIMessageCode.L_DATA_REQ.value,
        CEMIMessageCode.L_DATA_CON.value,
        CEMIMessageCode.L_DATA_IND.value,
    }
)


class RFSignalStrength(IntEnum):
    """Received signal strength of an RF frame."""

    VOID = 0b00
    WEAK = 0b01
    MEDIUM = 0b10
    STRONG = 0b11


@dataclass(frozen=True, slots=True)
class RFMediumInfo:
    """
    RF medium information of a cEMI L_Data frame - KNX v01.04.02 - External Message Interface 03.06.03 - §4.1.4.3.2.

    `serial_number_or_domain_address` is the sender's KNX Serial Number when the
    frame is a system broadcast (the cEMI "system broadcast" flag is 0) and the
    Domain Address otherwise. `signal_strength` is measured by the interface on
    reception, `retransmitter_signal_strength` the lowest one a retransmitter saw.
    """

    serial_number_or_domain_address: bytes = VOID_SERIAL_NUMBER_OR_DOMAIN_ADDRESS
    frame_number: int = VOID_FRAME_NUMBER
    route_last: bool = False
    signal_strength: RFSignalStrength = RFSignalStrength.VOID
    retransmitter_signal_strength: RFSignalStrength = RFSignalStrength.VOID
    battery_ok: bool = True
    unidirectional: bool = False

    @classmethod
    def from_knx(cls, data: bytes) -> RFMediumInfo:
        """Parse the 8 octets of the information (without type and length)."""
        if len(data) != RF_MEDIUM_INFO_LENGTH:
            raise ValueError(f"RF medium information has 8 octets, not {len(data)}")
        info = data[0]
        return cls(
            serial_number_or_domain_address=bytes(data[1:7]),
            frame_number=data[7],
            route_last=bool(info & 0x80),
            signal_strength=RFSignalStrength((info >> 4) & 0x03),
            retransmitter_signal_strength=RFSignalStrength((info >> 2) & 0x03),
            battery_ok=bool(info & 0x02),
            unidirectional=bool(info & 0x01),
        )

    def to_knx(self) -> bytes:
        """Serialize with type and length, as additional information of a cEMI frame."""
        info = (
            (0x80 if self.route_last else 0)
            | self.signal_strength << 4
            | self.retransmitter_signal_strength << 2
            | (0x02 if self.battery_ok else 0)
            | (0x01 if self.unidirectional else 0)
        )
        return (
            bytes((RF_MEDIUM_INFO_TYPE, RF_MEDIUM_INFO_LENGTH, info))
            + self.serial_number_or_domain_address
            + bytes((self.frame_number,))
        )


def medium_of_mask_version(mask_version: int | None) -> KNXMedium:
    """Return the medium of a mask version; TP1 when it is unknown."""
    if mask_version is None:
        return KNXMedium.TP1
    return _MASK_MEDIA.get((mask_version >> 12) & 0x0F, KNXMedium.TP1)


def _additional_info(raw_cemi: bytes) -> list[tuple[int, bytes]] | None:
    """Return the additional information of a cEMI L_Data frame; None for other frames."""
    if len(raw_cemi) < 2 or raw_cemi[0] not in _L_DATA_CODES:
        return None
    end = 2 + raw_cemi[1]
    if len(raw_cemi) < end:
        return None
    entries: list[tuple[int, bytes]] = []
    position = 2
    while position + 2 <= end:
        length = raw_cemi[position + 1]
        data = raw_cemi[position + 2 : position + 2 + length]
        if len(data) != length or position + 2 + length > end:
            return None
        entries.append((raw_cemi[position], data))
        position += 2 + length
    return entries


def rf_medium_info(raw_cemi: bytes) -> RFMediumInfo | None:
    """Return the RF medium information of a cEMI L_Data frame; None without one."""
    for info_type, data in _additional_info(raw_cemi) or ():
        if info_type == RF_MEDIUM_INFO_TYPE and len(data) == RF_MEDIUM_INFO_LENGTH:
            return RFMediumInfo.from_knx(data)
    return None


def with_rf_medium_info(raw_cemi: bytes) -> bytes:
    """
    Return a cEMI L_Data.req with RF medium information.

    A frame that already has one is returned as it is; otherwise a void one is
    added: the interface inserts its own Domain Address (KNX Serial Number for a
    system broadcast) and frame number, the sender's battery is ok and it is
    bidirectional.
    """
    if not raw_cemi or raw_cemi[0] != CEMIMessageCode.L_DATA_REQ.value:
        return raw_cemi
    entries = _additional_info(raw_cemi)
    if entries is None or any(kind == RF_MEDIUM_INFO_TYPE for kind, _ in entries):
        return raw_cemi
    info_length = raw_cemi[1]
    addition = RFMediumInfo().to_knx()
    return (
        bytes((raw_cemi[0], info_length + len(addition)))
        + raw_cemi[2 : 2 + info_length]
        + addition
        + raw_cemi[2 + info_length :]
    )
