"""Unit test for DPTControlStepCode objects."""
import pytest

from xknx.dpt import (
    DPTBinary,
    DPTControlStartStop,
    DPTControlStartStopBlinds,
    DPTControlStartStopDimming,
    DPTControlStepCode,
    DPTControlStepwise,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTControlStepCode:
    """Test class for DPTControlStepCode objects."""

    def test_to_knx(self):
        """Test serializing values to DPTControlStepCode."""
        for rawref in range(16):
            control = 1 if rawref >> 3 else 0
            raw = DPTControlStepCode.to_knx(
                {"control": control, "step_code": rawref & 0x07}
            )
            assert raw == DPTBinary(rawref)

    def test_to_knx_wrong_type(self):
        """Test serializing wrong type to DPTControlStepCode."""
        with pytest.raises(ConversionError):
            DPTControlStepCode.to_knx("")
        with pytest.raises(ConversionError):
            DPTControlStepCode.to_knx(0)

    def test_to_knx_wrong_keys(self):
        """Test serializing map with missing keys to DPTControlStepCode."""
        with pytest.raises(ConversionError):
            DPTControlStepCode.to_knx({"control": 0})
        with pytest.raises(ConversionError):
            DPTControlStepCode.to_knx({"step_code": 0})

    def test_to_knx_wrong_value_types(self):
        """Test serializing map with keys of invalid type to DPTControlStepCode."""
        with pytest.raises(ConversionError):
            DPTControlStepCode.to_knx({"control": ""})
        with pytest.raises(ConversionError):
            DPTControlStepCode.to_knx({"step_code": ""})

    def test_to_knx_wrong_values(self):
        """Test serializing map with keys of invalid values to DPTControlStepCode."""
        # with self.assertRaises(ConversionError):
        #     DPTControlStepCode.to_knx({"control": -1, "step_code": 0})
        # with self.assertRaises(ConversionError):
        #     DPTControlStepCode.to_knx({"control": 2, "step_code": 0})
        with pytest.raises(ConversionError):
            DPTControlStepCode.to_knx({"control": 0, "step_code": -1})
        with pytest.raises(ConversionError):
            DPTControlStepCode.to_knx({"control": 0, "step_code": 0x8})

    def test_from_knx(self):
        """Test parsing DPTControlStepCode types from KNX."""
        for raw in range(16):
            control = 1 if raw >> 3 else 0
            valueref = {"control": control, "step_code": raw & 0x07}
            value = DPTControlStepCode.from_knx(DPTBinary((raw,)))
            assert value == valueref

    def test_from_knx_wrong_value(self):
        """Test parsing invalid DPTControlStepCode type from KNX."""
        with pytest.raises(ConversionError):
            DPTControlStepCode.from_knx(DPTBinary((0x1F,)))

    def test_unit(self):
        """Test unit_of_measurement function."""
        assert DPTControlStepCode.unit is None


class TestDPTControlStepwise:
    """Test class for DPTControlStepwise objects."""

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            (0xF, 1),
            (0xE, 3),
            (0xD, 6),
            (0xC, 12),
            (0xB, 25),
            (0xA, 50),
            (0x9, 100),
            (0x7, -1),
            (0x6, -3),
            (0x5, -6),
            (0x4, -12),
            (0x3, -25),
            (0x2, -50),
            (0x1, -100),
            (0x0, 0),
        ],
    )
    def test_to_knx(self, raw, value):
        """Test serializing values to DPTControlStepwise."""
        assert DPTControlStepwise.to_knx(value) == DPTBinary(raw)

    def test_to_knx_wrong_type(self):
        """Test serializing wrong type to DPTControlStepwise."""
        with pytest.raises(ConversionError):
            DPTControlStepwise.to_knx("")

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            (0xF, 1),
            (0xE, 3),
            (0xD, 6),
            (0xC, 12),
            (0xB, 25),
            (0xA, 50),
            (0x9, 100),
            (0x8, 0),
            (0x7, -1),
            (0x6, -3),
            (0x5, -6),
            (0x4, -12),
            (0x3, -25),
            (0x2, -50),
            (0x1, -100),
            (0x0, 0),
        ],
    )
    def test_from_knx(self, raw, value):
        """Test parsing DPTControlStepwise types from KNX."""
        assert DPTControlStepwise.from_knx(DPTBinary(raw)) == value

    def test_from_knx_wrong_value(self):
        """Test parsing invalid DPTControlStepwise type from KNX."""
        with pytest.raises(ConversionError):
            DPTControlStepwise.from_knx(DPTBinary(0x1F))

    def test_unit(self):
        """Test unit_of_measurement function."""
        assert DPTControlStepwise.unit == "%"


