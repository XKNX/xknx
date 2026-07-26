"""
MCP tool functions for the KNX bus and data point types.

The bus tools take a connected :class:`~xknx.xknx.XKNX` instance; the DPT tools
are static. Each returns a JSON-serialisable dataclass. They are transport- and
host-agnostic (no MCP SDK, Home Assistant or web-framework imports), so every
consumer wraps them into its own MCP transport.

The functions are ``async`` for a uniform calling convention across the XKNX
MCP tool libraries, even where the underlying operation is synchronous.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from xknx.core.connection_state import XknxConnectionState
from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTNumeric
from xknx.tools import (
    group_value_read,
    group_value_write,
    read_group_value as _read_group_value,
)

from .types import (
    ConnectionStatusResult,
    DecodePayloadInput,
    DecodePayloadResult,
    DptDetail,
    DptFilter,
    DptListResult,
    DptSummary,
    EncodeValueInput,
    EncodeValueResult,
    GroupAddressInput,
    GroupValue,
    GroupValueReadInput,
    GroupValueReadResult,
    GroupValueWriteInput,
    SendResult,
)

if TYPE_CHECKING:
    from xknx.xknx import XKNX

_T = TypeVar("_T")


def _paginate(items: list[_T], limit: int, offset: int) -> tuple[list[_T], bool]:
    """Slice ``items`` by ``offset``/``limit`` and report whether the limit was hit."""
    window = items[offset : offset + limit] if limit >= 0 else items[offset:]
    limit_reached = 0 <= limit < len(items) - offset
    return window, limit_reached


def _numeric_bounds(dpt: type[DPTBase]) -> tuple[float | None, float | None, float | None]:
    """Return ``(value_min, value_max, resolution)`` for numeric DPTs, else ``None``s."""
    if issubclass(dpt, DPTNumeric):
        return (float(dpt.value_min), float(dpt.value_max), float(dpt.resolution))
    return (None, None, None)


def _summarize_dpt(dpt: type[DPTBase]) -> DptSummary:
    value_min, value_max, resolution = _numeric_bounds(dpt)
    return DptSummary(
        dpt=dpt.dpt_number_str(),
        value_type=dpt.value_type,
        unit=dpt.unit,
        value_min=value_min,
        value_max=value_max,
        resolution=resolution,
    )


def _concrete_dpts() -> list[type[DPTBase]]:
    """Every concrete DPT transcoder (those with a main number), ordered by main then sub."""
    seen: dict[str, type[DPTBase]] = {
        dpt.dpt_number_str(): dpt
        for dpt in DPTBase.dpt_class_tree()
        if dpt.dpt_main_number is not None
    }
    return sorted(
        seen.values(),
        key=lambda dpt: (dpt.dpt_main_number or 0, dpt.dpt_sub_number or -1),
    )


async def list_dpts(filters: DptFilter | None = None) -> DptListResult:
    """List the known KNX data point types, optionally filtered."""
    filters = filters or DptFilter()
    needle = filters.text.lower() if filters.text else None

    matches: list[DptSummary] = []
    for dpt in _concrete_dpts():
        if filters.main is not None and dpt.dpt_main_number != filters.main:
            continue
        summary = _summarize_dpt(dpt)
        if needle is not None and needle not in (
            f"{summary.dpt}\n{summary.value_type or ''}\n{summary.unit or ''}".lower()
        ):
            continue
        matches.append(summary)

    window, limit_reached = _paginate(matches, filters.limit, filters.offset)
    return DptListResult(
        dpts=window,
        total_count=len(matches),
        offset=filters.offset,
        next_offset=filters.offset + len(window) if limit_reached else None,
        limit_reached=limit_reached,
    )


async def describe_dpt(dpt: str) -> DptDetail:
    """Resolve a DPT number (``"9.001"``) or value type name to its definition."""
    try:
        transcoder = DPTBase.get_dpt(dpt)
    except ValueError:
        return DptDetail(found=False, dpt=None)
    return DptDetail(found=True, dpt=_summarize_dpt(transcoder))


async def get_connection_status(xknx: XKNX) -> ConnectionStatusResult:
    """Report the bus connection state, type and local individual address."""
    manager = xknx.connection_manager
    return ConnectionStatusResult(
        state=manager.state.value,
        connection_type=manager.connection_type.value,
        connected=manager.state is XknxConnectionState.CONNECTED,
        connected_since=(
            manager.connected_since.isoformat()
            if manager.connected_since is not None
            else None
        ),
        local_address=str(xknx.current_address),
    )


def _jsonify(value: object) -> GroupValue:
    """
    Coerce a decoded bus value into a JSON-native shape.

    ``read_group_value`` returns Python natives (a DPT transcoder's ``from_knx``
    output, or the raw payload value). Tuples become lists; anything not already
    JSON-native (e.g. an enum or dataclass from a complex DPT) is stringified.
    """
    if isinstance(value, tuple):
        return [_jsonify(item) for item in value]
    if value is None or isinstance(value, bool | int | float | str | list | dict):
        return value
    return str(value)


async def read_group_value(
    xknx: XKNX, request: GroupValueReadInput
) -> GroupValueReadResult:
    """Read a value from a group address, decoding it with the given DPT if set."""
    value = await _read_group_value(
        xknx, request.group_address, value_type=request.value_type
    )
    return GroupValueReadResult(
        group_address=request.group_address,
        value_type=request.value_type,
        responded=value is not None,
        value=_jsonify(value),
    )


async def send_group_value_read(xknx: XKNX, request: GroupAddressInput) -> SendResult:
    """
    Queue a GroupValueRead telegram to trigger a response on the bus.

    Raises :exc:`~xknx.exceptions.CouldNotParseAddress` for an invalid address
    (nothing is queued in that case).
    """
    group_value_read(xknx, request.group_address)
    return SendResult(group_address=request.group_address, apci="GroupValueRead")


async def send_group_value_write(xknx: XKNX, request: GroupValueWriteInput) -> SendResult:
    """
    Queue a GroupValueWrite telegram encoding ``value`` with the given DPT.

    This is a **write** operation: consumers gate it behind their read-write mode.
    Raises :exc:`~xknx.exceptions.CouldNotParseAddress` for an invalid address and
    :exc:`~xknx.exceptions.ConversionError` if ``value`` does not fit ``value_type``
    (nothing is queued in either case).
    """
    group_value_write(
        xknx, request.group_address, request.value, value_type=request.value_type
    )
    return SendResult(group_address=request.group_address, apci="GroupValueWrite")


async def encode_value(request: EncodeValueInput) -> EncodeValueResult:
    """Encode a value using a specific DPT into its raw payload bytes."""
    transcoder = DPTBase.get_dpt(request.value_type)
    encoded = transcoder.to_knx(request.value)
    if isinstance(encoded, DPTArray):
        payload = list(encoded.value)
    else:
        payload = [encoded.value]
    return EncodeValueResult(payload=payload, value_type=request.value_type)


async def decode_payload(request: DecodePayloadInput) -> DecodePayloadResult:
    """Decode raw payload bytes or integer using a specific DPT."""
    transcoder = DPTBase.get_dpt(request.value_type)
    if transcoder.payload_type is DPTBinary:
        if isinstance(request.payload, int):
            raw = DPTBinary(request.payload)
        elif isinstance(request.payload, list | tuple):
            if not request.payload:
                raise ValueError("Empty payload for DPTBinary")
            raw = DPTBinary(request.payload[0])
        else:
            raise TypeError("Unsupported payload type for DPTBinary")
    else:
        if isinstance(request.payload, int):
            raw = DPTArray([request.payload])
        elif isinstance(request.payload, list | tuple):
            raw = DPTArray(list(request.payload))
        else:
            raise TypeError("Unsupported payload type for DPTArray")

    decoded = transcoder.from_knx(raw)
    return DecodePayloadResult(value=_jsonify(decoded), value_type=request.value_type)

