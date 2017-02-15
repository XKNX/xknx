from enum import Enum

class ErrorCode(Enum):
    # The connection state is normal.
    E_NO_ERROR = 0x00

    # The KNXnet/IP Server device cannot find an active data
    # connection with the specified ID.
    E_CONNECTION_ID = 0x21

    # The KNXnet/IP Server device detects an error concerning
    # the data connection with the specified ID.
    E_DATA_CONNECTION = 0x26

    # The KNXnet/IP Server device detects an error concerning
    # the KNX subnetwork connection with the specified ID.
    E_KNX_CONNECTION = 0x27

    # The requested tunnelling layer is not supported by the
    # KNXnet/IP Server device.
    E_TUNNELLING_LAYER = 0x29

    # Unclear error, looks like device has no free channels
    E_NO_FREE_CHANNEL = 0x25
