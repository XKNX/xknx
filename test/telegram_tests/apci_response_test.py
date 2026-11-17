"""Unit test for telling the response to a request apart from other telegrams."""

import pytest

from xknx.telegram.apci import (
    APCI,
    ADCRead,
    ADCResponse,
    APCIRequest,
    AuthorizeRequest,
    AuthorizeResponse,
    DeviceDescriptorRead,
    DeviceDescriptorResponse,
    FunctionPropertyExtStateRead,
    FunctionPropertyExtStateResponse,
    FunctionPropertyStateRead,
    FunctionPropertyStateResponse,
    MemoryExtendedRead,
    MemoryExtendedReadResponse,
    MemoryExtendedWrite,
    MemoryExtendedWriteResponse,
    MemoryRead,
    MemoryResponse,
    PropertyDescriptionRead,
    PropertyDescriptionResponse,
    PropertyExtDescriptionRead,
    PropertyExtDescriptionResponse,
    PropertyExtValueRead,
    PropertyExtValueResponse,
    PropertyExtValueWriteCon,
    PropertyExtValueWriteConRes,
    PropertyValueRead,
    PropertyValueResponse,
    PropertyValueWrite,
    ReturnCode,
    UserMemoryRead,
    UserMemoryResponse,
)

_PROPERTY_WRITE = PropertyValueWrite(
    object_index=1, property_id=5, count=1, start_index=1, data=bytes(10)
)


