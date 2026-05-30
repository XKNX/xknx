"""Tests for DPTComplex.get_dict_schema()."""

from __future__ import annotations

import json

import pytest

from xknx.dpt.dpt import DPTComplex


def _all_dpt_complex_classes() -> list[type[DPTComplex]]:  # type: ignore[type-arg]
    return list(DPTComplex.dpt_class_tree())


@pytest.mark.parametrize(
    "dpt_class", _all_dpt_complex_classes(), ids=lambda c: c.__name__
)
class TestAllDPTComplexSchemas:
    """Verify every DPTComplex subclass has a working, JSON-serializable get_dict_schema()."""

    def test_schema_is_list(self, dpt_class: type[DPTComplex]) -> None:  # type: ignore[type-arg]
        """Test that get_dict_schema() returns a non-empty list."""
        schema = dpt_class.get_dict_schema()
        assert isinstance(schema, list)
        assert len(schema) > 0

    def test_schema_fields_have_required_keys(
        self, dpt_class: type[DPTComplex]
    ) -> None:  # type: ignore[type-arg]
        """Test that every field dict contains the required keys with correct types."""
        schema = dpt_class.get_dict_schema()
        for field in schema:
            assert "name" in field
            assert "type" in field
            assert "required" in field
            assert isinstance(field["name"], str)
            assert field["type"] in ("integer", "string", "float", "boolean", "enum")
            assert isinstance(field["required"], bool)

    def test_enum_fields_have_options(self, dpt_class: type[DPTComplex]) -> None:  # type: ignore[type-arg]
        """Test that enum-typed fields include a non-empty options list."""
        schema = dpt_class.get_dict_schema()
        for field in schema:
            if field["type"] == "enum":
                assert "options" in field
                assert isinstance(field["options"], list)
                assert len(field["options"]) > 0

    def test_json_serializable(self, dpt_class: type[DPTComplex]) -> None:  # type: ignore[type-arg]
        """Test that the schema is JSON-serializable."""
        schema = dpt_class.get_dict_schema()
        json.dumps(schema)  # must not raise
