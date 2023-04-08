"""Unit test for KNX DPT HVAC Operation modes."""
import pytest

from xknx.dpt import DPTArray, DPTControllerStatus, DPTHVACMode
from xknx.dpt.dpt_hvac_mode import HVACOperationMode
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTControllerStatus:
    """Test class for KNX DPT HVAC Operation modes."""

    def test_mode_to_knx(self):
        """Test parsing DPTHVACMode to KNX."""
        assert DPTHVACMode.to_knx(HVACOperationMode.AUTO) == DPTArray((0x00,))
        assert DPTHVACMode.to_knx(HVACOperationMode.COMFORT) == DPTArray((0x01,))
        assert DPTHVACMode.to_knx(HVACOperationMode.STANDBY) == DPTArray((0x02,))
        assert DPTHVACMode.to_knx(HVACOperationMode.NIGHT) == DPTArray((0x03,))
        assert DPTHVACMode.to_knx(HVACOperationMode.FROST_PROTECTION) == DPTArray(
            (0x04,)
        )

    def test_mode_to_knx_wrong_value(self):
        """Test serializing DPTHVACMode to KNX with wrong value."""
        with pytest.raises(ConversionError):
            DPTHVACMode.to_knx(5)

    def test_mode_from_knx(self):
        """Test parsing DPTHVACMode from KNX."""
        assert DPTHVACMode.from_knx(DPTArray((0x00,))) == HVACOperationMode.AUTO
        assert DPTHVACMode.from_knx(DPTArray((0x01,))) == HVACOperationMode.COMFORT
        assert DPTHVACMode.from_knx(DPTArray((0x02,))) == HVACOperationMode.STANDBY
        assert DPTHVACMode.from_knx(DPTArray((0x03,))) == HVACOperationMode.NIGHT
        assert (
            DPTHVACMode.from_knx(DPTArray((0x04,)))
            == HVACOperationMode.FROST_PROTECTION
        )

    def test_controller_status_to_knx(self):
        """Test serializing DPTControllerStatus to KNX."""
        with pytest.raises(ConversionError):
            DPTControllerStatus.to_knx(HVACOperationMode.AUTO)
        assert DPTControllerStatus.to_knx(HVACOperationMode.COMFORT) == DPTArray(
            (0x21,)
        )
        assert DPTControllerStatus.to_knx(HVACOperationMode.STANDBY) == DPTArray(
            (0x22,)
        )
        assert DPTControllerStatus.to_knx(HVACOperationMode.NIGHT) == DPTArray((0x24,))
        assert DPTControllerStatus.to_knx(
            HVACOperationMode.FROST_PROTECTION
        ) == DPTArray((0x28,))

    def test_controller_status_to_knx_wrong_value(self):
        """Test serializing DPTControllerStatus to KNX with wrong value."""
        with pytest.raises(ConversionError):
            DPTControllerStatus.to_knx(5)

    def test_controller_status_from_knx(self):
        """Test parsing DPTControllerStatus from KNX."""
        assert (
            DPTControllerStatus.from_knx(DPTArray((0x21,))) == HVACOperationMode.COMFORT
        )
        assert (
            DPTControllerStatus.from_knx(DPTArray((0x22,))) == HVACOperationMode.STANDBY
        )
        assert (
            DPTControllerStatus.from_knx(DPTArray((0x24,))) == HVACOperationMode.NIGHT
        )
        assert (
            DPTControllerStatus.from_knx(DPTArray((0x28,)))
            == HVACOperationMode.FROST_PROTECTION
        )

    def test_controller_status_from_knx_other_bits_set(self):
        """Test parsing DPTControllerStatus from KNX."""
        assert (
            DPTControllerStatus.from_knx(DPTArray((0x21,))) == HVACOperationMode.COMFORT
        )
        assert (
            DPTControllerStatus.from_knx(DPTArray((0x23,))) == HVACOperationMode.STANDBY
        )
        assert (
            DPTControllerStatus.from_knx(DPTArray((0x27,))) == HVACOperationMode.NIGHT
        )
        assert (
            DPTControllerStatus.from_knx(DPTArray((0x2F,)))
            == HVACOperationMode.FROST_PROTECTION
        )

    def test_mode_from_knx_wrong_value(self):
        """Test parsing of DPTControllerStatus with wrong value)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTHVACMode.from_knx(DPTArray((1, 2)))

    def test_mode_from_knx_wrong_code(self):
        """Test parsing of DPTHVACMode with wrong code."""
        with pytest.raises(ConversionError):
            DPTHVACMode.from_knx(DPTArray((0x05,)))

    def test_controller_status_from_knx_wrong_value(self):
        """Test parsing of DPTControllerStatus with wrong value)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTControllerStatus.from_knx(DPTArray((1, 2)))

    def test_controller_status_from_knx_wrong_code(self):
        """Test parsing of DPTControllerStatus with wrong code."""
        with pytest.raises(ConversionError):
            DPTControllerStatus.from_knx(DPTArray((0x00,)))
