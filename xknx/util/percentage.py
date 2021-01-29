"""Percentage util functions. From homeassistant/util/percentage.py ."""
from typing import Tuple


def ranged_value_to_percentage(
    low_high_range: Tuple[float, float], value: float
) -> int:
    """Given a range of low and high values convert a single value to a percentage.

    When using this utility for fan speeds, do not include 0 if it is off
    Given a low value of 1 and a high value of 255 this function
    will return:
    (1,255), 255: 100
    (1,255), 127: 50
    (1,255), 10: 4
    """
    return int((value * 100) // (low_high_range[1] - low_high_range[0] + 1))


def percentage_to_ranged_value(
    low_high_range: Tuple[float, float], percentage: int
) -> float:
    """Given a range of low and high values convert a percentage to a single value.

    When using this utility for fan speeds, do not include 0 if it is off
    Given a low value of 1 and a high value of 255 this function
    will return:
    (1,255), 100: 255
    (1,255), 50: 127.5
    (1,255), 4: 10.2
    """
    return (low_high_range[1] - low_high_range[0] + 1) * percentage / 100
