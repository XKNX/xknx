"""
cEMI local device management of a KNXnet/IP tunnelling server.

M_PropRead.req and M_PropWrite.req are answered from read-only Properties of the
server's own Interface Objects - KNX v01.04.02 - External Message Interface
03.06.03 - §4.1.7.3. The requests are parsed from the raw octets, so a request
for an Interface Object type xknx doesn't know is answered as well.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from xknx.cemi import CEMIErrorCode, CEMIMessageCode

# message code, interface object type, object instance, property id,
# number of elements and start index - KNX v01.04.02 - External Message
# Interface 03.06.03 - §4.1.7.3.1
PROPERTY_SERVICE_HEADER_LENGTH: Final = 7

PropertyElements = Callable[[int, int], list[bytes] | None]
"""Return the elements of a Property by object type and property id, or None when it doesn't exist."""


def _response(
    code: CEMIMessageCode, request: bytes, number_of_elements: int, data: bytes
) -> bytes:
    """Return a property service response to `request` with its start index."""
    start_index = int.from_bytes(request[5:7], "big") & 0x0FFF
    return (
        bytes((code.value,))
        + request[1:5]
        + ((number_of_elements << 12) | start_index).to_bytes(2, "big")
        + data
    )


def _error(code: CEMIMessageCode, request: bytes, error: CEMIErrorCode) -> bytes:
    """Return a negative property service response - number of elements 0, error code as data."""
    return _response(code, request, 0, bytes((error,)))


def property_service_response(
    raw: bytes, elements_of: PropertyElements
) -> bytes | None:
    """
    Return the M_PropRead.con or M_PropWrite.con answering a request.

    Only object instance 1 exists. Reading start index 0 returns the current
    number of elements. Every Property is read-only. The errors are checked in the
    order of KNX v01.04.02 - External Message Interface 03.06.03 - §4.1.7.3.7.3:
    Void DP, Property index range, Read Only. Return None for anything but a
    property service request.
    """
    if len(raw) < PROPERTY_SERVICE_HEADER_LENGTH:
        return None
    if raw[0] == CEMIMessageCode.M_PROP_READ_REQ.value:
        code = CEMIMessageCode.M_PROP_READ_CON
    elif raw[0] == CEMIMessageCode.M_PROP_WRITE_REQ.value:
        code = CEMIMessageCode.M_PROP_WRITE_CON
    else:
        return None
    object_type = int.from_bytes(raw[1:3], "big")
    object_instance = raw[3]
    property_id = raw[4]
    number_of_elements = raw[5] >> 4
    start_index = int.from_bytes(raw[5:7], "big") & 0x0FFF

    elements = elements_of(object_type, property_id) if object_instance == 1 else None
    if elements is None:
        return _error(code, raw, CEMIErrorCode.CEMI_ERROR_VOID_DP)
    if start_index == 0:
        index_valid = number_of_elements == 1
    else:
        index_valid = (
            number_of_elements > 0
            and start_index + number_of_elements - 1 <= len(elements)
        )
    if not index_valid:
        return _error(code, raw, CEMIErrorCode.CEMI_ERROR_PROP_INDEX_RANGE)
    if code is CEMIMessageCode.M_PROP_WRITE_CON:
        return _error(code, raw, CEMIErrorCode.CEMI_ERROR_READ_ONLY)
    if start_index == 0:
        return _response(code, raw, 1, len(elements).to_bytes(2, "big"))
    return _response(
        code,
        raw,
        number_of_elements,
        b"".join(elements[start_index - 1 : start_index - 1 + number_of_elements]),
    )


def property_info_indication(
    object_type: int, property_id: int, element: bytes
) -> bytes:
    """Return an M_PropInfo.ind for the first element of a Property - KNX v01.04.02 - External Message Interface 03.06.03 - §4.1.7.3.6."""
    return (
        bytes((CEMIMessageCode.M_PROP_INFO_IND.value,))
        + object_type.to_bytes(2, "big")
        + bytes((1, property_id))
        + ((1 << 12) | 1).to_bytes(2, "big")
        + element
    )
