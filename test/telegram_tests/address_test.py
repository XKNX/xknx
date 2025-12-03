"""Unit test for Address class."""

from typing import Any

import pytest

from xknx.exceptions import CouldNotParseAddress
from xknx.telegram.address import (
    GroupAddress,
    GroupAddressType,
    IndividualAddress,
    InternalGroupAddress,
    parse_device_group_address,
)

_broadcast_group_addresses: list[str | int] = ["0/0/0", "0/0", "0", 0]

device_group_addresses_valid: dict[Any, int] = {
    "0/1": 1,
    "0/11": 11,
    "0/111": 111,
    "0/1111": 1111,
    "0/2047": 2047,
    "0/0/1": 1,
    "0/0/11": 11,
    "0/0/111": 111,
    "0/0/255": 255,
    "0/1/11": 267,
    "0/1/111": 367,
    "0/7/255": 2047,
    "1/0": 2048,
    "1/0/0": 2048,
    "1/1/111": 2415,
    "1/7/255": 4095,
    "31/7/255": 65535,
    "1": 1,
    65535: 65535,
    GroupAddress("1/1/111"): 2415,
}

group_addresses_valid = (
    dict.fromkeys(_broadcast_group_addresses, 0) | device_group_addresses_valid
)

group_addresses_invalid: list[Any] = [
    "0/2049",
    "0/8/0",
    "0/0/256",
    "32/0",
    "0/0a",
    "a0/0",
    "abc",
    "1.1.1",
    "0.0",
    IndividualAddress("11.11.111"),
    65536,
    (0xAB, 0xCD),
    -1,
    [],
    None,
]

device_group_addresses_invalid: list[Any] = [
    *group_addresses_invalid,
    *_broadcast_group_addresses,
]

individual_addresses_valid: dict[Any, int] = {
    "0.0.0": 0,
    "123": 123,
    "1.0.0": 4096,
    "1.1.0": 4352,
    "1.1.1": 4353,
    "1.1.11": 4363,
    "1.1.111": 4463,
    "1.11.111": 7023,
    "11.11.111": 47983,
    IndividualAddress("11.11.111"): 47983,
    "15.15.255": 65535,
    0: 0,
    65535: 65535,
}

individual_addresses_invalid: list[Any] = [
    "15.15.256",
    "16.0.0",
    "0.16.0",
    "15.15.255a",
    "a15.15.255",
    "abc",
    "1/1/1",
    "0/0",
    GroupAddress("1/1/111"),
    65536,
    (0xAB, 0xCD),
    -1,
    [],
    None,
]

internal_group_addresses_valid: dict[str | InternalGroupAddress, str] = {
    "i 123": "i-123",
    "i-123": "i-123",
    "i_123": "i-123",
    "I 123": "i-123",
    "i abc": "i-abc",
    "i-abc": "i-abc",
    "i_abc": "i-abc",
    "I-abc": "i-abc",
    "i123": "i-123",
    "iabc": "i-abc",
    "IABC": "i-ABC",
    "i   abc  ": "i-abc",
    "i asdf 123 adsf ": "i-asdf 123 adsf",
    "i-1/2/3": "i-1/2/3",
    InternalGroupAddress("i-123"): "i-123",
}

internal_group_addresses_invalid: list[str | None] = [
    "i",
    "i-",
    "i ",
    "i  ",
    "i- ",
    "a",
    None,
]


