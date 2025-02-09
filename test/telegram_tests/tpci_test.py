"""Unit test for TPCI objects."""

import pytest

from xknx.exceptions import ConversionError
from xknx.telegram.tpci import (
    TPCI,
    TAck,
    TConnect,
    TDataBroadcast,
    TDataConnected,
    TDataGroup,
    TDataIndividual,
    TDataTagGroup,
    TDisconnect,
    TNak,
)


@pytest.mark.parametrize(
    ("tpci_int", "dst_is_group_address", "dst_is_zero", "tpci_expected"),
    [
        (0b00000000, True, False, TDataGroup()),
        (0b00000000, True, True, TDataBroadcast()),
        (0b00000100, True, False, TDataTagGroup()),
        (0b00000000, False, False, TDataIndividual()),
        (0b00000000, False, True, TDataIndividual()),
        (0b01011100, False, False, TDataConnected(sequence_number=0b0111)),
        (0b10000000, False, False, TConnect()),
        (0b10000000, False, True, TConnect()),
        (0b10000001, False, False, TDisconnect()),
        (0b11101010, False, False, TAck(sequence_number=10)),
        (0b11010011, False, False, TNak(sequence_number=4)),
    ],
)
def test_tpci_resolve_encode(
    tpci_int: int, dst_is_group_address: bool, dst_is_zero: bool, tpci_expected: TPCI
) -> None:
    """Test resolving and encoding TPCI classes."""
    assert (
        TPCI.resolve(
            raw_tpci=tpci_int,
            dst_is_group_address=dst_is_group_address,
            dst_is_zero=dst_is_zero,
        )
        == tpci_expected
    )
    assert tpci_expected.to_knx() == tpci_int


@pytest.mark.parametrize("dst_is_zero", [True, False])
@pytest.mark.parametrize(
    ("tpci_int", "dst_is_group_address"),
    [
        # sequence_number for non-numbered
        (0b00100000, True),
        (0b00001000, False),
        (0b10000100, True),
        (0b10000100, False),
        # numbered for group addressed
        (0b01000000, True),
    ],
)
def test_invalid_tpci(
    tpci_int: int, dst_is_group_address: bool, dst_is_zero: bool
) -> None:
    """Test resolving TPCI classes."""
    with pytest.raises(ConversionError):
        TPCI.resolve(
            raw_tpci=tpci_int,
            dst_is_group_address=dst_is_group_address,
            dst_is_zero=dst_is_zero,
        )


def test_equality() -> None:
    """Test equality."""
    assert TDataGroup() == TDataGroup()
    assert TDataGroup() != TDataIndividual()
