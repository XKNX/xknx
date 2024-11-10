"""Enums for KNX Application Layer."""

from enum import Enum


class ReturnCode(Enum):
    """Enum class for Generic device management Return Codes."""

    ## Basic positive Return Code
    # The service, function or command is executed successfully, without additional information.
    E_SUCCESS = 0x00
    ## Generic negative Return Codes
    # Memory cannot be accessed or only with fault(s).
    E_MEMORY_ERROR = 0xF1
    # Requested data will not fit into a Frame supported by this server.
    # This shall be used for Device limitations of the maximum supported Frame length
    # by accessing resources (Properties, Function Properties, memory…) of the device.
    E_LENGTH_EXCEEDS_MAX_APDU_LENGTH = 0xF4
    # Writing data beyond what is reserved for the addressed Resource.
    E_DATA_OVERFLOW = 0xF5
    # Write value too low. Preferable to give this instead of “Value not supported”.
    E_DATA_MIN = 0xF6
    # Write value too high. Preferable to give this instead of “Value not supported”.
    E_DATA_MAX = 0xF7
    # The service or function is supported, but request data is not valid for this receiver.
    E_DATA_VOID = 0xF8
    # Data could generally be written, but not possible at this time.
    E_TEMPORARILY_NOT_AVAILABLE = 0xF9
    # Read access attempted to a “write only” service or Resource.
    E_ACCESS_WRITE_ONLY = 0xFA
    # Write access attempted to a “read only” service or Resource.
    E_ACCESS_READ_ONLY = 0xFB
    # Access denied due to authorization reasons. A_Authorize as well as KNX Security
    E_ACCESS_DENIED = 0xFC
    # Interface Object or Property is not present, or index is out of range.
    E_ADDRESS_VOID = 0xFD
    # Write access with a wrong datatype (Datapoint length).
    E_DATA_TYPE_CONFLICT = 0xFE
    # The service, function or command has failed without a closer indication of the problem.
    E_ERROR = 0xFF
    ## Generic positive Return Codes
    # (01h-1Fh - None proposed)
    ## Specific positive Return Codes
    # (20h-5Fh - None proposed)
    ## Specific negative Return Codes
    # (A0h-DFh - None proposed)
