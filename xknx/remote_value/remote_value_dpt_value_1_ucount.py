"""
Module for managing a DTP 5010 remote value.

DPT 5.010.
"""

from __future__ import annotations

from xknx.dpt import DPTValue1Ucount

from .remote_value import RemoteValue


class RemoteValueDptValue1Ucount(RemoteValue[int]):
    """Abstraction for remote value of KNX DPT 5.010."""

    dpt_class = DPTValue1Ucount
