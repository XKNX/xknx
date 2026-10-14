"""Unit test for KNX DPT 238 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_238 import (
    DALIDiagnostics,
    DPTDALIDiagnostics,
    DPTSceneConfig,
    SceneConfig,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestSceneConfig:
    """Test SceneConfig class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            ({"scene_number": 1}, SceneConfig(1)),
            (
                {"scene_number": 64, "scene_active": False},
                SceneConfig(64, scene_active=False),
            ),
            (
                {"scene_number": 5, "scene_active": True, "storage_enabled": False},
                SceneConfig(5, True, False),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: SceneConfig) -> None:
        """Test from_dict and as_dict methods."""
        assert SceneConfig.from_dict(data) == value
        default_dict = {"scene_active": True, "storage_enabled": True}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"scene_active": True},
            {"scene_number": "a"},
            {"scene_number": None},
            {"scene_number": 1, "scene_active": "a"},
            {"scene_number": 1, "storage_enabled": None},
            [1],
        ],
    )
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            SceneConfig.from_dict(data)


class TestDPTSceneConfig:
    """Test class for KNX DPTSceneConfig objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (SceneConfig(1), (0x00,)),
            (SceneConfig(64), (0x3F,)),
            (SceneConfig(1, scene_active=False), (0x40,)),
            (SceneConfig(1, storage_enabled=False), (0x80,)),
            (SceneConfig(64, False, False), (0xFF,)),
            (SceneConfig(11, True, False), (0x8A,)),
        ],
    )
    def test_values(self, value: SceneConfig, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        knx_value = DPTSceneConfig.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTSceneConfig.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test serializing from a dict."""
        assert DPTSceneConfig.to_knx(
            {"scene_number": 2, "scene_active": False}
        ) == DPTArray(0x41)

    @pytest.mark.parametrize(
        "value",
        [
            SceneConfig(0),
            SceneConfig(65),
            SceneConfig("a"),  # type: ignore[arg-type]
            {"scene_number": 0},
            {"scene_active": True},
            None,
            1,
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTSceneConfig.to_knx(value)

    @pytest.mark.parametrize(
        "payload", [DPTArray(()), DPTArray((0x00, 0x00)), DPTBinary(1)]
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing wrong payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTSceneConfig.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema."""
        assert DPTSceneConfig.get_dict_schema() == [
            {
                "name": "scene_number",
                "type": "integer",
                "required": True,
                "value_min": 1,
                "value_max": 64,
            },
            {
                "name": "scene_active",
                "type": "boolean",
                "required": False,
                "default": True,
            },
            {
                "name": "storage_enabled",
                "type": "boolean",
                "required": False,
                "default": True,
            },
        ]

    def test_transcoder_lookup(self) -> None:
        """Test lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder("238.001") is DPTSceneConfig
        assert DPTBase.parse_transcoder("scene_config") is DPTSceneConfig


class TestDALIDiagnostics:
    """Test DALIDiagnostics class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            ({"address": 0}, DALIDiagnostics(0)),
            (
                {"address": 63, "lamp_failure": True},
                DALIDiagnostics(63, lamp_failure=True),
            ),
            (
                {"address": 7, "lamp_failure": False, "ballast_failure": True},
                DALIDiagnostics(7, False, True),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: DALIDiagnostics) -> None:
        """Test from_dict and as_dict methods."""
        assert DALIDiagnostics.from_dict(data) == value
        default_dict = {"lamp_failure": False, "ballast_failure": False}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"lamp_failure": True},
            {"address": "a"},
            {"address": 1, "lamp_failure": "a"},
            {"address": 1, "ballast_failure": None},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            DALIDiagnostics.from_dict(data)


class TestDPTDALIDiagnostics:
    """Test class for KNX DPTDALIDiagnostics objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (DALIDiagnostics(0), (0x00,)),
            (DALIDiagnostics(63), (0x3F,)),
            (DALIDiagnostics(0, lamp_failure=True), (0x40,)),
            (DALIDiagnostics(0, ballast_failure=True), (0x80,)),
            (DALIDiagnostics(63, True, True), (0xFF,)),
            (DALIDiagnostics(21, True, False), (0x55,)),
        ],
    )
    def test_values(self, value: DALIDiagnostics, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        knx_value = DPTDALIDiagnostics.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTDALIDiagnostics.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test serializing from a dict."""
        assert DPTDALIDiagnostics.to_knx(
            {"address": 2, "ballast_failure": True}
        ) == DPTArray(0x82)

    @pytest.mark.parametrize(
        "value",
        [
            DALIDiagnostics(-1),
            DALIDiagnostics(64),
            DALIDiagnostics("a"),  # type: ignore[arg-type]
            {"address": 64},
            {"lamp_failure": True},
            None,
            1,
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTDALIDiagnostics.to_knx(value)

    @pytest.mark.parametrize(
        "payload", [DPTArray(()), DPTArray((0x00, 0x00)), DPTBinary(1)]
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing wrong payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTDALIDiagnostics.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema."""
        assert DPTDALIDiagnostics.get_dict_schema() == [
            {
                "name": "address",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 63,
            },
            {
                "name": "lamp_failure",
                "type": "boolean",
                "required": False,
                "default": False,
            },
            {
                "name": "ballast_failure",
                "type": "boolean",
                "required": False,
                "default": False,
            },
        ]

    def test_transcoder_lookup(self) -> None:
        """Test lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder("238.600") is DPTDALIDiagnostics
        assert DPTBase.parse_transcoder("dali_diagnostics") is DPTDALIDiagnostics
