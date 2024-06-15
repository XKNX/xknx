"""
Module for managing a DTP Scene Number remote value.

DPT 17.001.
"""

from __future__ import annotations

from xknx.dpt import DPTSceneNumber

from .remote_value import RemoteValue


class RemoteValueSceneNumber(RemoteValue[int]):
    """Abstraction for remote value of KNX DPT 17.001 (DPT_Scene_Number)."""

    dpt_class = DPTSceneNumber
