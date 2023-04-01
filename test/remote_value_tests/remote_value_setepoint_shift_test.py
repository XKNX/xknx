"""Unit test for RemoteValueSetpointShift objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, DPTTemperature, DPTValue1Count
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value.remote_value_setpoint_shift import (
    RemoteValueSetpointShift,
    SetpointShiftMode,
)


class TestRemoteValueSetpointShift:
    """Test class for RemoteValueSetpointShift objects."""

    def test_payload_valid_mode_assignment(self):
        """Test if setpoint_shift_mode is assigned properly by payload length."""
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(xknx=xknx)
        dpt_6_payload = DPTValue1Count.to_knx(1)
        dpt_9_payload = DPTTemperature.to_knx(1)

        with pytest.raises(CouldNotParseTelegram):
            remote_value.from_knx(DPTBinary(0))
        with pytest.raises(CouldNotParseTelegram):
            remote_value.from_knx(DPTArray((0, 1, 2)))

        # DPT 6 - payload_length 1
        assert remote_value.dpt_class is None
        # default setpoint_shift_step = 0.1
        assert remote_value.from_knx(dpt_6_payload) == 0.1
        assert remote_value.dpt_class == SetpointShiftMode.DPT6010.value
        with pytest.raises(CouldNotParseTelegram):
            # DPT 9 is invalid now
            remote_value.from_knx(dpt_9_payload)

        remote_value.dpt_class = None
        # DPT 9 - payload_length 2
        assert remote_value.from_knx(dpt_9_payload) == 1
        assert remote_value.dpt_class == SetpointShiftMode.DPT9002.value
        with pytest.raises(CouldNotParseTelegram):
            # DPT 6 is invalid now
            remote_value.from_knx(dpt_6_payload)

    def test_payload_valid_preassigned_mode(self):
        """Test if setpoint_shift_mode is assigned properly by payload length."""
        xknx = XKNX()
        remote_value_6 = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT6010
        )
        remote_value_9 = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT9002
        )
        dpt_6_payload = DPTValue1Count.to_knx(1)
        dpt_9_payload = DPTTemperature.to_knx(1)

        assert remote_value_6.dpt_class == DPTValue1Count
        with pytest.raises(CouldNotParseTelegram):
            remote_value_6.from_knx(None)
        with pytest.raises(CouldNotParseTelegram):
            remote_value_6.from_knx(dpt_9_payload)
        with pytest.raises(CouldNotParseTelegram):
            remote_value_6.from_knx(DPTArray((1, 2, 3, 4)))
        with pytest.raises(CouldNotParseTelegram):
            remote_value_6.from_knx(DPTBinary(1))
        assert remote_value_6.from_knx(dpt_6_payload) == 0.1

        assert remote_value_9.dpt_class == DPTTemperature
        with pytest.raises(CouldNotParseTelegram):
            remote_value_9.from_knx(None)
        with pytest.raises(CouldNotParseTelegram):
            remote_value_9.from_knx(dpt_6_payload)
        with pytest.raises(CouldNotParseTelegram):
            remote_value_9.from_knx(DPTArray((1, 2, 3)))
        with pytest.raises(CouldNotParseTelegram):
            remote_value_9.from_knx(DPTBinary(1))
        assert remote_value_9.from_knx(dpt_9_payload) == 1

    def test_to_knx_uninitialized(self):
        """Test to_knx raising ConversionError."""
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(xknx=xknx)

        assert remote_value.dpt_class is None
        with pytest.raises(ConversionError):
            remote_value.to_knx(1)

    def test_to_knx_dpt_6(self):
        """Test to_knx returning DPT 6.010 payload."""
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT6010
        )
        assert remote_value.setpoint_shift_step == 0.1
        assert remote_value.to_knx(1) == DPTArray((10,))

    def test_to_knx_dpt_9(self):
        """Test to_knx returning DPT 9.002 payload."""
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT9002
        )
        assert remote_value.to_knx(1) == DPTArray((0x00, 0x64))

    def test_from_knx_uninitialized(self):
        """Test from_knx for uninitialized setpoint_shift_mode."""
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(xknx=xknx)
        with pytest.raises(CouldNotParseTelegram):
            remote_value.from_knx(1)
        # assign DPT 9.002 mode
        assert remote_value.from_knx(DPTArray((0x00, 0x64))) == 1
        assert remote_value.from_knx(DPTArray((0x07, 0xD0))) == 20
        # wrong payload length raises, once assigned
        with pytest.raises(CouldNotParseTelegram):
            remote_value.from_knx(DPTArray((10,)))

    def test_from_knx_dpt_6(self):
        """Test from_knx for DPT 6.010 setpoint_shift_mode."""
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT6010
        )
        assert remote_value.setpoint_shift_step == 0.1
        assert remote_value.from_knx(DPTArray((10,))) == 1

    def test_from_knx_dpt_9(self):
        """Test from_knx for DPT 9.002 setpoint_shift_mode."""
        xknx = XKNX()
        remote_value = RemoteValueSetpointShift(
            xknx=xknx, setpoint_shift_mode=SetpointShiftMode.DPT9002
        )
        assert remote_value.from_knx(DPTArray((0x00, 0x64))) == 1
