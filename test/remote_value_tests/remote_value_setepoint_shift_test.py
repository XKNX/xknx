"""Unit test for RemoteValueSensor objects."""
import pytest
from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, DPTTemperature, DPTValue1Count
from xknx.exceptions import ConversionError
from xknx.remote_value.remote_value_setpoint_shift import (
    RemoteValueSetpointShift,
    SetpointShiftMode,
)


class TestRemoteValueSetpointShift:
    """Test class for RemoteValueSensor objects."""

    def test_wrong_setpoint_shift_mode(self):
        """Test initializing with wrong value_type."""
        xknx = XKNX()
        with pytest.raises(AttributeError):
            RemoteValueSetpointShift(xknx=xknx, setpoint_shift_mode=1)

    def test_payload_valid_mode_assignment(self):
        """Test if setpoint_shift_mode is assigned properly by payload length."""
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(xknx=xknx)
        dpt_6_payload = DPTArray(DPTValue1Count.to_knx(1))
        dpt_9_payload = DPTArray(DPTTemperature.to_knx(1))

        assert remote_value.payload_valid(DPTBinary(0)) is None
        assert remote_value.payload_valid(DPTArray((0, 1, 2))) is None

        # DPT 6 - payload_length 1
        assert remote_value.dpt_class is None
        assert remote_value.payload_valid(dpt_6_payload) == dpt_6_payload
        assert remote_value.dpt_class == SetpointShiftMode.DPT6010.value
        #   DPT 9 is invalid now
        assert remote_value.payload_valid(dpt_9_payload) is None

        remote_value.dpt_class = None
        # DPT 9 - payload_length 2
        assert remote_value.payload_valid(dpt_9_payload) == dpt_9_payload
        assert remote_value.dpt_class == SetpointShiftMode.DPT9002.value
        #   DPT 6 is invalid now
        assert remote_value.payload_valid(dpt_6_payload) is None

    def test_payload_valid_preassigned_mode(self):
        """Test if setpoint_shift_mode is assigned properly by payload length."""
        xknx = XKNX()
        remote_value_6 = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT6010
        )
        remote_value_9 = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT9002
        )
        dpt_6_payload = DPTArray(DPTValue1Count.to_knx(1))
        dpt_9_payload = DPTArray(DPTTemperature.to_knx(1))

        assert remote_value_6.dpt_class == DPTValue1Count
        assert remote_value_6.payload_valid(None) is None
        assert remote_value_6.payload_valid(dpt_9_payload) is None
        assert remote_value_6.payload_valid(DPTArray((1, 2, 3, 4))) is None
        assert remote_value_6.payload_valid(DPTBinary(1)) is None
        assert remote_value_6.payload_valid(dpt_6_payload) == dpt_6_payload

        assert remote_value_9.dpt_class == DPTTemperature
        assert remote_value_9.payload_valid(None) is None
        assert remote_value_9.payload_valid(dpt_6_payload) is None
        assert remote_value_9.payload_valid(DPTArray((1, 2, 3))) is None
        assert remote_value_9.payload_valid(DPTBinary(1)) is None
        assert remote_value_9.payload_valid(dpt_9_payload) == dpt_9_payload

    def test_to_knx_uninitialized(self):
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(xknx=xknx)

        assert remote_value.dpt_class is None
        with pytest.raises(ConversionError):
            remote_value.to_knx(1)

    def test_to_knx_dpt_6(self):
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT6010
        )
        assert remote_value.setpoint_shift_step == 0.1
        assert remote_value.to_knx(1) == DPTArray((10,))

    def test_to_knx_dpt_9(self):
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT9002
        )
        assert remote_value.to_knx(1) == DPTArray((0x00, 0x64))

    def test_from_knx_uninitialized(self):
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(xknx=xknx)
        with pytest.raises(AssertionError):
            remote_value.from_knx(1)
        # assign DPT 9.002 mode
        remote_value.payload_valid(DPTArray((0x00, 0x64)))
        assert remote_value.from_knx(DPTArray((0x07, 0xD0))) == 20
        # wrong payload length raises, once assigned
        with pytest.raises(ConversionError):
            remote_value.from_knx(DPTArray((10,)))

    def test_from_knx_dpt_6(self):
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT6010
        )
        assert remote_value.setpoint_shift_step == 0.1
        assert remote_value.from_knx(DPTArray((10,))) == 1

    def test_from_knx_dpt_9(self):
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT9002
        )
        assert remote_value.from_knx(DPTArray((0x00, 0x64))) == 1
