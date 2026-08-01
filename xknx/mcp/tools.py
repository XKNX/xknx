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
from xknx.dpt import (
    DPTArray,
    DPTBase,
    DPTBinary,
    DPTComplex,
    DPTComplexData,
    DPTEnum,
    DPTEnumData,
    DPTNumeric,
)
from xknx.tools import (
    group_value_read,
    group_value_write,
    read_group_value as _read_group_value,
)

from .types import (
    ConnectionStatusResult,
    DecodeDptPayloadInput,
    DecodeDptPayloadResult,
    DptDetail,
    DptFilter,
    DptListResult,
    DptSummary,
    EncodeDptPayloadInput,
    EncodeDptPayloadResult,
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


def _numeric_bounds(
    dpt: type[DPTBase],
) -> tuple[float | None, float | None, float | None]:
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
        payload_type="binary" if dpt.payload_type is DPTBinary else "array",
        payload_length=dpt.payload_length,
    )


def _dpt_haystack(dpt: type[DPTBase]) -> str:
    """Return the lower-cased text a ``list_dpts`` text filter matches against."""
    return f"{dpt.dpt_number_str()}\n{dpt.value_type or ''}\n{dpt.unit or ''}".lower()


async def list_dpts(filters: DptFilter | None = None) -> DptListResult:
    """List the known KNX data point types, optionally filtered."""
    filters = filters or DptFilter()
    needle = filters.text.lower() if filters.text else None

    # dpt_class_tree() already yields only concrete transcoders (each with a
    # main number); filter, then order by DPT number.
    matches = [
        dpt
        for dpt in DPTBase.dpt_class_tree()
        if (filters.main is None or dpt.dpt_main_number == filters.main)
        and (needle is None or needle in _dpt_haystack(dpt))
    ]
    matches.sort(key=lambda dpt: (dpt.dpt_main_number, dpt.dpt_sub_number or -1))

    window, limit_reached = _paginate(matches, filters.limit, filters.offset)
    return DptListResult(
        dpts=[_summarize_dpt(dpt) for dpt in window],
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
    options = (
        [member.name.lower() for member in transcoder.get_valid_values()]
        if issubclass(transcoder, DPTEnum)
        else None
    )
    fields = (
        [dict(field) for field in transcoder.get_dict_schema()]
        if issubclass(transcoder, DPTComplex)
        else None
    )
    return DptDetail(
        found=True,
        dpt=_summarize_dpt(transcoder),
        options=options,
        fields=fields,
    )


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
    output, or the raw payload value). Complex DPT values become their
    ``as_dict()`` form and enum values their lower-cased member name (matching HA,
    the Group Monitor and the ``as_dict()`` enum form); tuples become lists;
    anything else JSON-native passes through, and the rest is stringified.
    """
    if isinstance(value, DPTComplexData):
        return value.as_dict()
    if isinstance(value, DPTEnumData):
        return value.name.lower()
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


async def send_group_value_write(
    xknx: XKNX, request: GroupValueWriteInput
) -> SendResult:
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


async def encode_dpt_payload(request: EncodeDptPayloadInput) -> EncodeDptPayloadResult:
    """
    Encode a value using a specific DPT into its raw payload bytes.

    Raises :exc:`ValueError` if ``value_type`` matches no DPT and
    :exc:`~xknx.exceptions.ConversionError` if ``value`` cannot be encoded with it.
    """
    transcoder = DPTBase.get_dpt(request.value_type)
    encoded = transcoder.to_knx(request.value)
    payload = (
        list(encoded.value) if isinstance(encoded, DPTArray) else [int(encoded.value)]
    )
    return EncodeDptPayloadResult(payload=payload, value_type=request.value_type)


async def decode_dpt_payload(request: DecodeDptPayloadInput) -> DecodeDptPayloadResult:
    """
    Decode a raw payload (byte list, or a single int for 6-bit DPTs) with a DPT.

    Raises :exc:`ValueError` if ``value_type`` matches no DPT and
    :exc:`~xknx.exceptions.ConversionError` if the payload is invalid for it.
    """
    transcoder = DPTBase.get_dpt(request.value_type)
    values = (
        [request.payload] if isinstance(request.payload, int) else list(request.payload)
    )
    raw: DPTArray | DPTBinary
    if transcoder.payload_type is DPTBinary:
        if not values:
            raise ValueError("Empty payload for DPTBinary")
        raw = DPTBinary(values[0])
    else:
        raw = DPTArray(values)
    decoded = transcoder.from_knx(raw)
    return DecodeDptPayloadResult(
        value=_jsonify(decoded), value_type=request.value_type
    )
