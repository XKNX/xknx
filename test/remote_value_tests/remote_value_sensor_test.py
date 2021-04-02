"""Unit test for RemoteValueSensor objects."""
import pytest
from xknx import XKNX
from xknx.dpt import DPTBase
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueSensor


class TestRemoteValueSensor:
    """Test class for RemoteValueSensor objects."""

    def test_wrong_value_type(self):
        """Test initializing with wrong value_type."""
        xknx = XKNX()
        with pytest.raises(ConversionError):
            RemoteValueSensor(xknx=xknx, value_type="wrong_value_type")

    def test_payload_length_defined(self):
        """Test if all members of DPTMAP implement payload_length."""
        for dpt_class in DPTBase.__recursive_subclasses__():
            assert isinstance(dpt_class.payload_length, int)
