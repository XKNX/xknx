"""Module for KNX/IP Error codes."""
from enum import Enum


class ErrorCode(Enum):
    """Enum class for KNX/IP error codes."""

    # The connection state is normal.
    E_NO_ERROR = 0x00

    # requested host protocol is not supported
    E_HOST_PROTOCOL_TYPE = 0x01

    # requested protocol version is not supported
    E_VERSION_NOT_SUPPORTED = 0x02

    # received sequence number is out of order.
    E_SEQUENCE_NUMBER = 0x04

    # The KNXnet/IP Server device cannot find an active data
    # connection with the specified ID.
    E_CONNECTION_ID = 0x21

    # The requested connection type is not supported
    E_CONNECTION_TYPE = 0x22

    # One or more requested connection options are not supported
    E_CONNECTION_OPTION = 0x23

    # The KNXnet/IP Server device cannot accept the new data connection
    # because its maximum amount of concurrent connections is already
    # occupied.
    E_NO_MORE_CONNECTIONS = 0x24

    # KNXnet/IP Tunnelling device does not accept connection because the
    # Individual Address is used multiple times
    E_NO_MORE_UNIQUE_CONNECTIONS = 0x25

    # The KNXnet/IP Server device detects an error concerning
    # the data connection with the specified ID.
    E_DATA_CONNECTION = 0x26

    # The KNXnet/IP Server device detects an error concerning
    # the KNX subnetwork connection with the specified ID.
    E_KNX_CONNECTION = 0x27

    # The requested tunnelling layer is not supported by the
    # KNXnet/IP Server device.
    E_TUNNELLING_LAYER = 0x29
