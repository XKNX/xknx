"""Unit test for RemoteValueByLength objects."""

import pytest

from xknx import XKNX
from xknx.dpt import (
    DPTArray,
    DPTBase,
    DPTBinary,
    DPTColorXYY,
    DPTOpenClose,
    DPTPressure,
    DPTPressure2Byte,
    DPTTemperature,
    DPTValue1Count,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value.remote_value_by_length import RemoteValueByLength


class TestRemoteValueByLength:
    """Test class for RemoteValueByLength objects."""

    @pytest.mark.parametrize(
        "dpt_classes",
        [
            (DPTOpenClose, DPTPressure),  # DPTBinary payload invalid
            (DPTTemperature, DPTPressure2Byte),  # similar payload_length
            (DPTColorXYY, DPTValue1Count),  # non-numeric DPT
        ],
    )
    def test_invalid_dpt_classes(self, dpt_classes: tuple[type[DPTBase]]) -> None:
        """Test if invalid DPT classes raise ConversionError."""
        xknx = XKNX()
        with pytest.raises(ConversionError):
            RemoteValueByLength(xknx, dpt_classes=dpt_classes)  # type: ignore[arg-type]

    @pytest.mark.parametrize("payload", [DPTBinary(0), DPTArray((0, 1, 2))])
    def test_invalid_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test if invalid payloads raise CouldNotParseTelegram."""
        xknx = XKNX()
        remote_value = RemoteValueByLength(
            xknx=xknx,
            dpt_classes=(DPTPressure, DPTPressure2Byte),
        )
        with pytest.raises(CouldNotParseTelegram):
            remote_value.from_knx(payload)

    @pytest.mark.parametrize(
        ("first_dpt", "invalid_dpt"),
        [
            (DPTPressure, DPTPressure2Byte),
            (DPTPressure2Byte, DPTPressure),
        ],
    )
    def test_payload_valid_mode_assignment(
        self, first_dpt: type[DPTBase], invalid_dpt: type[DPTBase]
    ) -> None:
        """Test if DPT is assigned properly by payload length."""
        test_value = 1
        xknx = XKNX()
        remote_value = RemoteValueByLength(
            xknx=xknx,
            dpt_classes=(DPTPressure, DPTPressure2Byte),
        )
        first_payload = first_dpt.to_knx(test_value)
        invalid_payload = invalid_dpt.to_knx(test_value)

        assert remote_value._internal_dpt_class is None
        assert remote_value.from_knx(first_payload) == test_value
        assert remote_value._internal_dpt_class == first_dpt
        with pytest.raises(CouldNotParseTelegram):
            # other DPT is invalid now
            remote_value.from_knx(invalid_payload)
        # to_knx works when initialized
        assert remote_value.to_knx(test_value) == first_payload

    def test_to_knx_uninitialized(self) -> None:
        """Test to_knx raising ConversionError when DPT is not known."""
        xknx = XKNX()
        remote_value = RemoteValueByLength(
            xknx=xknx,
            dpt_classes=(DPTPressure, DPTPressure2Byte),
        )

        assert remote_value._internal_dpt_class is None
        with pytest.raises(ConversionError):
            remote_value.to_knx(1)
