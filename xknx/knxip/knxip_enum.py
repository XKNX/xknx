"""Module for KNX/IP Enum classes."""

from enum import Enum


class KNXIPServiceType(Enum):
    """Enum class for KNX/IP Service Types."""

    # 0x02 Core services
    SEARCH_REQUEST = 0x0201
    SEARCH_RESPONSE = 0x0202
    DESCRIPTION_REQUEST = 0x0203
    DESCRIPTION_RESPONSE = 0x0204
    CONNECT_REQUEST = 0x0205
    CONNECT_RESPONSE = 0x0206
    CONNECTIONSTATE_REQUEST = 0x0207
    CONNECTIONSTATE_RESPONSE = 0x0208
    DISCONNECT_REQUEST = 0x0209
    DISCONNECT_RESPONSE = 0x020A
    SEARCH_REQUEST_EXTENDED = 0x020B
    SEARCH_RESPONSE_EXTENDED = 0x020C
    # 0x03 Device Management services
    DEVICE_CONFIGURATION_REQUEST = 0x0310
    DEVICE_CONFIGURATION_ACK = 0x0311
    # 0x04 Tunneling services
    TUNNELLING_REQUEST = 0x0420
    TUNNELLING_ACK = 0x0421
    TUNNELLING_FEATURE_GET = 0x0422
    TUNNELLING_FEATURE_RESPONSE = 0x0423
    TUNNELLING_FEATURE_SET = 0x0424
    TUNNELLING_FEATURE_INFO = 0x0425
    # 0x05 Routing services
    ROUTING_INDICATION = 0x0530
    ROUTING_LOST_MESSAGE = 0x0531
    ROUTING_BUSY = 0x0532
    ROUTING_SYSTEM_BROADCAST = 0x0533
    # 0x06 Remote Logging services
    # 0x07 Remote Configuration and Diagnosis services
    REMOTE_DIAG_REQUEST = 0x0740
    REMOTE_DIAG_RESPONSE = 0x0741
    REMOTE_CONFIG_REQUEST = 0x0742
    REMOTE_RESET_REQUEST = 0x0743
    # 0x08 Object Server services
    # 0x09 Security services
    SECURE_WRAPPER = 0x0950
    SESSION_REQUEST = 0x0951
    SESSION_RESPONSE = 0x0952
    SESSION_AUTHENTICATE = 0x0953
    SESSION_STATUS = 0x0954
    TIMER_NOTIFY = 0x0955


class CEMIMessageCode(Enum):
    """Enum class for KNX/IP CEMI Message Codes."""

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


class CEMIFlags:
    """Enum class for KNX/IP CEMI Flags."""

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


class ConnectRequestType(Enum):
    """Enum class for KNX/IP Connect Rquest Typess."""

    # Data connection used to configure a KNXnet/IP device
    DEVICE_MGMT_CONNECTION = 0x03

    # Data connection used to forward KNX telegrams between
    # two KNXnet/IP devices.
    TUNNEL_CONNECTION = 0x04

    # Data connection used for configuration and data transfer
    # with a remote logging server.
    REMLOG_CONNECTION = 0x06

    # Data connection used for data transfer with a remote
    # configuration server.
    REMCONF_CONNECTION = 0x07

    # Data connection used for configuration and data transfer
    # with an Object Server in a KNXnet/IP device.
    OBJSVR_CONNECTION = 0x08


class DIBTypeCode(Enum):
    """Enum class for KNX/IP DIB Type Codes."""

    # Device information e.g. KNX medium.
    DEVICE_INFO = 0x01

    # Service families supported by the device.
    SUPP_SVC_FAMILIES = 0x02

    # IP configuration
    IP_CONFIG = 0x03

    # current configuration
    IP_CUR_CONFIG = 0x04

    # KNX addresses
    KNX_ADDRESSES = 0x05

    # KNX IP Secure
    SECURED_SERVICE_FAMILIES = 0x06
    TUNNELING_INFO = 0x07
    ADDITIONAL_DEVICE_INFO = 0x08

    # DIB structure for further data defined by device manufacturer.
    MFR_DATA = 0xFE


class HostProtocol(Enum):
    """Enum class for host protocol."""

    IPV4_UDP = 0x01
    IPV4_TCP = 0x02


class KNXMedium(Enum):
    """Enum class for KNX Medium."""

    TP1 = 0x02
    PL110 = 0x04
    RF = 0x10
    KNX_IP = 0x20


class DIBServiceFamily(Enum):
    """Enum class for KNX/IP DIB Service Family."""

    #  Core
    CORE = 0x02

    # Device Management
    DEVICE_MANAGEMENT = 0x03

    # Tunnelling
    TUNNELING = 0x04

    # Routing
    ROUTING = 0x05

    # Remote Logging
    REMOTE_LOGGING = 0x06

    # Configuration and Diagnosis
    REMOTE_CONFIGURATION_DIAGNOSIS = 0x07

    # Object Server'.
    OBJECT_SERVER = 0x08

    # Security - Extended search response only
    SECURITY = 0x09


class SecureSessionStatusCode(Enum):
    """Enum class for KNX/IP Secure session status codes."""

    # The user could successfully be authenticated
    STATUS_AUTHENTICATION_SUCCESS = 0x00
    # An error occurred during secure session handshake
    STATUS_AUTHENTICATION_FAILED = 0x01
    # The session is not (yet) authenticated
    STATUS_UNAUTHENTICATED = 0x02
    # A timeout occurred during secure session handshake
    STATUS_TIMEOUT = 0x03
    # Prevent inactivity on the secure session closing it with timeout error
    STATUS_KEEPALIVE = 0x04
    # The secure session shall be closed
    STATUS_CLOSE = 0x05


class SearchRequestParameterType(Enum):
    """Search Request Parameter (SRP) is used to transfer additional information in a KNXnet/IP SEARCH_REQUEST_EXTENDED."""

    # Used to test behavior of the KNXnet/IP server for unknown SRPs. Don't use!
    INVALID = 0x00

    # Select only KNXnet/IP Servers that are currently in programming mode
    SELECT_BY_PROGRAMMING_MODE = 0x01

    # Select only KNXnet/IP Servers that have the given MAC address
    SELECT_BY_MAC_ADDRESS = 0x02

    # Select only KNXnet/IP Servers that support the given DIBServiceFamily in a given version
    SELECT_BY_SERVICE = 0x03

    # The Client shall include this SRP to indicate that it is interested in the listed DIBs
    REQUEST_DIBS = 0x04
