"""Unit test for KNX DPT 18 objects."""

import pytest

from xknx.dpt import DPTArray, DPTBinary, DPTSceneControl, SceneControl
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestSceneControl:
    """Test SceneControl class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"scene_number": 5, "learn": False},
                SceneControl(5, False),
            ),
            (
                {"scene_number": 2},
                SceneControl(scene_number=2),
            ),
            (
                {"scene_number": 17, "learn": True},
                SceneControl(scene_number=17, learn=True),
            ),
        ],
    )
    def test_dict(self, data, value):
        """Test from_dict and as_dict methods."""
        test_value = SceneControl.from_dict(data)
        assert test_value == value
        # learn defaults to `False`
        default_dict = {"learn": False}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            # invalid data
            {"learn": False},
            {"scene_number": "a"},
            {"scene_number": None, "learn": True},
            {"scene_number": 1, "learn": "a"},
            {"scene_number": 1, "learn": None},
        ],
    )
    def test_dict_invalid(self, data):
        """Test from_dict and as_dict methods."""
        with pytest.raises(ValueError):
            SceneControl.from_dict(data)


class TestDPTSceneControl:
    """Test class for KNX DPTSceneControl objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (SceneControl(1, False), (0b00000000,)),
            (SceneControl(1, True), (0b10000000,)),
            (SceneControl(64, False), (0b00111111,)),
            (SceneControl(64, True), (0b10111111,)),
        ],
    )
    def test_parse(self, value, raw):
        """Test DPTTariffActiveEnergy parsing and streaming."""
        knx_value = DPTSceneControl.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTSceneControl.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ({"scene_number": 17, "learn": False}, (0x10,)),
            ({"scene_number": 21, "learn": True}, (0x94,)),
        ],
    )
    def test_to_knx_from_dict(self, value, raw):
        """Test DPTTariffActiveEnergy parsing from a dict."""
        assert DPTSceneControl.to_knx(value) == DPTArray(raw)

    @pytest.mark.parametrize(
        ("value"),
        [
            SceneControl(scene_number=0, learn=False),
            SceneControl(scene_number=65, learn=True),
        ],
    )
    def test_to_knx_limits(self, value):
        """Test initialization of DPTTariffActiveEnergy with wrong value."""
        with pytest.raises(ConversionError):
            DPTSceneControl.to_knx(value)

    def test_from_knx_wrong_value(self):
        """Test DPTTariffActiveEnergy parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPTSceneControl.from_knx(DPTArray((0xFF, 0x4E)))
        with pytest.raises(CouldNotParseTelegram):
            DPTSceneControl.from_knx(DPTBinary(True))
