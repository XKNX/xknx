"""Unit test for RemoteValueDateTime objects."""

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray
from xknx.dpt.dpt_19 import KNXDateTime, KNXDayOfWeek
from xknx.exceptions import CouldNotParseTelegram
from xknx.remote_value import RemoteValueDateTime


class TestRemoteValueDateTime:
    """Test class for RemoteValueDateTime objects."""

    def test_from_knx(self) -> None:
        """Test parsing of RV with datetime object."""
        xknx = XKNX()
        rv_datetime = RemoteValueDateTime(xknx)
        assert rv_datetime.from_knx(
            DPTArray((0x75, 0x0B, 0x1C, 0x17, 0x07, 0x18, 0x20, 0x80))
        ) == KNXDateTime(
            2017,
            11,
            28,
            23,
            7,
            24,
            day_of_week=KNXDayOfWeek.ANY_DAY,
            external_sync=True,
        )

    def test_to_knx(self) -> None:
        """Testing date time object."""
        xknx = XKNX()
        rv_datetime = RemoteValueDateTime(xknx)
        array = rv_datetime.to_knx(
            KNXDateTime(
                2017,
                11,
                28,
                23,
                7,
                24,
                day_of_week=KNXDayOfWeek.ANY_DAY,
                external_sync=True,
            )
        )
        assert array.value == (0x75, 0x0B, 0x1C, 0x17, 0x07, 0x18, 0x20, 0x80)

    def test_payload_invalid(self) -> None:
        """Testing KNX/Byte representation of DPTDateTime object."""
        xknx = XKNX()
        rv_datetime = RemoteValueDateTime(xknx)
        with pytest.raises(CouldNotParseTelegram):
            rv_datetime.from_knx(DPTArray((0x0B, 0x1C, 0x57, 0x07, 0x18, 0x20, 0x80)))
