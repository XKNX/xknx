"""
Module for managing a scaling speed remote value.

DPT 225.001.
"""

from __future__ import annotations

from xknx.dpt import DPTScalingSpeed, ScalingSpeed

from .remote_value import RemoteValue


class RemoteValueScalingSpeed(RemoteValue[ScalingSpeed]):
    """Abstraction for remote value of KNX DPT 225.001 (DPT_ScalingSpeed)."""

    __slots__ = ()
    dpt_class = DPTScalingSpeed
