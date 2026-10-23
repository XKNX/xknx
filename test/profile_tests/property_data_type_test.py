"""Unit test for Property Datatypes."""

import pytest

from xknx.profile import PropertyDataType


@pytest.mark.parametrize(
    ("pdt", "size"),
    [
        (PropertyDataType.PDT_CHAR, 1),
        (PropertyDataType.PDT_UNSIGNED_INT, 2),
        (PropertyDataType.PDT_DATE, 3),
        (PropertyDataType.PDT_UNSIGNED_LONG, 4),
        (PropertyDataType.PDT_DOUBLE, 8),
        (PropertyDataType.PDT_CHAR_BLOCK, 10),
        (PropertyDataType.PDT_POLL_GROUP_SETTINGS, 3),
        (PropertyDataType.PDT_SHORT_CHAR_BLOCK, 5),
        (PropertyDataType.PDT_DATE_TIME, 8),
        (PropertyDataType.PDT_GENERIC_01, 1),
        (PropertyDataType.PDT_GENERIC_02, 2),
        (PropertyDataType.PDT_GENERIC_04, 4),
        (PropertyDataType.PDT_GENERIC_20, 20),
        (PropertyDataType.PDT_VERSION, 2),
        (PropertyDataType.PDT_ALARM_INFO, 6),
        (PropertyDataType.PDT_BINARY_INFORMATION, 1),
        (PropertyDataType.PDT_BITSET16, 2),
        (PropertyDataType.PDT_SCALING, 1),
        (PropertyDataType.PDT_CONTROL, None),
        (PropertyDataType.PDT_VARIABLE_LENGTH, None),
        (PropertyDataType.PDT_REFERENCE, None),
        (PropertyDataType.PDT_UTF_8, None),
        (PropertyDataType.PDT_FUNCTION, None),
        (PropertyDataType.PDT_ESCAPE, None),
    ],
)
def test_size(pdt: PropertyDataType, size: int | None) -> None:
    """Test the element size of a Property Datatype."""
    assert pdt.size == size


@pytest.mark.parametrize("value", [*range(0x26, 0x2F), *range(0x37, 0x3C)])
def test_reserved(value: int) -> None:
    """Test reserved Property Datatypes are not defined."""
    with pytest.raises(ValueError):
        PropertyDataType(value)
