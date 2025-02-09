"""Unit test for Scene objects."""

from xknx import XKNX
from xknx.devices import Scene
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestScene:
    """Test class for Scene objects."""

    #
    # SYNC
    #
    async def test_sync(self) -> None:
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        scene = Scene(xknx, "TestScene", group_address="1/2/1", scene_number=23)
        await scene.sync()
        assert xknx.telegrams.qsize() == 0

    #
    # TEST RUN SCENE
    #
    async def test_run(self) -> None:
        """Test running scene."""
        xknx = XKNX()
        scene = Scene(xknx, "TestScene", group_address="1/2/1", scene_number=23)
        await scene.run()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTArray(0x16)),
        )

    #
    # TEST has_group_address
    #
    def test_has_group_address(self) -> None:
        """Test has_group_address."""
        xknx = XKNX()
        scene = Scene(xknx, "TestScene", group_address="1/2/1", scene_number=23)
        assert scene.has_group_address(GroupAddress("1/2/1"))
        assert not scene.has_group_address(GroupAddress("2/2/2"))
