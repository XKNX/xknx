"""Unit test for RemoteValueSensor objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTValue1Ucount
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueNumeric, RemoteValueSensor


class TestRemoteValueSensor:
    """Test class for RemoteValueSensor objects."""

    def test_value_type(self):
        """Test initializing a value_type."""
        xknx = XKNX()
        assert RemoteValueSensor(xknx=xknx, value_type="pulse")
        assert RemoteValueSensor(xknx=xknx, value_type=9)
        assert RemoteValueSensor(xknx=xknx, value_type="9.021")
        assert RemoteValueSensor(xknx=xknx, value_type="string")

    def test_wrong_value_type(self):
        """Test initializing with wrong value_type."""
        xknx = XKNX()
        with pytest.raises(ConversionError):
            RemoteValueSensor(xknx=xknx, value_type="wrong_value_type")
        with pytest.raises(ConversionError):
            RemoteValueSensor(xknx=xknx, value_type="binary")
        with pytest.raises(ConversionError):
            RemoteValueSensor(xknx=xknx, value_type=1)
        with pytest.raises(ConversionError):
            RemoteValueSensor(xknx=xknx, value_type=2)
        with pytest.raises(ConversionError):
            RemoteValueSensor(xknx=xknx, value_type=None)
        with pytest.raises(ConversionError):
            RemoteValueSensor(xknx=xknx)

    def test_payload_length_defined(self):
        """Test if all members of DPTMAP implement payload_length."""
        for dpt_class in DPTBase.__recursive_subclasses__():
            assert isinstance(dpt_class.payload_length, int)

    def test_payload_invalid(self):
        """Test invalid payloads."""
        xknx = XKNX()
        remote_value = RemoteValueSensor(xknx=xknx, value_type="pulse")

        assert remote_value.dpt_class == DPTValue1Ucount
        with pytest.raises(CouldNotParseTelegram):
            remote_value.from_knx(None)
        with pytest.raises(CouldNotParseTelegram):
            remote_value.from_knx(DPTArray((1, 2, 3, 4)))
        with pytest.raises(CouldNotParseTelegram):
            remote_value.from_knx(DPTBinary(1))


class TestRemoteValueNumeric:
    """Test class for RemoteValueNumeric objects."""

    def test_value_type(self):
        """Test initializing a value_type."""
        xknx = XKNX()
        assert RemoteValueNumeric(xknx=xknx, value_type="pulse")
        assert RemoteValueNumeric(xknx=xknx, value_type=9)
        assert RemoteValueNumeric(xknx=xknx, value_type="9.021")

    def test_wrong_value_type(self):
        """Test initializing with wrong value_type."""
        xknx = XKNX()
        with pytest.raises(ConversionError):
            RemoteValueNumeric(xknx=xknx, value_type="string")
        with pytest.raises(ConversionError):
            RemoteValueNumeric(xknx=xknx, value_type=16)
        with pytest.raises(ConversionError):
            RemoteValueNumeric(xknx=xknx, value_type="binary")
        with pytest.raises(ConversionError):
            RemoteValueNumeric(xknx=xknx)