class TestIndividualAddress:
    """Test class for IndividualAddress."""

    @pytest.mark.parametrize(
        ("address_test", "address_raw"), individual_addresses_valid.items()
    )
    def test_with_valid(self, address_test: Any, address_raw: int) -> None:
        """Test with some valid addresses."""

        assert IndividualAddress(address_test).raw == address_raw

    @pytest.mark.parametrize("address_test", individual_addresses_invalid)
    def test_with_invalid(self, address_test: Any) -> None:
        """Test with some invalid addresses."""

        with pytest.raises(CouldNotParseAddress):
            IndividualAddress(address_test)

    def test_with_int(self) -> None:
        """Test initialization with free format address as integer."""
        assert IndividualAddress(49552).raw == 49552

    def test_from_knx(self) -> None:
        """Test initialization with Bytes."""
        ia = IndividualAddress.from_knx(bytes((0x12, 0x34)))
        assert ia.raw == 0x1234

    def test_is_line(self) -> None:
        """Test if `IndividualAddress.is_line` works like excepted."""
        assert IndividualAddress("1.0.0").is_line
        assert not IndividualAddress("1.0.1").is_line

    def test_is_device(self) -> None:
        """Test if `IndividualAddress.is_device` works like excepted."""
        assert IndividualAddress("1.0.1").is_device
        assert not IndividualAddress("1.0.0").is_device

    def test_to_knx(self) -> None:
        """Test if `IndividualAddress.to_knx()` generates valid byte objects."""
        assert IndividualAddress("0.0.0").to_knx() == bytes((0x0, 0x0))
        assert IndividualAddress("15.15.255").to_knx() == bytes((0xFF, 0xFF))

    def test_equal(self) -> None:
        """Test if the equal operator works in all cases."""
        assert IndividualAddress("1.0.0") == IndividualAddress(4096)
        assert IndividualAddress("1.0.0") != IndividualAddress("1.1.1")
        assert IndividualAddress("1.0.0") is not None
        assert IndividualAddress("1.0.0") != "example"
        assert IndividualAddress("1.1.1") != GroupAddress("1/1/1")
        assert IndividualAddress(250) != GroupAddress(250)
        assert IndividualAddress(250) != 250

    def test_comparison(self) -> None:
        """Test if the less than operator works in all cases."""
        assert IndividualAddress("1.0.0") < IndividualAddress("1.0.1")
        assert IndividualAddress("1.1.1") < IndividualAddress("1.10.0")
        assert IndividualAddress("1.1.0") < IndividualAddress("2.0.0")
        with pytest.raises(
            TypeError,
            match=r"'<'' not supported between instances of 'IndividualAddress' and 'GroupAddress'",
        ):
            _ = IndividualAddress("1.0.0") < GroupAddress("1/0")

    def test_representation(self) -> None:
        """Test string representation of address."""
        assert repr(IndividualAddress("2.3.4")) == 'IndividualAddress("2.3.4")'


