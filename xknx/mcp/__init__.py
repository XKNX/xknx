"""
Host-agnostic MCP tool functions for the KNX bus and data point types.

These are plain async functions with frozen, JSON-serialisable dataclass inputs
and outputs. The bus tools operate on a connected :class:`~xknx.xknx.XKNX`
instance; the DPT tools are static. They carry **no dependency on any MCP SDK,
Home Assistant or a web framework** — each consumer (SpectrumKNX, Home
Assistant, …) wraps them into its own MCP transport and decides which write
tools to expose.

See :mod:`xknx.mcp.tools` for the tool functions and :mod:`xknx.mcp.types` for
the input/output models.
"""

from .tools import (
    describe_dpt,
    get_connection_status,
    list_dpts,
    read_group_value,
    send_group_value_read,
    send_group_value_write,
)
from .types import (
    ConnectionStatusResult,
    DptDetail,
    DptFilter,
    DptListResult,
    DptSummary,
    GroupAddressInput,
    GroupValue,
    GroupValueWriteInput,
    ReadGroupValueInput,
    ReadGroupValueResult,
    SendResult,
)

__all__ = [
    "ConnectionStatusResult",
    "DptDetail",
    "DptFilter",
    "DptListResult",
    "DptSummary",
    "GroupAddressInput",
    "GroupValue",
    "GroupValueWriteInput",
    "ReadGroupValueInput",
    "ReadGroupValueResult",
    "SendResult",
    "describe_dpt",
    "get_connection_status",
    "list_dpts",
    "read_group_value",
    "send_group_value_read",
    "send_group_value_write",
]
