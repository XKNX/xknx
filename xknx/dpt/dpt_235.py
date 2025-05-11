"""Implementation of the KNX 235 data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .dpt import DPTComplex, DPTComplexData
from .dpt_5 import DPTTariff
from .dpt_13 import DPTActiveEnergy
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class TariffActiveEnergy(DPTComplexData):
    """
    Representation of Tariff and ActiveEnergy.

    `energy`: int 4byte signed; None if invalid
    `tariff`: int 0..254; None if invalid
    """

    energy: int | None = None
    tariff: int | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, int]) -> TariffActiveEnergy:
        """Init from a dictionary."""
        try:
            energy = data.get("energy")
            tariff = data.get("tariff")
        except AttributeError as err:
            raise ValueError(f"Invalid value for TariffActiveEnergy: {err}") from err
        if energy is not None:
            try:
                energy = int(energy)
            except ValueError as err:
                raise ValueError(f"Invalid value for energy: {err}") from err
        if tariff is not None:
            try:
                tariff = int(tariff)
            except ValueError as err:
                raise ValueError(f"Invalid value for tariff: {err}") from err
        return cls(energy=energy, tariff=tariff)

    def as_dict(self) -> dict[str, int | None]:
        """Create a JSON serializable dictionary."""
        return {
            "energy": self.energy,
            "tariff": self.tariff,
        }


class DPTTariffActiveEnergy(DPTComplex[TariffActiveEnergy]):
    """Abstraction for KNX 6 octet Tariff and ActiveEnergy (DPT 235.001)."""

    data_type = TariffActiveEnergy
    payload_type = DPTArray
    payload_length = 6
    dpt_main_number = 235
    dpt_sub_number = 1
    value_type = "tariff_active_energy"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> TariffActiveEnergy:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        energy_valid = (raw[5] >> 1 & 0b1) == 0
        tariff_valid = (raw[5] & 0b1) == 0
        return TariffActiveEnergy(
            energy=(
                DPTActiveEnergy.from_knx(DPTArray(raw[:4])) if energy_valid else None
            ),
            tariff=DPTTariff.from_knx(DPTArray([raw[4]])) if tariff_valid else None,
        )

    @classmethod
    def _to_knx(cls, value: TariffActiveEnergy) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        energy = (
            DPTActiveEnergy.to_knx(value.energy).value
            if value.energy is not None
            else [0, 0, 0, 0]
        )
        tariff = (
            DPTTariff.to_knx(value.tariff).value if value.tariff is not None else [0]
        )
        return DPTArray(
            (
                *energy,
                *tariff,
                (value.energy is None) << 1 | (value.tariff is None),
            )
        )
