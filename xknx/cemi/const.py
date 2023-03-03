"""Constants for CEMI."""
from enum import Enum, IntEnum


class CEMIMessageCode(Enum):
    """Enum class for CEMI Message Codes."""

    # pylint disable=line-too-long

    # FROM NETWORK LAYER TO DATA LINK LAYER
    L_RAW_REQ = 0x10
    L_DATA_REQ = 0x11  # Data Service.
    # Primitive used for transmitting a data frame
    L_POLL_DATA_REQ = 0x13  # Poll Data Service

    # FROM DATA LINK LAYER TO NETWORK LAYER
    L_POLL_DATA_CON = 0x25  # Poll Data Service
    L_DATA_IND = 0x29  # Data Service.
    # Primitive used for receiving a data frame
    L_BUSMON_IND = 0x2B  # Bus Monitor Service
    L_RAW_IND = 0x2D
    L_DATA_CON = 0x2E  # Data Service.
    # Primitive used for local confirmation
    # that a frame was sent
    # (does not indicate a successful receive though)
    L_RAW_CON = 0x2F

    # Management Configuration message types
    M_PROP_READ_REQ = 0xFC  # Read Property Request
    M_PROP_READ_CON = 0xFB  # Read Property Confirmation
    M_PROP_WRITE_REQ = 0xF6  # Write Property Request
    M_PROP_WRITE_CON = 0xF5  # Write Property Confirmation
    M_PROP_INFO_IND = 0xF7  # Property Indication
    M_FUNC_PROP_COMMAND_REQ = 0xF8  # Call Property Function
    M_FUNC_PROP_STATE_READ_REQ = 0xF9  # Read status of Property Function
    M_FUNC_PROP_COMMAND_CON = 0xFA  # Property Function Confirmation
    M_FUNC_PROP_STATE_READ_CON = 0xFA  # Read status of Property Function Confirmation
    M_RESET_REQ = 0xF1  # Reset Request
    M_RESET_IND = 0xF0  # Reset confirmation


class CEMIFlags:
    """Enum class for CEMI Flags."""

    # Bit 1/7
    FRAME_TYPE_EXTENDED = 0x0000
    FRAME_TYPE_STANDARD = 0x8000

    # Bit 1/6 - Reserved

    # Bit 1/5
    # Repeat in case of an error
    REPEAT = 0x0000
    DO_NOT_REPEAT = 0x2000

    # Bit 1/4
    SYSTEM_BROADCAST = 0x0000
    BROADCAST = 0x1000

    # Bit 1/3+2
    PRIORITY_SYSTEM = 0x0000
    PRIORITY_NORMAL = 0x0400
    PRIORITY_URGENT = 0x0800
    PRIORITY_LOW = 0x0C00

    # Bit 1/1
    NO_ACK_REQUESTED = 0x0000
    ACK_REQUESTED = 0x0200

    # Bit 1/0
    CONFIRM_NO_ERROR = 0x0000
    CONFIRM_ERROR = 0x0100

    # Bit 0/7
    DESTINATION_INDIVIDUAL_ADDRESS = 0x0000
    DESTINATION_GROUP_ADDRESS = 0x0080

    # Bit 0/6+5+4
    HOP_COUNT_NO = 0x0070
    HOP_COUNT_1ST = 0x0060

    # Bit 0/3+2+1+0
    STANDARD_FRAME_FORMAT = 0x0000
    EXTENDED_FRAME_FORMAT = 0x0001


class CEMIErrorCode(IntEnum):
    """Enum class for CEMI Error Codes."""

    CEMI_ERROR_UNSPECIFIED = 0x00
    CEMI_ERROR_OUT_OF_RANGE = 0x01
    CEMI_ERROR_OUT_OF_MAX_RANGE = 0x02
    CEMI_ERROR_OUT_OF_MIN_RANGE = 0x03
    CEMI_ERROR_MEMORY = 0x04
    CEMI_ERROR_READ_ONLY = 0x05
    CEMI_ERROR_ILLEGAL_COMMAND = 0x06
    CEMI_ERROR_VOID_DP = 0x07
    CEMI_ERROR_TYPE_CONFLICT = 0x08
    CEMI_ERROR_PROP_INDEX_RANGE = 0x09
    CEMI_ERROR_TEMPORARILY_READ_ONLY = 0x0A

    def __repr__(self) -> str:
        """Return object as readable string."""
        return str(self.value)
