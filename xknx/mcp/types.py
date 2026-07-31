"""
Input/output dataclasses for the xknx MCP tools.

All fields are JSON-native, so a consumer can build inputs directly from tool
arguments and serialise outputs with :func:`dataclasses.asdict` without custom
encoders. DPTs are rendered as ``"main"`` or ``"main.sub"`` strings and
timestamps as ISO-8601.

Input fields carry their human-readable description as :data:`typing.Annotated`
metadata (a plain string). This keeps the library free of any schema/validation
dependency while letting a consumer surface per-parameter descriptions in its
tool schema via ``typing.get_type_hints(..., include_extras=True)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

# JSON-native value carried on the bus (decoded via a DPT transcoder, or raw).
GroupValue = bool | int | float | str | list[Any] | dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class DptFilter:
    """Filters for :func:`~xknx.mcp.tools.list_dpts`."""

    main: Annotated[int | None, "Restrict to this DPT main number, e.g. 9."] = None
    text: Annotated[
        str | None, "Case-insensitive match on the DPT number, value type and unit."
    ] = None
    limit: Annotated[int, "Maximum number of results to return."] = 200
    offset: Annotated[int, "Number of results to skip, for pagination."] = 0


@dataclass(frozen=True, slots=True)
class DptSummary:
    """A JSON-serialisable view of a KNX data point type."""

    dpt: str
    value_type: str | None
    unit: str | None
    value_min: float | None
    value_max: float | None
    resolution: float | None
    payload_length: int | None  # DPTArray byte / DPTBinary bit length; e.g. string max length
    options: list[str] | None  # enum DPTs: lower-cased value names, as in a complex DPT's enum-field schema
    schema: list[dict[str, Any]] | None  # for complex DPTs: the field schema of the dict form


@dataclass(frozen=True, slots=True)
class DptListResult:
    """Result of :func:`~xknx.mcp.tools.list_dpts`."""

    dpts: list[DptSummary]
    total_count: int
    offset: int
    next_offset: int | None  # pass as ``offset`` for the next page; ``None`` when exhausted
    limit_reached: bool


@dataclass(frozen=True, slots=True)
class DptDetail:
    """
    Result of :func:`~xknx.mcp.tools.describe_dpt`.

    ``found`` is ``False`` when the identifier resolves to no transcoder, in
    which case ``dpt`` is ``None``.
    """

    found: bool
    dpt: DptSummary | None


@dataclass(frozen=True, slots=True)
class ConnectionStatusResult:
    """Result of :func:`~xknx.mcp.tools.get_connection_status`."""

    state: str
    connection_type: str | None
    connected: bool
    connected_since: str | None
    local_address: str


@dataclass(frozen=True, slots=True)
class GroupValueReadInput:
    """Input for :func:`~xknx.mcp.tools.read_group_value`."""

    group_address: Annotated[str, 'Destination group address, e.g. "1/2/3".']
    value_type: Annotated[
        str | None,
        'DPT number ("9.001") or value-type name ("temperature"); omit to return '
        "the raw payload value.",
    ] = None


@dataclass(frozen=True, slots=True)
class GroupValueReadResult:
    """Result of :func:`~xknx.mcp.tools.read_group_value`."""

    group_address: str
    value_type: str | None
    responded: bool
    value: GroupValue


@dataclass(frozen=True, slots=True)
class GroupAddressInput:
    """Input naming a single group address (e.g. for a GroupValueRead)."""

    group_address: Annotated[str, 'Group address to act on, e.g. "1/2/3".']


@dataclass(frozen=True, slots=True)
class GroupValueWriteInput:
    """Input for :func:`~xknx.mcp.tools.send_group_value_write`."""

    group_address: Annotated[str, 'Destination group address, e.g. "1/2/3".']
    value: Annotated[GroupValue, "Value to write; encoded with value_type when given."]
    value_type: Annotated[
        str | None,
        'DPT number ("9.001") or value-type name ("temperature"). Without it, an '
        "int is sent as a 6-bit payload and a list of ints as a byte array.",
    ] = None


@dataclass(frozen=True, slots=True)
class SendResult:
    """Outcome of a fire-and-forget bus send: ``queued`` means the telegram was enqueued for transmission, not that it was delivered or acted upon."""

    group_address: str
    apci: str
    queued: bool = True


@dataclass(frozen=True, slots=True)
class EncodeDptPayloadInput:
    """Input for :func:`~xknx.mcp.tools.encode_dpt_payload`."""

    value: Annotated[GroupValue, "Value to encode (Python native type)."]
    value_type: Annotated[
        str,
        'DPT number ("9.001") or value-type name ("temperature") to encode with.',
    ]


@dataclass(frozen=True, slots=True)
class EncodeDptPayloadResult:
    """Result of :func:`~xknx.mcp.tools.encode_dpt_payload`."""

    payload: list[int]
    value_type: str


@dataclass(frozen=True, slots=True)
class DecodeDptPayloadInput:
    """Input for :func:`~xknx.mcp.tools.decode_dpt_payload`."""

    payload: Annotated[
        list[int] | int,
        "Raw payload representation to decode (list of byte integers, or a single integer for 6-bit DPTs like DPT 1/2/3).",
    ]
    value_type: Annotated[
        str,
        'DPT number ("9.001") or value-type name ("temperature") to decode with.',
    ]


@dataclass(frozen=True, slots=True)
class DecodeDptPayloadResult:
    """Result of :func:`~xknx.mcp.tools.decode_dpt_payload`."""

    value: GroupValue
    value_type: str