class TestGroupAddress:
    """Test class for GroupAddress."""

    @pytest.mark.parametrize(
        ("address_test", "address_raw"), group_addresses_valid.items()
    )
    def test_with_valid(self, address_test: str | int, address_raw: int) -> None:
        """
        Test if the class constructor generates valid raw values.

        This test checks:
        * all allowed input variants (strings, tuples, integers)
        * for conversation errors
        * for upper/lower limits still working, to avoid off-by-one errors
        """

        assert GroupAddress(address_test).raw == address_raw

    @pytest.mark.parametrize("address_test", group_addresses_invalid)
    def test_with_invalid(self, address_test: Any) -> None:
        """
        Test if constructor raises an exception for all known invalid cases.

        Checks:
        * addresses or parts of it too high/low
        * invalid input variants (lists instead of tuples)
        * invalid strings
        """

        with pytest.raises(CouldNotParseAddress):
            GroupAddress(address_test)

    def test_main(self) -> None:
        """
        Test if `GroupAddress.main` works.

        Checks:
        * Main group part of a strings returns the right value
        * Return `None` on `GroupAddressType.FREE`
        """
        assert GroupAddress("1/0").main == 1
        assert GroupAddress("15/0").main == 15
        assert GroupAddress("31/0/0").main == 31
        GroupAddress.address_format = GroupAddressType.FREE
        assert GroupAddress("1/0").main is None

    def test_middle(self) -> None:
        """
        Test if `GroupAddress.middle` works.

        Checks:
        * Middle group part of a strings returns the right value
        * Return `None` if not `GroupAddressType.LONG`
        """
        GroupAddress.address_format = GroupAddressType.LONG
        assert GroupAddress("1/0/1").middle == 0
        assert GroupAddress("1/7/1").middle == 7
        GroupAddress.address_format = GroupAddressType.SHORT
        assert GroupAddress("1/0").middle is None
        GroupAddress.address_format = GroupAddressType.FREE
        assert GroupAddress("1/0").middle is None

    def test_sub(self) -> None:
        """
        Test if `GroupAddress.sub` works.

        Checks:
        * Sub group part of a strings returns the right value
        * Return never `None`
        """
        GroupAddress.address_format = GroupAddressType.SHORT
        assert GroupAddress("1/0").sub == 0
        assert GroupAddress("31/0").sub == 0
        assert GroupAddress("1/2047").sub == 2047
        assert GroupAddress("31/2047").sub == 2047

        GroupAddress.address_format = GroupAddressType.LONG
        assert GroupAddress("1/0/0").sub == 0
        assert GroupAddress("1/0/255").sub == 255

        GroupAddress.address_format = GroupAddressType.FREE
        assert GroupAddress("0/0").sub == 0
        assert GroupAddress("1/0").sub == 2048
        assert GroupAddress("31/2047").sub == 65535

    def test_from_knx(self) -> None:
        """Test initialization with Bytes."""
        ga = GroupAddress.from_knx(bytes((0x12, 0x34)))
        assert ga.raw == 0x1234

    def test_to_knx(self) -> None:
        """Test if `GroupAddress.to_knx()` generates valid byte tuples."""
        assert GroupAddress("0/0").to_knx() == bytes((0x0, 0x0))
        assert GroupAddress("31/2047").to_knx() == bytes((0xFF, 0xFF))

    def test_equal(self) -> None:
        """Test if the equal operator works in all cases."""
        assert GroupAddress("1/0") == GroupAddress(2048)
        assert GroupAddress("1/1") != GroupAddress("1/1/0")
        assert GroupAddress("1/0") is not None
        assert GroupAddress("1/0") != "example"
        assert GroupAddress(1) != IndividualAddress(1)
        assert GroupAddress(1) != 1

    def test_comparison(self) -> None:
        """Test if the less than operator works in all cases."""
        assert GroupAddress("1/0/4") < GroupAddress("1/1/0")
        assert GroupAddress("1/1/1") < GroupAddress("10/0/0")
        assert GroupAddress("1/2047") < GroupAddress("2/0")
        with pytest.raises(
            TypeError,
            match=r"'<'' not supported between instances of 'GroupAddress' and 'IndividualAddress'",
        ):
            _ = GroupAddress("1/0") < IndividualAddress("1.0.0")
        with pytest.raises(
            TypeError,
            match=r"'<'' not supported between instances of 'GroupAddress' and 'int'",
        ):
            _ = GroupAddress("1/0") < 100
        with pytest.raises(
            TypeError,
            match=r"'<'' not supported between instances of 'GroupAddress' and 'InternalGroupAddress'",
        ):
            _ = GroupAddress("1/0") < InternalGroupAddress("i-0")

        assert sorted(
            [GroupAddress("1/0/1"), GroupAddress("1/0/0"), GroupAddress("0/20")]
        ) == [GroupAddress("0/20"), GroupAddress("1/0/0"), GroupAddress("1/0/1")]

    @pytest.mark.parametrize(
        ("initializer", "string_free", "string_short", "string_long"),
        [
            ("0", "0", "0/0", "0/0/0"),
            ("1/4/70", "3142", "1/1094", "1/4/70"),
        ],
    )
    def test_representation(
        self, initializer: str, string_free: str, string_short: str, string_long: str
    ) -> None:
        """Test string representation of address."""
        group_address = GroupAddress(initializer)
        GroupAddress.address_format = GroupAddressType.FREE
        assert str(group_address) == string_free
        assert repr(group_address) == f'GroupAddress("{string_free}")'
        GroupAddress.address_format = GroupAddressType.SHORT
        assert str(group_address) == string_short
        assert repr(group_address) == f'GroupAddress("{string_short}")'
        GroupAddress.address_format = GroupAddressType.LONG
        assert str(group_address) == string_long
        assert repr(group_address) == f'GroupAddress("{string_long}")'


