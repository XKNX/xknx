"""
Shared handling of PDT_CONTROL Function Property responses.

The Load and Run State Machines' control properties (``PID_LOAD_STATE_CONTROL``
and ``PID_RUN_STATE_CONTROL``) are ``PDT_CONTROL``. Accessed through the
extended Function Property services, KNX v02.01.01 - Application Layer
03.03.07 - §3.4.8.4 fixes the response shape: "a positive return code and
the data field shall be a single octet containing the new state ... or a
negative return code, in which case the data field shall be empty."
"""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.telegram import apci

# KNX v02.01.01 - Application Layer 03.03.07 - §3.4.8.3: positive return
# codes are 00h (basic), 01h-1Fh (generic) and 20h-5Fh (specific).
_MAX_POSITIVE_RETURN_CODE = 0x5F


def format_return_code(return_code: apci.ReturnCode | int) -> str:
    """Return a readable name for a return code, which may be outside ReturnCode."""
    if isinstance(return_code, apci.ReturnCode):
        return return_code.name
    return f"{return_code:#04x}"


def is_positive_return_code(return_code: apci.ReturnCode | int) -> bool:
    """Return whether a return code is positive (00h-5Fh)."""
    value = (
        return_code.value if isinstance(return_code, apci.ReturnCode) else return_code
    )
    return value <= _MAX_POSITIVE_RETURN_CODE


def pdt_control_state_data(
    payload: apci.FunctionPropertyExtStateResponse, what: str
) -> bytes:
    """
    Return the state data of a PDT_CONTROL response, raising on a negative return code.

    :param what: Describes the state machine for error messages
    :raises ManagementConnectionError: If the return code is not positive
    """
    if not is_positive_return_code(payload.return_code):
        raise ManagementConnectionError(
            f"{what} failed: {format_return_code(payload.return_code)}"
        )
    return payload.data
