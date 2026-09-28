"""Commands for KNX group address communication."""

from ._base import GroupCommand
from .monitor import MonitorCommand
from .read import ReadCommand
from .write import WriteCommand

COMMANDS: tuple[type[GroupCommand], ...] = (
    ReadCommand,
    WriteCommand,
    MonitorCommand,
)

__all__ = [
    "COMMANDS",
    "GroupCommand",
    "MonitorCommand",
    "ReadCommand",
    "WriteCommand",
]
