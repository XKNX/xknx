"""Base class for `xknx group` commands."""

from __future__ import annotations

from abc import abstractmethod
import argparse

from xknx import XKNX

from .._command import Command, connection_config


class GroupCommand(Command):
    """Group address communication over a KNX bus connection."""

    name = "group"
    help_text = "read, write and monitor group addresses"

    async def run(self, args: argparse.Namespace) -> int:
        """Connect to the KNX bus and run the command."""
        async with XKNX(connection_config=connection_config(args)) as xknx:
            return await self.run_connected(xknx, args)

    @abstractmethod
    async def run_connected(self, xknx: XKNX, args: argparse.Namespace) -> int:
        """Execute the command on a connected XKNX instance."""
