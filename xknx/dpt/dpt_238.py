"""Implementation of KNX DPT 238 Scene Configuration and DALI Diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..exceptions import ConversionError
from .dpt import DPTComplex, DPTComplexData
from .dpt_17 import DPTSceneNumber
from .payload import DPTArray, DPTBinary


def _parse_flags(
    data: Mapping[str, Any], defaults: Mapping[str, bool], name: str
) -> dict[str, bool]:
    """Return boolean fields from a dictionary; raise ValueError for invalid values."""
    flags = {key: data.get(key, default) for key, default in defaults.items()}
    for key, flag in flags.items():
        if flag not in (True, False):
            raise ValueError(f"Invalid value for {name} value `{key}`: {flag}")
    return {key: bool(flag) for key, flag in flags.items()}


@dataclass(slots=True)
class SceneConfig(DPTComplexData):
    """
    Representation of a Scene Configuration.

    `scene_number`: int 1..64 (encoded as 0..63, like DPT 17.001)
    `scene_active`: bool; encoded inverted (0: active)
    `storage_enabled`: bool; True if the scene may be stored via DPT 18.001
        at runtime; encoded inverted (0: enable)
    """

    scene_number: int = field(metadata={"value_min": 1, "value_max": 64})
    scene_active: bool = True
    storage_enabled: bool = True

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SceneConfig:
        """Init from a dictionary."""
        try:
            scene_number = int(data["scene_number"])
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for SceneConfig: {err}") from err
        flags = _parse_flags(
            data, {"scene_active": True, "storage_enabled": True}, "SceneConfig"
        )
        return cls(scene_number=scene_number, **flags)

    def as_dict(self) -> dict[str, int | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "scene_number": self.scene_number,
            "scene_active": self.scene_active,
            "storage_enabled": self.storage_enabled,
        }


class DPTSceneConfig(DPTComplex[SceneConfig]):
    """
    Abstraction for KNX 1 Octet Scene Configuration.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.50.1
    DPT 238.001
    """

    data_type = SceneConfig
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 238
    dpt_sub_number = 1
    value_type = "scene_config"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> SceneConfig:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)[0]
        return SceneConfig(
            scene_number=(raw & 0x3F) + 1,
            scene_active=not (raw & 0x40),
            storage_enabled=not (raw & 0x80),
        )

    @classmethod
    def _to_knx(cls, value: SceneConfig) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        scene_raw = DPTSceneNumber.to_knx(value.scene_number).value[0]
        return DPTArray(
            (not value.storage_enabled) << 7 | (not value.scene_active) << 6 | scene_raw
        )


@dataclass(slots=True)
class DALIDiagnostics(DPTComplexData):
    """
    Representation of DALI Diagnostics.

    `address`: int 0..63; DALI Device Address
    `lamp_failure`: bool
    `ballast_failure`: bool
    """

    address: int = field(metadata={"value_min": 0, "value_max": 63})
    lamp_failure: bool = False
    ballast_failure: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DALIDiagnostics:
        """Init from a dictionary."""
        try:
            address = int(data["address"])
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for DALIDiagnostics: {err}") from err
        flags = _parse_flags(
            data, {"lamp_failure": False, "ballast_failure": False}, "DALIDiagnostics"
        )
        return cls(address=address, **flags)

    def as_dict(self) -> dict[str, int | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "address": self.address,
            "lamp_failure": self.lamp_failure,
            "ballast_failure": self.ballast_failure,
        }


class DPTDALIDiagnostics(DPTComplex[DALIDiagnostics]):
    """
    Abstraction for KNX 1 Octet DALI Diagnostics.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.8.1
    DPT 238.600
    """

    data_type = DALIDiagnostics
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 238
    dpt_sub_number = 600
    value_type = "dali_diagnostics"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> DALIDiagnostics:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)[0]
        return DALIDiagnostics(
            address=raw & 0x3F,
            lamp_failure=bool(raw & 0x40),
            ballast_failure=bool(raw & 0x80),
        )

    @classmethod
    def _to_knx(cls, value: DALIDiagnostics) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= value.address <= 63:
            raise ConversionError(f"Address out of range 0..63: {value.address}")
        return DPTArray(
            bool(value.ballast_failure) << 7
            | bool(value.lamp_failure) << 6
            | value.address
        )
