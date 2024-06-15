"""
Module for managing a remote temperature value.

DPT 9.001.
"""

from __future__ import annotations

from xknx.dpt import DPTTemperature

from .remote_value import RemoteValue


class RemoteValueTemp(RemoteValue[float]):
    """Abstraction for remote value of KNX 9.001 (DPT_Value_Temp)."""

    dpt_class = DPTTemperature
