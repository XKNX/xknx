"""Unit test for KNX payload objects."""
import pytest

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError


class TestDPT:
    """Test class for KNX binary/integer objects."""

    def test_compare_binary(self):
        """Test comparison of DPTBinary objects."""
        assert DPTBinary(0) == DPTBinary(0)
        assert DPTBinary(0) == DPTBinary(False)
        assert DPTBinary(1) == DPTBinary(True)
        assert DPTBinary(2) == DPTBinary(2)
        assert DPTBinary(1) != DPTBinary(4)
        assert DPTBinary(2) != DPTBinary(0)
        assert DPTBinary(0) != DPTBinary(2)

    def test_compare_array(self):
        """Test comparison of DPTArray objects."""
        assert DPTArray(()) == DPTArray(())
        assert DPTArray([1]) == DPTArray((1,))
        assert DPTArray([1, 2, 3]) == DPTArray([1, 2, 3])
        assert DPTArray([1, 2, 3]) == DPTArray((1, 2, 3))
        assert DPTArray((1, 2, 3)) == DPTArray([1, 2, 3])
        assert DPTArray((1, 2, 3)) != DPTArray([1, 2, 3, 4])
        assert DPTArray((1, 2, 3, 4)) != DPTArray([1, 2, 3])
        assert DPTArray((1, 2, 3)) != DPTArray([1, 2, 4])

    def test_compare_none(self):
        """Test comparison DPTArray objects with None."""
        assert DPTArray(()) is not None
        assert None is not DPTArray(())
        assert DPTBinary(0) is not None
        assert None is not DPTBinary(0)
        assert DPTArray((1, 2, 3)) is not None
        assert None is not DPTArray((1, 2, 3))
        assert DPTBinary(1) is not None
        assert None is not DPTBinary(1)

    def test_compare_array_binary(self):
        """Test comparison of empty DPTArray objects with DPTBinary objects."""
        assert DPTArray(()) != DPTBinary(0)
        assert DPTBinary(0) != DPTArray(())
        assert DPTBinary(0) != DPTArray(0)
        assert DPTBinary(1) != DPTArray(1)
        assert DPTArray((1, 2, 3)) != DPTBinary(2)
        assert DPTBinary(2) != DPTArray((1, 2, 3))
        assert DPTArray((2,)) != DPTBinary(2)
        assert DPTBinary(2) != DPTArray((2,))

    def test_dpt_binary_assign(self):
        """Test initialization of DPTBinary objects."""
        assert DPTBinary(8).value == 8

    def test_dpt_binary_assign_limit_exceeded(self):
        """Test initialization of DPTBinary objects with wrong value (value exceeded)."""
        with pytest.raises(ConversionError):
            DPTBinary(DPTBinary.APCI_BITMASK + 1)

    def test_dpt_init_with_string(self):
        """Teest initialization of DPTBinary object with wrong value (wrong type)."""
        with pytest.raises(TypeError):
            DPTBinary("bla")

    def test_dpt_array_init_with_string(self):
        """Test initialization of DPTArray object with wrong value (wrong type)."""
        with pytest.raises(TypeError):
            DPTArray("bla")

    def test_dpt_representation(self):
        """Test representation of DPTBinary and DPTArray."""
        assert DPTBinary(True).__repr__() == "DPTBinary(0x1)"
        assert DPTArray((5, 15)).__repr__() == "DPTArray((0x5, 0xf))"
