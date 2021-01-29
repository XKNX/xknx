"""Unit test for DPTControlStepCode objects."""
import unittest

from xknx.dpt import (
    DPTControlStartStop,
    DPTControlStartStopBlinds,
    DPTControlStartStopDimming,
    DPTControlStepCode,
    DPTControlStepwise,
)
from xknx.exceptions import ConversionError


class TestDPTControlStepCode(unittest.TestCase):
    """Test class for DPTControlStepCode objects."""

    def test_to_knx(self):
        """Test serializing values to DPTControlStepCode."""
        for rawref in range(16):
            control = 1 if rawref >> 3 else 0
            raw = DPTControlStepCode.to_knx(
                {"control": control, "step_code": rawref & 0x07}
            )
            self.assertEqual(raw, rawref)

    def test_to_knx_wrong_type(self):
        """Test serializing wrong type to DPTControlStepCode."""
        with self.assertRaises(ConversionError):
            DPTControlStepCode.to_knx("")
        with self.assertRaises(ConversionError):
            DPTControlStepCode.to_knx(0)

    def test_to_knx_wrong_keys(self):
        """Test serializing map with missing keys to DPTControlStepCode."""
        with self.assertRaises(ConversionError):
            DPTControlStepCode.to_knx({"control": 0})
        with self.assertRaises(ConversionError):
            DPTControlStepCode.to_knx({"step_code": 0})

    def test_to_knx_wrong_value_types(self):
        """Test serializing map with keys of invalid type to DPTControlStepCode."""
        with self.assertRaises(ConversionError):
            DPTControlStepCode.to_knx({"control": ""})
        with self.assertRaises(ConversionError):
            DPTControlStepCode.to_knx({"step_code": ""})

    def test_to_knx_wrong_values(self):
        """Test serializing map with keys of invalid values to DPTControlStepCode."""
        with self.assertRaises(ConversionError):
            DPTControlStepCode.to_knx({"control": -1, "step_code": 0})
        with self.assertRaises(ConversionError):
            DPTControlStepCode.to_knx({"control": 2, "step_code": 0})
        with self.assertRaises(ConversionError):
            DPTControlStepCode.to_knx({"control": 0, "step_code": -1})
        with self.assertRaises(ConversionError):
            DPTControlStepCode.to_knx({"control": 0, "step_code": 0x8})

    def test_from_knx(self):
        """Test parsing DPTControlStepCode types from KNX."""
        for raw in range(16):
            control = 1 if raw >> 3 else 0
            valueref = {"control": control, "step_code": raw & 0x07}
            value = DPTControlStepCode.from_knx(raw)
            self.assertEqual(value, valueref)

    def test_from_knx_wrong_value(self):
        """Test parsing invalid DPTControlStepCode type from KNX."""
        with self.assertRaises(ConversionError):
            DPTControlStepCode.from_knx(0x1F)

    def test_unit(self):
        """Test unit_of_measurement function."""
        self.assertEqual(DPTControlStepCode.unit, "")


class TestDPTControlStepwise(unittest.TestCase):
    """Test class for DPTControlStepwise objects."""

    def test_to_knx(self):
        """Test serializing values to DPTControlStepwise."""
        self.assertEqual(DPTControlStepwise.to_knx(1), 0xF)
        self.assertEqual(DPTControlStepwise.to_knx(3), 0xE)
        self.assertEqual(DPTControlStepwise.to_knx(6), 0xD)
        self.assertEqual(DPTControlStepwise.to_knx(12), 0xC)
        self.assertEqual(DPTControlStepwise.to_knx(25), 0xB)
        self.assertEqual(DPTControlStepwise.to_knx(50), 0xA)
        self.assertEqual(DPTControlStepwise.to_knx(100), 0x9)
        self.assertEqual(DPTControlStepwise.to_knx(-1), 0x7)
        self.assertEqual(DPTControlStepwise.to_knx(-3), 0x6)
        self.assertEqual(DPTControlStepwise.to_knx(-6), 0x5)
        self.assertEqual(DPTControlStepwise.to_knx(-12), 0x4)
        self.assertEqual(DPTControlStepwise.to_knx(-25), 0x3)
        self.assertEqual(DPTControlStepwise.to_knx(-50), 0x2)
        self.assertEqual(DPTControlStepwise.to_knx(-100), 0x1)
        self.assertEqual(DPTControlStepwise.to_knx(0), 0x0)

    def test_to_knx_wrong_type(self):
        """Test serializing wrong type to DPTControlStepwise."""
        with self.assertRaises(ConversionError):
            DPTControlStepwise.to_knx("")

    def test_from_knx(self):
        """Test parsing DPTControlStepwise types from KNX."""
        self.assertEqual(DPTControlStepwise.from_knx(0xF), 1)
        self.assertEqual(DPTControlStepwise.from_knx(0xE), 3)
        self.assertEqual(DPTControlStepwise.from_knx(0xD), 6)
        self.assertEqual(DPTControlStepwise.from_knx(0xC), 12)
        self.assertEqual(DPTControlStepwise.from_knx(0xB), 25)
        self.assertEqual(DPTControlStepwise.from_knx(0xA), 50)
        self.assertEqual(DPTControlStepwise.from_knx(0x9), 100)
        self.assertEqual(DPTControlStepwise.from_knx(0x8), 0)
        self.assertEqual(DPTControlStepwise.from_knx(0x7), -1)
        self.assertEqual(DPTControlStepwise.from_knx(0x6), -3)
        self.assertEqual(DPTControlStepwise.from_knx(0x5), -6)
        self.assertEqual(DPTControlStepwise.from_knx(0x4), -12)
        self.assertEqual(DPTControlStepwise.from_knx(0x3), -25)
        self.assertEqual(DPTControlStepwise.from_knx(0x2), -50)
        self.assertEqual(DPTControlStepwise.from_knx(0x1), -100)
        self.assertEqual(DPTControlStepwise.from_knx(0x0), 0)

    def test_from_knx_wrong_value(self):
        """Test parsing invalid DPTControlStepwise type from KNX."""
        with self.assertRaises(ConversionError):
            DPTControlStepwise.from_knx(0x1F)

    def test_unit(self):
        """Test unit_of_measurement function."""
        self.assertEqual(DPTControlStepwise.unit, "%")


