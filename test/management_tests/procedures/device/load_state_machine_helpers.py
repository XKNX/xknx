"""Helpers shared by the tests of the DM_LoadStateMachine* procedures."""

from collections.abc import Iterable
import itertools

from xknx import XKNX
from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceObjectType
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

IA = IndividualAddress("4.0.10")
PID_LOAD_STATE_CONTROL = 5


def sent_requests(xknx: XKNX) -> list[apci.APCI]:
    """Return the payloads of the connected data telegrams sent so far."""
    return [
        call.args[0].payload
        for call in xknx.cemi_handler.send_telegram.call_args_list
        if isinstance(call.args[0].tpci, tpci.TDataConnected)
    ]


def _incoming(xknx: XKNX, tpdu: tpci.TPCI, payload: apci.APCI | None = None) -> None:
    xknx.management.process(
        Telegram(
            source_address=IA,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpdu,
            payload=payload,
        )
    )


async def connect(xknx: XKNX, replies: Iterable[apci.APCI | None]) -> P2PConnection:
    """
    Connect to a device answering the requests on the connection in turn.

    Each request is acknowledged right when it is sent and answered with its
    reply (None = acknowledge only). A request without a reply fails the test.
    Requests are not rate limited.
    """
    conn = await xknx.management.connect(IA, rate_limit=0)
    xknx.cemi_handler.send_telegram.reset_mock()
    pending = iter(replies)
    device_sequence = itertools.count()

    def send_telegram(telegram: Telegram) -> None:
        if not isinstance(telegram.tpci, tpci.TDataConnected):
            return
        try:
            reply = next(pending)
        except StopIteration:
            raise AssertionError(f"Unexpected request {telegram.payload}") from None
        _incoming(xknx, tpci.TAck(telegram.tpci.sequence_number))
        if reply is not None:
            _incoming(xknx, tpci.TDataConnected(next(device_sequence) & 0xF), reply)

    xknx.cemi_handler.send_telegram.side_effect = send_telegram
    return conn


def property_response(data: bytes, count: int = 1) -> apci.PropertyValueResponse:
    """Return the A_PropertyValue_Response of the load state Property."""
    return apci.PropertyValueResponse(
        object_index=3,
        property_id=PID_LOAD_STATE_CONTROL,
        count=count,
        start_index=1,
        data=data,
    )


def ext_response(
    data: bytes, return_code: apci.ReturnCode = apci.ReturnCode.E_SUCCESS
) -> apci.FunctionPropertyExtStateResponse:
    """Return the A_FunctionPropertyExtState_Response of a Load State Machine."""
    return apci.FunctionPropertyExtStateResponse(
        interface_object_type=ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
        object_instance=1,
        property_id=PID_LOAD_STATE_CONTROL,
        return_code=return_code,
        data=data,
    )


def memory_response(state: int, address: int = 0xB6EC) -> apci.MemoryResponse:
    """Return the A_Memory_Response of a memory mapped load state."""
    return apci.MemoryResponse(address=address, data=bytes([state]))


def property_write(event: int, data: bytes = b"") -> apci.PropertyValueWrite:
    """Return the A_PropertyValue_Write of a load control."""
    return apci.PropertyValueWrite(
        object_index=3,
        property_id=PID_LOAD_STATE_CONTROL,
        count=1,
        start_index=1,
        data=bytes([event]) + data.ljust(9, b"\x00"),
    )


def property_read(object_index: int = 3) -> apci.PropertyValueRead:
    """Return the A_PropertyValue_Read of the load state Property."""
    return apci.PropertyValueRead(
        object_index=object_index,
        property_id=PID_LOAD_STATE_CONTROL,
        count=1,
        start_index=1,
    )
