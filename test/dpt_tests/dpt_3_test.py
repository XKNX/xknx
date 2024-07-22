"""Unit test for DPT 3 objects."""

import pytest

from xknx.dpt import DPTArray, DPTBinary, DPTControlBlinds, DPTControlDimming
from xknx.dpt.dpt_1 import Step, UpDown
from xknx.dpt.dpt_3 import ControlBlinds, ControlDimming
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestControlData:
    """Test class for Control data objects."""

    @pytest.mark.parametrize(
        ("data", "dict_value"),
        [
            (
                ControlBlinds(control=UpDown.UP, step_code=0),
                {"control": "up", "step_code": 0},
            ),
            (
                ControlBlinds(control=UpDown.DOWN, step_code=7),
                {"control": "down", "step_code": 7},
            ),
            (
                ControlDimming(control=Step.DECREASE, step_code=5),
                {"control": "decrease", "step_code": 5},
            ),
            (
                ControlDimming(control=Step.INCREASE, step_code=0),
                {"control": "increase", "step_code": 0},
            ),
        ],
    )
    def test_dict(self, data, dict_value):
        """Test from_dict and as_dict methods."""
        test_dataclass = data.__class__
        assert test_dataclass.from_dict(dict_value) == data
        assert data.as_dict() == dict_value

    @pytest.mark.parametrize(
        "data",
        [
            {"control": 1, "step_code": "invalid"},
            {"control": "up", "step_code": "invalid"},
            {"control": "increase", "step_code": "invalid"},
            {"control": "down", "step_code": None},
            {"control": None, "step_code": 1},
            {"control": "invalid", "step_code": 0},
            {"control": 2, "step_code": 4},
        ],
    )
    def test_dict_invalid(self, data):
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            ControlBlinds.from_dict(data)
        with pytest.raises(ValueError):
            ControlDimming.from_dict(data)


@pytest.mark.parametrize(
    ("dpt", "dpt_data", "control_enum"),
    [
        (DPTControlDimming, ControlDimming, Step),
        (DPTControlBlinds, ControlBlinds, UpDown),
    ],
)
class TestDPTControlStepCode:
    """Test class for DPT 3 objects."""

    def test_to_knx(self, dpt, dpt_data, control_enum):
        """Test serializing values."""
        for rawref in range(16):
            control = 1 if rawref >> 3 else 0
            raw = dpt.to_knx(
                dpt_data(
                    control=control_enum(control),
                    step_code=rawref & 0x07,
                )
            )
            assert raw == DPTBinary(rawref)

    def test_to_knx_dict(self, dpt, dpt_data, control_enum):
        """Test serializing values from dict."""
        for rawref in range(16):
            control = 1 if rawref >> 3 else 0
            raw = dpt.to_knx(
                {
                    "control": control_enum(control).name.lower(),
                    "step_code": rawref & 0x07,
                }
            )
            assert raw == DPTBinary(rawref)

    def test_to_knx_wrong_type(self, dpt, dpt_data, control_enum):
        """Test serializing wrong type."""
        with pytest.raises(ConversionError):
            dpt.to_knx("")
        with pytest.raises(ConversionError):
            dpt.to_knx(0)

    def test_to_knx_missing_keys(self, dpt, dpt_data, control_enum):
        """Test serializing map with missing keys."""
        with pytest.raises(ConversionError):
            dpt.to_knx({"control": 0})
        with pytest.raises(ConversionError):
            dpt.to_knx({"step_code": 0})

    def test_to_knx_wrong_value_types(self, dpt, dpt_data, control_enum):
        """Test serializing map with keys of invalid type."""
        with pytest.raises(ConversionError):
            dpt.to_knx({"control": "", "step_code": 0})
        with pytest.raises(ConversionError):
            dpt.to_knx({"control": 0, "step_code": ""})

    def test_to_knx_wrong_values(self, dpt, dpt_data, control_enum):
        """Test serializing with invalid values."""
        with pytest.raises(ConversionError):
            dpt.to_knx({"control": -1, "step_code": 0})
        with pytest.raises(ConversionError):
            dpt.to_knx({"control": 2, "step_code": 0})
        with pytest.raises(ConversionError):
            dpt.to_knx({"control": 0, "step_code": -1})
        with pytest.raises(ConversionError):
            dpt.to_knx(dpt_data(control=control_enum(0), step_code=8))

    def test_from_knx(self, dpt, dpt_data, control_enum):
        """Test parsing from KNX."""
        for raw in range(16):
            control = 1 if raw >> 3 else 0
            valueref = dpt_data(
                control=control_enum(control),
                step_code=raw & 0x07,
            )
            value = dpt.from_knx(DPTBinary((raw,)))
            assert value == valueref

    def test_from_knx_wrong_value(self, dpt, dpt_data, control_enum):
        """Test parsing invalid values from KNX."""
        with pytest.raises(CouldNotParseTelegram):
            dpt.from_knx(DPTBinary((0x1F,)))
        with pytest.raises(CouldNotParseTelegram):
            dpt.from_knx(DPTArray((1,)))
