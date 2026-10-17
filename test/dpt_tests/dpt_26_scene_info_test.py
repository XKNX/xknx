"""Unit test for KNX DPT 26 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTSceneInfo, SceneInfo
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestSceneInfo:
    """Test SceneInfo class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"scene_number": 5, "active": False},
                SceneInfo(5, False),
            ),
            (
                {"scene_number": 2},
                SceneInfo(scene_number=2),
            ),
            (
                {"scene_number": 64, "active": True},
                SceneInfo(scene_number=64, active=True),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: SceneInfo) -> None:
        """Test from_dict and as_dict methods."""
        test_value = SceneInfo.from_dict(data)
        assert test_value == value
        # active defaults to `True`
        default_dict = {"active": True}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            {"active": False},
            {"scene_number": "a"},
            {"scene_number": None, "active": True},
            {"scene_number": 1, "active": "a"},
            {"scene_number": 1, "active": None},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            SceneInfo.from_dict(data)


class TestDPTSceneInfo:
    """Test class for KNX DPTSceneInfo objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (SceneInfo(1, True), (0b00000000,)),
            (SceneInfo(1, False), (0b01000000,)),
            (SceneInfo(17, True), (0b00010000,)),
            (SceneInfo(64, True), (0b00111111,)),
            (SceneInfo(64, False), (0b01111111,)),
        ],
    )
    def test_parse(self, value: SceneInfo, raw: tuple[int]) -> None:
        """Test DPTSceneInfo parsing and streaming."""
        knx_value = DPTSceneInfo.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTSceneInfo.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            ((0b10000000,), SceneInfo(1, True)),
            ((0b11111111,), SceneInfo(64, False)),
        ],
    )
    def test_from_knx_reserved_bit(self, raw: tuple[int], value: SceneInfo) -> None:
        """Test DPTSceneInfo ignores the reserved bit."""
        assert DPTSceneInfo.from_knx(DPTArray(raw)) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ({"scene_number": 17, "active": True}, (0x10,)),
            ({"scene_number": 21, "active": False}, (0x54,)),
            ({"scene_number": 3}, (0x02,)),
        ],
    )
    def test_to_knx_from_dict(self, value: dict[str, Any], raw: tuple[int]) -> None:
        """Test DPTSceneInfo serializing from a dict."""
        assert DPTSceneInfo.to_knx(value) == DPTArray(raw)

    @pytest.mark.parametrize(
        "value",
        [
            SceneInfo(scene_number=0, active=True),
            SceneInfo(scene_number=65, active=False),
            {"scene_number": 0},
            {"scene_number": 65},
            {"scene_number": 1, "active": "a"},
            {"active": True},
        ],
    )
    def test_to_knx_invalid(self, value: SceneInfo | dict[str, Any]) -> None:
        """Test DPTSceneInfo serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTSceneInfo.to_knx(value)

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray(()),
            DPTArray((0x01, 0x02)),
            DPTBinary(True),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test DPTSceneInfo parsing with wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTSceneInfo.from_knx(payload)

    @pytest.mark.parametrize("identifier", ["26.001", "scene_info"])
    def test_parse_transcoder(self, identifier: str) -> None:
        """Test DPTSceneInfo lookup by number and value_type."""
        assert DPTBase.parse_transcoder(identifier) is DPTSceneInfo

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTSceneInfo."""
        assert DPTSceneInfo.get_dict_schema() == [
            {
                "name": "scene_number",
                "type": "integer",
                "required": True,
                "value_min": 1,
                "value_max": 64,
            },
            {"name": "active", "type": "boolean", "required": False, "default": True},
        ]
