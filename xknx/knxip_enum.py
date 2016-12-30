from enum import Enum



class KNXIPServiceType(Enum):

    SEARCH_REQUEST = 0x0201
    SEARCH_RESPONSE = 0x0202
    DESCRIPTION_REQUEST = 0x0203
    DESCRIPTION_RESPONSE = 0x0204
    CONNECT_REQUEST = 0x0205
    CONNECT_RESPONSE = 0x0206
    CONNECTIONSTATE_REQUEST = 0x0207
    CONNECTIONSTATE_RESPONSE = 0x0208
    DISCONNECT_REQUEST = 0x0209
    DISCONNECT_RESPONSE = 0x020a
    DEVICE_CONFIGURATION_REQUEST = 0x0310
    DEVICE_CONFIGURATION_ACK = 0x0111
    TUNNELING_REQUEST = 0x0420
    TUNNELLING_ACK = 0x0421
    ROUTING_INDICATION = 0x0530
    ROUTING_LOST_MESSAGE = 0x0531
    UNKNOWN = 0x0000


class CEMIMessageCode(Enum):

    # FROM NETWORK LAYER TO DATA LINK LAYER
    L_RAW_REQ       =   0x10
    L_Data_REQ      =   0x11 # Data Service. Primitive used for transmitting a data frame
    L_POLL_DATA_REQ =   0x13 # Poll Data Service

    # FROM DATA LINK LAYER TO NETWORK LAYER
    L_POLL_DATA_CON =   0x25 # Poll Data Service
    L_DATA_IND      =   0x29 # Data Service. Primitive used for receiving a data frame
    L_BUSMON_IND    =   0x2B # Bus Monitor Service
    L_RAW_IND       =   0x2D
    L_DATA_CON      =   0x2E # Data Service. Primitive used for local confirmation that a frame was sent#
                             # (does not indicate a successful receive though)
    L_RAW_CON       =   0x2F


class APCICommand(Enum):

    GROUP_READ     = 0x00
    GROUP_WRITE    = 0x80
    GROUP_RESPONSE = 0x40



class CEMIFlags():

        # Bit 1/7
        FRAME_TYPE_EXTENDED = 0x0000
        FRAME_TYPE_STANDARD = 0x8000

        # Bit 1/6 - Reserved

        # Bit 1/5
        # Repeat in case of an error
        REPEAT        = 0x0000
        DO_NOT_REPEAT = 0x2000

        # Bit 1/4
        SYSTEM_BROADCAST = 0x0000
        BROADCAST        = 0x1000


        # Bit 1/3+2
        PRIORITY_SYSTEM    = 0x0000
        PRIORITY_NORMAL    = 0x0400
        PRIORITY_URGENT    = 0x0800
        PRIORITY_LOW       = 0x0C00

        # Bit 1/1
        NO_ACK_REQUESTED = 0x0000
        ACK_REQUESTED    = 0x0200

        #Bit 1/0
        CONFIRM_NO_ERROR = 0x0000
        CONFIRM_ERROR    = 0x0100

        # Bit 0/7
        DESTINATION_INDIVIDUAL_ADDRESS = 0x0000
        DESTINATION_GROUP_ADDRESS      = 0x0080

        # Bit 0/6+5+4
        HOP_COUNT_NO = 0x0070
        HOP_COUNT_1ST = 0x0060

        # Bit 0/3+2+1+0
        STANDARD_FRAME_FORMAT = 0x0000
        EXTENDED_FRAME_FORMAT = 0x0001