class TestDPTControlStartStop(unittest.TestCase):
    """Test class for DPTControlStartStop objects."""

    def test_mode_to_knx(self):
        """Test serializing dimming commands to KNX."""
        self.assertEqual(
            DPTControlStartStopDimming.to_knx(
                DPTControlStartStopDimming.Direction.INCREASE
            ),
            9,
        )
        self.assertEqual(
            DPTControlStartStopDimming.to_knx(
                DPTControlStartStopDimming.Direction.DECREASE
            ),
            1,
        )
        self.assertEqual(
            DPTControlStartStopDimming.to_knx(
                DPTControlStartStopDimming.Direction.STOP
            ),
            0,
        )

    def test_mode_to_knx_wrong_value(self):
        """Test serializing invalid data type to KNX."""
        with self.assertRaises(ConversionError):
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
            self.assertEqual(DPTControlStartStopDimming.from_knx(i), expected_direction)

    def test_mode_from_knx_wrong_value(self):
        """Test serializing invalid data type to KNX."""
        with self.assertRaises(ConversionError):
            DPTControlStartStopDimming.from_knx((1, 2))

    def test_direction_names(self):
        """Test names of Direction Enum."""
        self.assertEqual(str(DPTControlStartStop.Direction.INCREASE), "Increase")
        self.assertEqual(str(DPTControlStartStop.Direction.DECREASE), "Decrease")
        self.assertEqual(str(DPTControlStartStop.Direction.STOP), "Stop")


class TestDPTControlStartStopDimming(TestDPTControlStartStop):
    """Test class for DPTControlStartStopDimming objects."""

    def test_direction_names(self):
        """Test names of Direction Enum."""
        self.assertEqual(str(DPTControlStartStopDimming.Direction.INCREASE), "Increase")
        self.assertEqual(str(DPTControlStartStopDimming.Direction.DECREASE), "Decrease")
        self.assertEqual(str(DPTControlStartStopDimming.Direction.STOP), "Stop")

    def test_direction_values(self):
        """Test values of Direction Enum."""
        # pylint: disable=no-member
        self.assertEqual(
            DPTControlStartStopDimming.Direction.DECREASE.value,
            DPTControlStartStop.Direction.DECREASE.value,
        )
        self.assertEqual(
            DPTControlStartStopDimming.Direction.INCREASE.value,
            DPTControlStartStop.Direction.INCREASE.value,
        )
        self.assertEqual(
            DPTControlStartStopDimming.Direction.STOP.value,
            DPTControlStartStop.Direction.STOP.value,
        )


class TestDPTControlStartStopBlinds(unittest.TestCase):
    """Test class for DPTControlStartStopBlinds objects."""

    def test_direction_names(self):
        """Test names of Direction Enum."""
        self.assertEqual(str(DPTControlStartStopBlinds.Direction.DOWN), "Down")
        self.assertEqual(str(DPTControlStartStopBlinds.Direction.UP), "Up")
        self.assertEqual(str(DPTControlStartStopBlinds.Direction.STOP), "Stop")

    def test_direction_values(self):
        """Test values of Direction Enum."""
        # pylint: disable=no-member
        self.assertEqual(
            DPTControlStartStopBlinds.Direction.UP.value,
            DPTControlStartStop.Direction.DECREASE.value,
        )
        self.assertEqual(
            DPTControlStartStopBlinds.Direction.DOWN.value,
            DPTControlStartStop.Direction.INCREASE.value,
        )
        self.assertEqual(
            DPTControlStartStopBlinds.Direction.STOP.value,
            DPTControlStartStop.Direction.STOP.value,
        )