@pytest.mark.parametrize(
    ("request_", "payload", "is_response"),
    [
        # memory: the same address; a short response is left to the procedure
        (
            MemoryRead(address=0x4003, count=10),
            MemoryResponse(address=0x4003, data=bytes(10)),
            True,
        ),
        (
            MemoryRead(address=0x4000, count=10),
            MemoryResponse(address=0x4003, data=bytes(10)),
            False,
        ),
        (
            MemoryRead(address=0x4003, count=10),
            MemoryResponse(address=0x4003, data=bytes(4)),
            True,
        ),
        (
            MemoryRead(address=0x4003, count=10),
            MemoryResponse(address=0x4003, data=b""),
            True,
        ),
        (
            MemoryRead(address=0x4003, count=2),
            UserMemoryResponse(address=0x4003, data=bytes(2)),
            False,
        ),
        (
            UserMemoryRead(address=0x10000, count=2),
            UserMemoryResponse(address=0x10000, data=bytes(2)),
            True,
        ),
        (
            UserMemoryRead(address=0x10000, count=2),
            UserMemoryResponse(address=0x10001, data=bytes(2)),
            False,
        ),
        (
            MemoryExtendedRead(count=4, address=0x20000),
            MemoryExtendedReadResponse(return_code=0, address=0x20000, data=bytes(4)),
            True,
        ),
        (
            MemoryExtendedRead(count=4, address=0x20000),
            MemoryExtendedReadResponse(return_code=0, address=0x20000, data=bytes(2)),
            True,
        ),
        (
            MemoryExtendedRead(count=4, address=0x20000),
            MemoryExtendedReadResponse(return_code=3, address=0x20000),
            True,
        ),
        (
            MemoryExtendedWrite(address=0x20000, data=bytes(4)),
            MemoryExtendedWriteResponse(return_code=0, address=0x20000),
            True,
        ),
        (
            MemoryExtendedWrite(address=0x20000, data=bytes(4)),
            MemoryExtendedWriteResponse(return_code=0, address=0x20004),
            False,
        ),
        # Property values: the same object, Property and start index
        (
            _PROPERTY_WRITE,
            PropertyValueResponse(
                object_index=1, property_id=5, count=1, start_index=1, data=b"\x02"
            ),
            True,
        ),
        (_PROPERTY_WRITE, MemoryResponse(address=0x4003, data=bytes(10)), False),
        (
            _PROPERTY_WRITE,
            PropertyValueResponse(
                object_index=1, property_id=5, count=0, start_index=1
            ),
            True,
        ),
        (
            _PROPERTY_WRITE,
            PropertyValueResponse(object_index=2, property_id=5, start_index=1),
            False,
        ),
        (
            _PROPERTY_WRITE,
            PropertyValueResponse(object_index=1, property_id=6, start_index=1),
            False,
        ),
        (
            _PROPERTY_WRITE,
            PropertyValueResponse(object_index=1, property_id=5, start_index=2),
            False,
        ),
        (
            PropertyValueRead(object_index=0, property_id=11, count=2),
            PropertyValueResponse(
                object_index=0, property_id=11, count=1, start_index=1
            ),
            True,
        ),
        (
            PropertyExtValueRead(11, 1, 52, nr_of_elem=1, start_index=1),
            PropertyExtValueResponse(11, 1, 52, nr_of_elem=1, start_index=1),
            True,
        ),
        (
            PropertyExtValueRead(11, 1, 52, nr_of_elem=1, start_index=1),
            PropertyExtValueResponse(11, 2, 52, nr_of_elem=1, start_index=1),
            False,
        ),
        (
            PropertyExtValueWriteCon(11, 1, 52, nr_of_elem=1, start_index=1),
            PropertyExtValueWriteConRes(
                11, 1, 52, ReturnCode.E_SUCCESS, nr_of_elem=1, start_index=1
            ),
            True,
        ),
        (
            PropertyExtValueWriteCon(11, 1, 52, nr_of_elem=1, start_index=1),
            PropertyExtValueWriteConRes(
                11, 1, 53, ReturnCode.E_SUCCESS, nr_of_elem=1, start_index=1
            ),
            False,
        ),
        # Property descriptions: by Property ID, or by index when the ID is 0
        (
            PropertyDescriptionRead(object_index=1, property_id=5),
            PropertyDescriptionResponse(
                object_index=1, property_id=5, property_index=3
            ),
            True,
        ),
        (
            PropertyDescriptionRead(object_index=1, property_id=5),
            PropertyDescriptionResponse(object_index=2, property_id=5),
            False,
        ),
        (
            PropertyDescriptionRead(object_index=1, property_id=0, property_index=3),
            PropertyDescriptionResponse(
                object_index=1, property_id=5, property_index=3
            ),
            True,
        ),
        (
            PropertyDescriptionRead(object_index=1, property_id=0, property_index=3),
            PropertyDescriptionResponse(
                object_index=1, property_id=5, property_index=4
            ),
            False,
        ),
        (
            PropertyExtDescriptionRead(11, 1, 52),
            PropertyExtDescriptionResponse(11, 1, 52),
            True,
        ),
        (
            PropertyExtDescriptionRead(11, 1, 0, property_index=2),
            PropertyExtDescriptionResponse(11, 1, 52, property_index=3),
            False,
        ),
        # Function Properties: the same object and Property
        (
            FunctionPropertyStateRead(object_index=1, property_id=52),
            FunctionPropertyStateResponse(object_index=1, property_id=52),
            True,
        ),
        (
            FunctionPropertyStateRead(object_index=1, property_id=52),
            FunctionPropertyStateResponse(object_index=1, property_id=53),
            False,
        ),
        (
            FunctionPropertyExtStateRead(11, 1, 52),
            FunctionPropertyExtStateResponse(11, 1, 52, ReturnCode.E_SUCCESS),
            True,
        ),
        (
            FunctionPropertyExtStateRead(11, 1, 52),
            FunctionPropertyExtStateResponse(12, 1, 52, ReturnCode.E_SUCCESS),
            False,
        ),
        # A/D converter: the same channel
        (ADCRead(channel=1, count=2), ADCResponse(channel=1, count=2), True),
        (ADCRead(channel=1, count=2), ADCResponse(channel=1, count=0), True),
        (ADCRead(channel=1, count=2), ADCResponse(channel=2, count=2), False),
        # services told by their response type alone
        (
            DeviceDescriptorRead(descriptor=0),
            DeviceDescriptorResponse(descriptor=0, value=0x07B0),
            True,
        ),
        (
            DeviceDescriptorRead(descriptor=0),
            MemoryResponse(address=0x4003, data=b""),
            False,
        ),
        (AuthorizeRequest(key=0xFFFFFFFF), AuthorizeResponse(level=0), True),
        (DeviceDescriptorRead(descriptor=0), None, False),
    ],
)
def test_is_response(
    request_: APCIRequest[APCI], payload: APCI | None, is_response: bool
) -> None:
    """Test which payloads answer a request."""
    assert request_.is_response(payload) is is_response
