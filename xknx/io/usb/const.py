"""Constants of the KNX USB HID transfer protocol."""

from __future__ import annotations

from enum import IntEnum, IntFlag
from typing import Final

# KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.4.1.2.1
REPORT_ID: Final = 0x01
# a HID report is 64 octets: report id, packet info, data length and 61 data octets
HID_REPORT_LENGTH: Final = 64
HID_REPORT_HEADER_LENGTH: Final = 3
MAX_REPORT_DATA_LENGTH: Final = HID_REPORT_LENGTH - HID_REPORT_HEADER_LENGTH
# KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.4.1.2.2
MAX_SEQUENCE_NUMBER: Final = 5
# KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.4.1.3
PROTOCOL_VERSION: Final = 0x00
TRANSFER_HEADER_LENGTH: Final = 8

# KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.2.1
DEVICE_FEATURE_GET_TIMEOUT: Final = 1.0

# Device Descriptor Type 0 (mask version) of the stand-alone USB interfaces whose own
# individual address is in the cEMI Server Object (PID_CEMI_SERVER_SNA,
# PID_CEMI_SERVER_DEVICE_ADDRESS) - KNX v02.01.01 - Configuration Procedures 03.05.03 -
# §3.13.2.1 Table 6, §3.13.3.2: USB TP1 Interface 1.1 and USB RF Interface 1.1
CEMI_SERVER_ADDRESS_MASKS: Final = frozenset({0x0310, 0x2311})
# Device Descriptor Type 0 of the BCU 1 and BCU 2 masks whose individual address is
# the first entry of the group address table at 0116h - KNX v01.10.01 - Resources
# 03.05.01 - §4.16.3
BCU_ADDRESS_MASKS: Final = frozenset({0x0010, 0x0011, 0x0012, 0x0020, 0x0021})


class PacketType(IntEnum):
    """Packet type of a HID report - KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.4.1.2.3."""

    START_AND_END = 0x03
    PARTIAL = 0x04
    START_AND_PARTIAL = 0x05
    PARTIAL_AND_END = 0x06


class ProtocolID(IntEnum):
    """Protocol of a KNX USB transfer frame - KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.4.1.3.4."""

    KNX_TUNNEL = 0x01
    M_BUS_TUNNEL = 0x02
    BATIBUS_TUNNEL = 0x03
    BUS_ACCESS_SERVER_FEATURE = 0x0F


class EMIID(IntEnum):
    """EMI format of a KNX tunnel frame - KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.4.1.3.4."""

    EMI1 = 0x01
    EMI2 = 0x02
    CEMI = 0x03


class DeviceFeatureService(IntEnum):
    """Device feature service - KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.2.1."""

    GET = 0x01
    RESPONSE = 0x02
    SET = 0x03
    INFO = 0x04


class DeviceFeature(IntEnum):
    """Device feature of the bus access server - KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.3."""

    SUPPORTED_EMI_TYPE = 0x01
    DEVICE_DESCRIPTOR_TYPE_0 = 0x02
    BUS_CONNECTION_STATUS = 0x03
    MANUFACTURER_CODE = 0x04
    ACTIVE_EMI_TYPE = 0x05


class SupportedEMIType(IntFlag):
    """Bits of the feature "Supported EMI type" - KNX v01.03.04 - Basic and System Components - Couplers 09.03 - §3.5.3.3.2."""

    EMI1 = 0x0001
    EMI2 = 0x0002
    CEMI = 0x0004


class CommunicationMode(IntEnum):
    """Values of PID_COMM_MODE of the cEMI server - KNX v01.04.02 - External Message Interface 03.06.03 - §4.2.2.4.2."""

    DATA_LINK_LAYER = 0x00
    DATA_LINK_LAYER_BUSMONITOR = 0x01
    DATA_LINK_LAYER_RAW = 0x02
    CEMI_TRANSPORT_LAYER = 0x06
    NO_LAYER = 0xFF
