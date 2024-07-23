"""Implementation of KNX DPT 18 Scene control."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .dpt_17 import DPTSceneNumber
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class SceneControl(DPTComplexData):
    """Class for scene control."""

    scene_number: int
    learn: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SceneControl:
        """Init from a dictionary."""
        try:
            scene_number = int(data["scene_number"])
            learn = data.get("learn", False)
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for SceneControl: {err}") from err
        if learn not in (True, False):
            raise ValueError(f"Invalid value for SceneControl value `learn`: {learn}")
        return cls(scene_number=scene_number, learn=bool(learn))

    def as_dict(self) -> dict[str, int | str]:
        """Create a JSON serializable dictionary."""
        return {
            "scene_number": self.scene_number,
            "learn": self.learn,
        }


class DPTSceneControl(DPTComplex[SceneControl]):
    """
    Abstraction for KNX 1 Octet Scene Control.

    DPT 18.001
    """

    data_type = SceneControl
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 18
    dpt_sub_number = 1
    value_type = "scene_control"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> SceneControl:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)[0]
        return SceneControl(
            learn=bool(raw & 0x80),
            scene_number=(raw & 0x3F) + 1,
        )

    @classmethod
    def _to_knx(cls, value: SceneControl) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        scene_payload = DPTSceneNumber.to_knx(value.scene_number)
        if value.learn:
            return DPTArray(scene_payload.value[0] | 0x80)
        return scene_payload
