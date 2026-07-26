"""
Input/output dataclasses for the xknx MCP tools.

All fields are JSON-native, so a consumer can build inputs directly from tool
arguments and serialise outputs with :func:`dataclasses.asdict` without custom
encoders. DPTs are rendered as ``"main"`` or ``"main.sub"`` strings and
timestamps as ISO-8601.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# JSON-native value carried on the bus (decoded via a DPT transcoder, or raw).
GroupValue = bool | int | float | str | list[Any] | dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class DptFilter:
    """
    Filters for :func:`~xknx.mcp.tools.list_dpts`.

    ``main`` restricts to a single DPT main number. ``text`` matches
    case-insensitively against the DPT number, value type and unit.
    """

    main: int | None = None
    text: str | None = None
    limit: int = 200
    offset: int = 0


@dataclass(frozen=True, slots=True)
class DptSummary:
    """A JSON-serialisable view of a KNX data point type."""

    dpt: str
    value_type: str | None
    unit: str | None
    value_min: float | None
    value_max: float | None
    resolution: float | None


@dataclass(frozen=True, slots=True)
class DptListResult:
    """Result of :func:`~xknx.mcp.tools.list_dpts`."""

    dpts: list[DptSummary]
    total_count: int
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
class ReadGroupValueInput:
    """
    Input for :func:`~xknx.mcp.tools.read_group_value`.

    ``value_type`` is a DPT number (``"9.001"``) or value type name
    (``"temperature"``); when omitted the raw payload value is returned.
    """

    group_address: str
    value_type: str | None = None


@dataclass(frozen=True, slots=True)
class ReadGroupValueResult:
    """Result of :func:`~xknx.mcp.tools.read_group_value`."""

    group_address: str
    value_type: str | None
    responded: bool
    value: GroupValue


@dataclass(frozen=True, slots=True)
class GroupAddressInput:
    """Input naming a single group address (e.g. for a GroupValueRead)."""

    group_address: str


@dataclass(frozen=True, slots=True)
class GroupValueWriteInput:
    """
    Input for :func:`~xknx.mcp.tools.send_group_value_write`.

    ``value_type`` selects the DPT transcoder used to encode ``value``. Without
    it, an ``int`` is sent as a 6-bit payload and a list of ints as a byte
    array.
    """

    group_address: str
    value: GroupValue
    value_type: str | None = None


@dataclass(frozen=True, slots=True)
class SendResult:
    """Result of a fire-and-forget bus send (the telegram was queued)."""

    group_address: str
    apci: str
    queued: bool = True
