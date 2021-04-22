"""
AddressFilter provides a mechanism for filtering KNX addresses with patterns.

Patterns can be

    for level3 KNX group addresses:

        AddressFilter("1/*/2-5")
        AddressFilter("1/1-3,4,5/*")
        AddressFilter("1/2/-10)

    for level2 KNX group addresses:

        AddressFilter("*/2-5")
        AddressFilter("1-3,4,5/*")
        AddressFilter("2/-10")

    for free format KNX group addresses:

        AddressFilter("2-5")
        AddressFilter("1-3,4,5")
        AddressFilter("-10")

    for xknx internal group addresses:

        AddressFilter("i-test")
        AddressFilter("i-t?st")
        AddressFilter("i-t*t")
"""
from __future__ import annotations

from fnmatch import fnmatch

from xknx.exceptions import ConversionError

from .address import GroupAddress, InternalGroupAddress, parse_device_group_address


class AddressFilter:
    """Class for filtering Addresses according to patterns."""

    def __init__(self, pattern: str) -> None:
        """Initialize AddressFilter class."""
        self.level_filters: list[AddressFilter.LevelFilter] = []
        self.internal_group_address_pattern: str | None = None
        self._parse_pattern(pattern)

    def _parse_pattern(self, pattern: str) -> None:
        if pattern.startswith("i"):
            self.internal_group_address_pattern = InternalGroupAddress(pattern).address
            return

        for part in pattern.split("/"):
            self.level_filters.append(AddressFilter.LevelFilter(part))
        if len(self.level_filters) > 3:
            raise ConversionError("Too many parts within pattern.", pattern=pattern)

    def match(self, address: str | GroupAddress | InternalGroupAddress) -> bool:
        """Test if provided address matches Addressfilter."""
        if isinstance(address, str):
            address = parse_device_group_address(address)

        if isinstance(address, GroupAddress) and self.level_filters:
            if len(self.level_filters) == 3:
                return self._match_level3(address)
            if len(self.level_filters) == 2:
                return self._match_level2(address)
            return self._match_free(address)

        if (
            isinstance(address, InternalGroupAddress)
            and self.internal_group_address_pattern
        ):
            return fnmatch(address.address, self.internal_group_address_pattern)

        return False

    def _match_level3(self, address: GroupAddress) -> bool:
        if address.main is None or address.middle is None:
            raise ConnectionError(
                f"Match level 3 incompatible with address level {address.levels}"
            )
        return bool(
            self.level_filters[0].match(address.main)
            and self.level_filters[1].match(address.middle)
            and self.level_filters[2].match(address.sub)
        )

    def _match_level2(self, address: GroupAddress) -> bool:
        if address.main is None:
            raise ConnectionError(
                f"Match level 2 incompatible with address level {address.levels}"
            )
        return bool(
            self.level_filters[0].match(address.main)
            and self.level_filters[1].match(address.sub)
        )

    def _match_free(self, address: GroupAddress) -> bool:
        return bool(self.level_filters[0].match(address.sub))

    class Range:
        """Class for filtering patterns like "8", "*", "8-10"."""

        def __init__(self, pattern: str) -> None:
            """Initialize Range object."""
            self.range_from: int = 0
            self.range_to: int = 0
            self._parse_pattern(pattern)

        def _parse_pattern(self, pattern: str) -> None:
            if pattern == "*":
                self._init_wildcard()
            elif pattern.isdigit():
                self._init_digit(pattern)
            elif "-" in pattern:
                self._init_range(pattern)
            self.range_to = self._adjust_range(self.range_to)
            self.range_from = self._adjust_range(self.range_from)
            self._flip_range_if_necessary()

        def _init_wildcard(self) -> None:
            self.range_from = 0
            self.range_to = GroupAddress.MAX_FREE

        def _init_digit(self, pattern: str) -> None:
            digit = int(pattern)
            self.range_from = digit
            self.range_to = digit

        def _init_range(self, pattern: str) -> None:
            (range_from, range_to) = pattern.split("-")
            self.range_from = int(range_from) if range_from else 0
            self.range_to = int(range_to) if range_to else GroupAddress.MAX_FREE

        @staticmethod
        def _adjust_range(digit: int) -> int:
            if digit > GroupAddress.MAX_FREE:
                return GroupAddress.MAX_FREE
            if digit < 0:
                return 0
            return digit

        def _flip_range_if_necessary(self) -> None:
            if self.range_from > self.range_to:
                self.range_to, self.range_from = self.range_from, self.range_to

        def get_range(self) -> tuple[int, int]:
            """Return the range (from,to) of this pattern."""
            return self.range_from, self.range_to

        def match(self, digit: int) -> bool:
            """Return if given digit is within range of pattern."""
            return bool(self.range_from <= digit <= self.range_to)

    class LevelFilter:
        """Class for filtering patterns like "8,11-14,20"."""

        def __init__(self, pattern: str) -> None:
            """Initialize LevelFilter."""
            self.ranges: list[AddressFilter.Range] = []
            self._parse_pattern(pattern)

        def _parse_pattern(self, pattern: str) -> None:
            for part in pattern.split(","):
                self.ranges.append(AddressFilter.Range(part))

        def match(self, digit: int) -> bool:
            """Return if given digit is within range of pattern."""
            for _range in self.ranges:
                if _range.match(digit):
                    return True
            return False
