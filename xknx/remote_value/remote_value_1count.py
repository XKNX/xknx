"""
Module for managing an 1 count remote value.

DPT 6.010.
"""

from __future__ import annotations

from xknx.dpt import DPTValue1Count

from .remote_value import RemoteValue


class RemoteValue1Count(RemoteValue[int]):
    """Abstraction for remote value of KNX 6.010 (DPT_Value_1_Count)."""

    dpt_class = DPTValue1Count
