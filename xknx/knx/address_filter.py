"""
AddressFilter provides a mechanism for filtering KNX addresses with patterns.

Patterns can be

    for level3 KNX addresses:

        AddressFilter("1/*/2-5")
        AddressFilter("1/1-3,4,5/*")
        AddressFilter("1/2/-10)

    for level2 KNX addresses:

        AddressFilter("*/2-5")
        AddressFilter("1-3,4,5/*")
        AddressFilter("2/-10")

    for free format KNX addresses:

        AddressFilter("2-5")
        AddressFilter("1-3,4,5")
        AddressFilter("-10")
"""
from xknx.exceptions import ConversionError

from .address import GroupAddress


class AddressFilter:
    """Class for filtering Addresses according to patterns."""

    # pylint: disable=too-few-public-methods

    def __init__(self, pattern):
        """Initialize AddressFilter class."""
        self.level_filters = []
        self._parse_pattern(pattern)

    def _parse_pattern(self, pattern):
        for part in pattern.split("/"):
            self.level_filters.append(AddressFilter.LevelFilter(part))
        if len(self.level_filters) > 3:
            raise ConversionError("Too many parts within pattern.", pattern=pattern)

    def match(self, address):
        """Test if provided address matches Addressfilter."""
        if isinstance(address, str):
            address = GroupAddress(address)
        if len(self.level_filters) == 3:
            return self._match_level3(address)
        elif len(self.level_filters) == 2:
            return self._match_level2(address)
        return self._match_free(address)

    def _match_level3(self, address):
        return (
            self.level_filters[0].match(address.main)
            and
            self.level_filters[1].match(address.middle)
            and
            self.level_filters[2].match(address.sub)
        )

    def _match_level2(self, address):
        return (
            self.level_filters[0].match(address.main)
            and
            self.level_filters[1].match(address.sub)
        )

    def _match_free(self, address):
        return (
            self.level_filters[0].match(address.sub)
        )

    class Range:
        """Class for filtering patterns like "8", "*", "8-10"."""

        def __init__(self, pattern):
            """Initialize Range object."""
            self.range_from = None
            self.range_to = None
            self._parse_pattern(pattern)

        def _parse_pattern(self, pattern):
            if pattern == "*":
                self._init_wildcard()
            elif pattern.isdigit():
                self._init_digit(pattern)
            elif "-" in pattern:
                self._init_range(pattern)
            self.range_to = self._adjust_range(self.range_to)
            self.range_from = self._adjust_range(self.range_from)
            self._flip_range_if_necessary()

        def _init_wildcard(self):
            self.range_from = 0
            self.range_to = GroupAddress.MAX_FREE

        def _init_digit(self, pattern):
            digit = int(pattern)
            self.range_from = digit
            self.range_to = digit

        def _init_range(self, pattern):
            (range_from, range_to) = pattern.split("-")
            self.range_from = int(range_from) \
                if range_from else 0
            self.range_to = int(range_to) \
                if range_to else GroupAddress.MAX_FREE

        @staticmethod
        def _adjust_range(digit):
            if digit > GroupAddress.MAX_FREE:
                return GroupAddress.MAX_FREE
            if digit < 0:
                return 0
            return digit

        def _flip_range_if_necessary(self):
            if self.range_from > self.range_to:
                self.range_to, self.range_from =\
                    self.range_from, self.range_to

        def get_range(self):
            """Return the range (from,to) of this pattern."""
            return self.range_from, self.range_to

        def match(self, digit):
            """Return if given digit is within range of pattern."""
            return \
                digit >= self.range_from and \
                digit <= self.range_to

    class LevelFilter:
        """Class for filtering patterns like "8,11-14,20"."""

        # pylint: disable=too-few-public-methods
        def __init__(self, pattern):
            """Initialize LevelFilter."""
            self.ranges = []
            self._parse_pattern(pattern)

        def _parse_pattern(self, pattern):
            for part in pattern.split(","):
                self.ranges.append(AddressFilter.Range(part))

        def match(self, digit):
            """Return if given digit is within range of pattern."""
            for _range in self.ranges:
                if _range.match(digit):
                    return True
            return False
