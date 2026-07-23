"""Shared helpers for the ControlDimming-based relative control DPTs (250/252/253/254)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import MISSING, fields as dataclass_fields
from typing import Any

from xknx.typing import Self

from ..dpt import DPTComplexData
from ..dpt_1 import Step
from ..dpt_3 import ControlDimming


def pack_control_dimming(step: ControlDimming | None) -> int:
    """Pack a ControlDimming into a single ``r4B1U3`` byte (``0`` if ``None``)."""
    if step is None:
        return 0
    return step.control.value << 3 | step.step_code


def unpack_control_dimming(raw: int) -> ControlDimming:
    """Unpack a single ``r4B1U3`` byte into a ControlDimming."""
    return ControlDimming(control=Step(raw >> 3 & 0b1), step_code=raw & 0b111)


class _RelativeControlDimming(DPTComplexData):
    """
    Base for DPTs whose every field is a ControlDimming component.

    Each dataclass field ``<name>`` maps to a ``<name>_control`` /
    ``<name>_step_code`` pair in the dict form. Fields declared with a default
    (``None``) are optional and may be omitted together; fields without a
    default are required (used by DPTs without validity/mask bits).
    """

    __slots__ = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Init from a dictionary."""
        result: dict[str, ControlDimming | None] = {}
        for field_ in dataclass_fields(cls):
            key = field_.name
            control = data.get(f"{key}_control")
            step_code = data.get(f"{key}_step_code")
            if control is not None and step_code is not None:
                try:
                    result[key] = ControlDimming(
                        control=Step.parse(control), step_code=int(step_code)
                    )
                except (TypeError, ValueError) as err:
                    raise ValueError(f"Invalid value for {key}: {err}") from err
            elif control is not None or step_code is not None:
                raise ValueError(
                    f"Provide both {key}_control and {key}_step_code, or neither"
                )
            elif field_.default is MISSING and field_.default_factory is MISSING:
                raise ValueError(f"Both {key}_control and {key}_step_code are required")
            else:
                result[key] = None
        return cls(**result)

    def as_dict(self) -> dict[str, int | str | None]:
        """Create a JSON serializable dictionary."""
        result: dict[str, int | str | None] = {}
        for field_ in dataclass_fields(self):
            value: ControlDimming | None = getattr(self, field_.name)
            result[f"{field_.name}_control"] = (
                value.control.name.lower() if value is not None else None
            )
            result[f"{field_.name}_step_code"] = (
                value.step_code if value is not None else None
            )
        return result
