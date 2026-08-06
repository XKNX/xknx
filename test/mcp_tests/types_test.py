"""Tests for the xknx MCP input/output dataclasses."""

from dataclasses import Field, fields

import pytest

from xknx.mcp import (
    DecodeDptPayloadInput,
    DptFilter,
    EncodeDptPayloadInput,
    GroupAddressInput,
    GroupValueReadInput,
    GroupValueWriteInput,
)


@pytest.mark.parametrize(
    "input_type",
    [
        DecodeDptPayloadInput,
        DptFilter,
        EncodeDptPayloadInput,
        GroupAddressInput,
        GroupValueReadInput,
        GroupValueWriteInput,
    ],
)
def test_input_fields_carry_a_description(input_type: type) -> None:
    """Every input field is described, so a consumer can build its tool schema."""
    field: Field  # type: ignore[type-arg]
    for field in fields(input_type):
        description = field.metadata.get("description")
        assert isinstance(description, str) and description, (
            f"{input_type.__name__}.{field.name} has no description metadata"
        )
