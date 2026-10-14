"""Implementation of KNX DPT 26 Scene info."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class SceneInfo(DPTComplexData):
    """
    Representation of a scene info.

    `scene_number`: int 1..64 - transmitted as 0..63
    `active`: bool - `True` if the scene is active
    """

    scene_number: int = field(metadata={"value_min": 1, "value_max": 64})
    active: bool = True

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SceneInfo:
        """Init from a dictionary."""
        try:
            scene_number = int(data["scene_number"])
            active = data.get("active", True)
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for SceneInfo: {err}") from err
        if active not in (True, False):
            raise ValueError(f"Invalid value for SceneInfo value `active`: {active}")
        return cls(scene_number=scene_number, active=bool(active))

    def as_dict(self) -> dict[str, int | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "scene_number": self.scene_number,
            "active": self.active,
        }


class DPTSceneInfo(DPTComplex[SceneInfo]):
    """
    Abstraction for KNX 1 Octet Scene Info.

    DPT 26.001
    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.25
    """

    data_type = SceneInfo
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 26
    dpt_sub_number = 1
    value_type = "scene_info"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> SceneInfo:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)[0]
        # the reserved bit 7 is ignored; bit 6 is set for an inactive scene
        return SceneInfo(
            scene_number=(raw & 0x3F) + 1,
            active=not raw & 0x40,
        )

    @classmethod
    def _to_knx(cls, value: SceneInfo) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not 1 <= value.scene_number <= 64:
            raise ValueError(f"Scene number out of range 1..64: {value}")
        inactive = 0 if value.active else 0x40
        return DPTArray(inactive | (value.scene_number - 1))