class TestDPTControlStartStop:
    """Test class for DPTControlStartStop objects."""

    def test_mode_to_knx(self):
        """Test serializing dimming commands to KNX."""
        assert DPTControlStartStopDimming.to_knx(
            DPTControlStartStopDimming.Direction.INCREASE
        ) == DPTBinary(9)
        assert DPTControlStartStopDimming.to_knx(
            DPTControlStartStopDimming.Direction.DECREASE
        ) == DPTBinary(1)
        assert DPTControlStartStopDimming.to_knx(
            DPTControlStartStopDimming.Direction.STOP
        ) == DPTBinary(0)

    def test_mode_to_knx_wrong_value(self):
        """Test serializing invalid data type to KNX."""
        with pytest.raises(ConversionError):
            DPTControlStartStopDimming.to_knx(1)

    def test_mode_from_knx(self):
        """Test parsing dimming commands from KNX."""
        for i in range(16):
            if i > 8:
                expected_direction = DPTControlStartStopDimming.Direction.INCREASE
            elif i in (0, 8):
                expected_direction = DPTControlStartStopDimming.Direction.STOP
            elif i < 8:
                expected_direction = DPTControlStartStopDimming.Direction.DECREASE
            assert (
                DPTControlStartStopDimming.from_knx(DPTBinary((i,)))
                == expected_direction
            )

    def test_mode_from_knx_wrong_value(self):
        """Test serializing invalid data type to KNX."""
        with pytest.raises(CouldNotParseTelegram):
            DPTControlStartStopDimming.from_knx(1)

    def test_direction_names(self):
        """Test names of Direction Enum."""
        assert str(DPTControlStartStop.Direction.INCREASE) == "Increase"
        assert str(DPTControlStartStop.Direction.DECREASE) == "Decrease"
        assert str(DPTControlStartStop.Direction.STOP) == "Stop"


class TestDPTControlStartStopDimming:
    """Test class for DPTControlStartStopDimming objects."""

    def test_direction_names(self):
        """Test names of Direction Enum."""
        assert str(DPTControlStartStopDimming.Direction.INCREASE) == "Increase"
        assert str(DPTControlStartStopDimming.Direction.DECREASE) == "Decrease"
        assert str(DPTControlStartStopDimming.Direction.STOP) == "Stop"

    def test_direction_values(self):
        """Test values of Direction Enum."""
        assert (
            DPTControlStartStopDimming.Direction.DECREASE.value
            == DPTControlStartStop.Direction.DECREASE.value
        )
        assert (
            DPTControlStartStopDimming.Direction.INCREASE.value
            == DPTControlStartStop.Direction.INCREASE.value
        )
        assert (
            DPTControlStartStopDimming.Direction.STOP.value
            == DPTControlStartStop.Direction.STOP.value
        )


class TestDPTControlStartStopBlinds:
    """Test class for DPTControlStartStopBlinds objects."""

    def test_direction_names(self):
        """Test names of Direction Enum."""
        assert str(DPTControlStartStopBlinds.Direction.DOWN) == "Down"
        assert str(DPTControlStartStopBlinds.Direction.UP) == "Up"
        assert str(DPTControlStartStopBlinds.Direction.STOP) == "Stop"

    def test_direction_values(self):
        """Test values of Direction Enum."""
        assert (
            DPTControlStartStopBlinds.Direction.UP.value
            == DPTControlStartStop.Direction.DECREASE.value
        )
        assert (
            DPTControlStartStopBlinds.Direction.DOWN.value
            == DPTControlStartStop.Direction.INCREASE.value
        )
        assert (
            DPTControlStartStopBlinds.Direction.STOP.value
            == DPTControlStartStop.Direction.STOP.value
        )
