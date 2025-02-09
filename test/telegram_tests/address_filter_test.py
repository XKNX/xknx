"""Unit test for Address class."""

import pytest

from xknx.exceptions import ConversionError
from xknx.telegram import AddressFilter
from xknx.telegram.address import GroupAddress, InternalGroupAddress


class TestAddressFilter:
    """Test class for Address."""

    def test_range_initialization(self) -> None:
        """Test Initialization of AddresFilter.Range."""
        assert AddressFilter.Range("*").get_range() == (0, 65535)
        assert AddressFilter.Range("5").get_range() == (5, 5)
        assert AddressFilter.Range("0").get_range() == (0, 0)
        assert AddressFilter.Range("3-5").get_range() == (3, 5)
        assert AddressFilter.Range("5-3").get_range() == (3, 5)
        assert AddressFilter.Range("-5").get_range() == (0, 5)
        assert AddressFilter.Range("5-").get_range() == (5, 65535)
        assert AddressFilter.Range("70-100").get_range() == (70, 100)

    def test_range_test(self) -> None:
        """Test matching within AddressFilter.Range."""
        range_filter = AddressFilter.Range("2-16")
        assert range_filter.match(10)
        assert range_filter.match(2)
        assert range_filter.match(16)
        assert not range_filter.match(1)
        assert not range_filter.match(17)

    def test_level_filter_test(self) -> None:
        """Test matching within AddressFilter.LevelFilter."""
        level_filter = AddressFilter.LevelFilter("2,4,8-10,13")
        assert not level_filter.match(1)
        assert level_filter.match(2)
        assert not level_filter.match(3)
        assert level_filter.match(4)
        assert not level_filter.match(5)
        assert level_filter.match(9)

    def test_address_filter_level3_3(self) -> None:
        """Test AddressFilter 3rd part of level3 addresses."""
        af1 = AddressFilter("1/2/3")
        assert af1.match("1/2/3")
        assert not af1.match("1/2/4")
        assert not af1.match("1/2/1")
        af2 = AddressFilter("1/2/2-3,5-")
        assert not af2.match("1/2/1")
        assert af2.match("1/2/3")
        assert not af2.match("1/2/4")
        assert af2.match("1/2/6")
        af3 = AddressFilter("1/2/*")
        assert af3.match("1/2/3")
        assert af3.match("1/2/5")

    def test_address_filter_level3_2(self) -> None:
        """Test AddressFilter 2nd part of level3 addresses."""
        af1 = AddressFilter("1/2/3")
        assert af1.match("1/2/3")
        assert not af1.match("1/3/3")
        assert not af1.match("1/1/3")
        af2 = AddressFilter("1/2-/3")
        assert not af2.match("1/1/3")
        assert af2.match("1/2/3")
        assert af2.match("1/5/3")
        af3 = AddressFilter("1/*/3")
        assert af3.match("1/4/3")
        assert af3.match("1/7/3")

    def test_address_filter_level3_1(self) -> None:
        """Test AddressFilter 1st part of level3 addresses."""
        af1 = AddressFilter("4/2/3")
        assert af1.match("4/2/3")
        assert not af1.match("2/2/3")
        assert not af1.match("10/2/3")
        af2 = AddressFilter("2-/4/3")
        assert not af2.match("1/4/3")
        assert af2.match("2/4/3")
        assert af2.match("10/4/3")
        af3 = AddressFilter("*/5/5")
        assert af3.match("2/5/5")
        assert af3.match("8/5/5")

    def test_address_filter_level2_2(self) -> None:
        """Test AddressFilter 2nd part of level2 addresses."""
        af1 = AddressFilter("2/3")
        assert af1.match("2/3")
        assert not af1.match("2/4")
        assert not af1.match("2/1")
        af2 = AddressFilter("2/3-4,7-")
        assert not af2.match("2/2")
        assert af2.match("2/3")
        assert not af2.match("2/6")
        assert af2.match("2/8")
        af3 = AddressFilter("2/*")
        assert af3.match("2/3")
        assert af3.match("2/5")

    def test_address_filter_level2_1(self) -> None:
        """Test AddressFilter 1st part of level2 addresses."""
        af1 = AddressFilter("4/2")
        assert af1.match("4/2")
        assert not af1.match("2/2")
        assert not af1.match("10/2")
        af2 = AddressFilter("2-3,8-/4")
        assert not af2.match("1/4")
        assert af2.match("2/4")
        assert not af2.match("7/4")
        assert af2.match("10/4")
        af3 = AddressFilter("*/5")
        assert af3.match("2/5")
        assert af3.match("8/5")

    def test_address_filter_free(self) -> None:
        """Test AddressFilter free format addresses."""
        af1 = AddressFilter("4")
        assert af1.match("4")
        assert not af1.match("1")
        assert not af1.match("10")
        af2 = AddressFilter("1,4,7-")
        assert af2.match("1")
        assert not af2.match("2")
        assert af2.match("4")
        assert not af2.match("6")
        assert af2.match("60")
        af3 = AddressFilter("*")
        assert af3.match("2")
        assert af3.match("8")

    def test_address_combined(self) -> None:
        """Test AddressFilter with complex filters."""
        af1 = AddressFilter("2-/2,3,5-/*")
        assert af1.match("2/3/8")
        assert af1.match("4/7/10")
        assert af1.match("2/7/10")
        assert not af1.match("1/7/10")
        assert not af1.match("2/4/10")
        assert not af1.match("2/1/10")

    def test_initialize_wrong_format(self) -> None:
        """Test if wrong address format raises exception."""
        with pytest.raises(ConversionError):
            AddressFilter("2-/2,3/4/5/1,5-/*")

    def test_adjust_range(self) -> None:
        """Test helper function _adjust_range."""
        assert (
            AddressFilter.Range._adjust_range(GroupAddress.MAX_FREE + 1)
            == GroupAddress.MAX_FREE
        )
        assert AddressFilter.Range._adjust_range(-1) == 0

    def test_internal_address_filter_exact(self) -> None:
        """Test AddressFilter for InternalGroupAddress."""
        af1 = AddressFilter("i-1")
        assert af1.match("i1")
        assert af1.match("i 1")
        assert af1.match("i-1")
        assert af1.match(InternalGroupAddress("i-1"))
        assert not af1.match("1")
        assert not af1.match(GroupAddress(1))

    def test_internal_address_filter_wildcard(self) -> None:
        """Test AddressFilter with wildcards for InternalGroupAddress."""
        af1 = AddressFilter("i-?")
        assert af1.match("i1")
        assert af1.match("i 2")
        assert af1.match("i-3")
        assert af1.match(InternalGroupAddress("i-4"))
        assert not af1.match("1")
        assert not af1.match(GroupAddress(1))
        assert not af1.match("i11")
        assert not af1.match("i 11")
        assert not af1.match("i-11")
        assert not af1.match(InternalGroupAddress("i-11"))

        af2 = AddressFilter("i-t?st")
        assert af2.match("it1st")
        assert af2.match("i t2st")
        assert af2.match("i-test")
        assert af2.match(InternalGroupAddress("i-test"))
        assert not af2.match("1")
        assert not af2.match(GroupAddress(1))
        assert not af2.match("i11")
        assert not af2.match("i tst")
        assert not af2.match("i-teest")
        assert not af2.match(InternalGroupAddress("i-tst"))

        af3 = AddressFilter("i-*")
        assert af3.match("i1")
        assert af3.match("i asdf")
        assert af3.match("i-3sdf")
        assert af3.match(InternalGroupAddress("i-4"))
        assert not af3.match("1")
        assert not af3.match(GroupAddress(1))
        assert af3.match("i11")
        assert af3.match("i 11??")
        assert af3.match("i-11*")
        assert af3.match(InternalGroupAddress("i-11"))

        af4 = AddressFilter("i-t*t")
        assert af4.match("it1t")
        assert af4.match("i t22t")
        assert af4.match("i-testt")
        assert af4.match("i-tt")
        assert af4.match(InternalGroupAddress("i-t333t"))
        assert not af4.match("1")
        assert not af4.match(GroupAddress(1))
        assert not af4.match("i testx")
        assert not af4.match("i-11test")
        assert not af4.match(InternalGroupAddress("i-11"))
