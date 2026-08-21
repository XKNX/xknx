"""
Module for managing a scene control remote value.

DPT 18.001.
"""

from __future__ import annotations

from xknx.dpt import DPTSceneControl, SceneControl

from .remote_value import RemoteValue


class RemoteValueSceneControl(RemoteValue[SceneControl]):
    """Abstraction for remote value of KNX DPT 18.001 (DPT_SceneControl)."""

    __slots__ = ()
    dpt_class = DPTSceneControl