class TestInternalGroupAddress:
    """Test class for InternalGroupAddress."""

    @pytest.mark.parametrize(
        ("address_test", "address_raw"), internal_group_addresses_valid.items()
    )
    def test_with_valid(
        self, address_test: str | InternalGroupAddress, address_raw: str
    ) -> None:
        """Test if the class constructor generates valid raw values."""

        assert InternalGroupAddress(address_test).raw == address_raw

    @pytest.mark.parametrize(
        "address_test",
        [
            *internal_group_addresses_invalid,
            *group_addresses_valid,
            *group_addresses_invalid,
            *individual_addresses_valid,
            *individual_addresses_invalid,
        ],
    )
    def test_with_invalid(self, address_test: Any) -> None:
        """Test if constructor raises an exception for all known invalid cases."""

        with pytest.raises(CouldNotParseAddress):
            InternalGroupAddress(address_test)

    def test_equal(self) -> None:
        """Test if the equal operator works in all cases."""
        assert InternalGroupAddress("i 123") == InternalGroupAddress("i 123")
        assert InternalGroupAddress("i-asdf") == InternalGroupAddress("i asdf")
        assert InternalGroupAddress("i-asdf") == InternalGroupAddress("Iasdf")
        assert InternalGroupAddress("i-1") != InternalGroupAddress("i-2")
        assert InternalGroupAddress("i-1") is not None
        assert InternalGroupAddress("i-example") != "example"
        assert InternalGroupAddress("i-0") != GroupAddress(0)
        assert InternalGroupAddress("i-1") != IndividualAddress(1)
        assert InternalGroupAddress("i-1") != 1

    def test_comparison(self) -> None:
        """Test if the less than operator works in all cases."""
        assert InternalGroupAddress("i-1") < InternalGroupAddress("i-2")
        assert InternalGroupAddress("i-abc") < InternalGroupAddress("i-def")
        assert InternalGroupAddress("i-1") < InternalGroupAddress("i-a")
        with pytest.raises(
            TypeError,
            match=r"'<'' not supported between instances of 'InternalGroupAddress' and 'GroupAddress'",
        ):
            _ = InternalGroupAddress("i-1") < GroupAddress("1/0")
        with pytest.raises(
            TypeError,
            match=r"'<'' not supported between instances of 'InternalGroupAddress' and 'IndividualAddress'",
        ):
            _ = InternalGroupAddress("i-1") < IndividualAddress("1.0.0")
        with pytest.raises(
            TypeError,
            match=r"'<'' not supported between instances of 'InternalGroupAddress' and 'str'",
        ):
            _ = InternalGroupAddress("i-1") < "i-2"

    def test_representation(self) -> None:
        """Test string representation of address."""
        assert repr(InternalGroupAddress("i0")) == 'InternalGroupAddress("i-0")'
        assert repr(InternalGroupAddress("i-0")) == 'InternalGroupAddress("i-0")'
        assert repr(InternalGroupAddress("i 0")) == 'InternalGroupAddress("i-0")'


class TestParseDestinationAddress:
    """Test class for parsing destination addresses."""

    @pytest.mark.parametrize("address_test", device_group_addresses_valid)
    def test_parse_device_group_address(self, address_test: Any) -> None:
        """Test if the function returns GroupAddress objects."""
        assert isinstance(parse_device_group_address(address_test), GroupAddress)

    @pytest.mark.parametrize("address_test", internal_group_addresses_valid)
    def test_parse_device_internal_group_address(
        self, address_test: str | InternalGroupAddress
    ) -> None:
        """Test if the function returns InternalGroupAddress objects."""
        assert isinstance(
            parse_device_group_address(address_test), InternalGroupAddress
        )

    @pytest.mark.parametrize(
        "address_test",
        [
            *internal_group_addresses_invalid,
            *device_group_addresses_invalid,
        ],
    )
    def test_parse_device_invalid(self, address_test: Any) -> None:
        """Test if the function raises CouldNotParseAddress on invalid values."""
        with pytest.raises(CouldNotParseAddress):
            parse_device_group_address(address_test)

    def test_parse_device_invalid_group_address_message(self) -> None:
        """Test if the error message is from GroupAddress, not InternalGroupAddress for strings."""
        with pytest.raises(CouldNotParseAddress, match=r".*Sub group out of range.*"):
            parse_device_group_address("0/0/700")
