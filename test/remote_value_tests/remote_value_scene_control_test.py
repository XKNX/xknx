"""Unit test for RemoteValueSceneControl objects."""

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, SceneControl
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueSceneControl
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueSceneControl:
    """Test class for RemoteValueSceneControl objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (SceneControl(11), 0x0A),
            (SceneControl(11, learn=True), 0x8A),
            (SceneControl(1), 0x00),
            (SceneControl(64, learn=True), 0xBF),
        ],
    )
    def test_to_knx(self, value: SceneControl, raw: int) -> None:
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSceneControl(xknx)
        assert remote_value.to_knx(value) == DPTArray((raw,))

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            (0x0A, SceneControl(11)),
            (0x8A, SceneControl(11, learn=True)),
            (0x00, SceneControl(1)),
            (0xBF, SceneControl(64, learn=True)),
        ],
    )
    def test_from_knx(self, raw: int, value: SceneControl) -> None:
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSceneControl(xknx)
        assert remote_value.from_knx(DPTArray((raw,))) == value

    def test_to_knx_error(self) -> None:
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueSceneControl(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(SceneControl(100))
        with pytest.raises(ConversionError):
            remote_value.to_knx({"scene_number": 11, "learn": "yes"})

    def test_set(self) -> None:
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueSceneControl(
            xknx, group_address=GroupAddress("1/2/3")
        )
        remote_value.set(SceneControl(11))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0A,))),
        )
        remote_value.set(SceneControl(11, learn=True))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x8A,))),
        )

    def test_process(self) -> None:
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSceneControl(
            xknx, group_address=GroupAddress("1/2/3")
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x8A,))),
        )
        remote_value.process(telegram)
        assert remote_value.value == SceneControl(11, learn=True)

    def test_to_process_error(self) -> None:
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSceneControl(
            xknx, group_address=GroupAddress("1/2/3")
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65))),
        )
        assert remote_value.process(telegram) is False

        assert remote_value.value is None
