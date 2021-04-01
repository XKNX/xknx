"""Unit test for Scene objects."""
from unittest.mock import patch

import pytest
from xknx import XKNX
from xknx.devices import Scene
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


# pylint: disable=no-self-use
@pytest.mark.asyncio
class TestScene:
    """Test class for Scene objects."""

    #
    # SYNC
    #
    async def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        scene = Scene(xknx, "TestScene", group_address="1/2/1", scene_number=23)
        await scene.sync()
        assert xknx.telegrams.qsize() == 0

    #
    # TEST RUN SCENE
    #
    async def test_run(self):
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

    async def test_do(self):
        """Test running scene with do command."""
        xknx = XKNX()
        scene = Scene(xknx, "TestScene", group_address="1/2/1", scene_number=23)
        await scene.do("run")
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTArray(0x16)),
        )

    async def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        scene = Scene(xknx, "TestScene", group_address="1/2/1", scene_number=23)
        with patch("logging.Logger.warning") as mockWarn:
            await scene.do("execute")
            mockWarn.assert_called_with(
                "Could not understand action %s for device %s", "execute", "TestScene"
            )
        assert xknx.telegrams.qsize() == 0

    #
    # TEST has_group_address
    #
    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        scene = Scene(xknx, "TestScene", group_address="1/2/1", scene_number=23)
        assert scene.has_group_address(GroupAddress("1/2/1"))
        assert not scene.has_group_address(GroupAddress("2/2/2"))

    def test_unique_id(self):
        """Test unique id functionality."""
        xknx = XKNX()
        scene = Scene(xknx, "TestScene", group_address="1/2/1", scene_number=23)
        assert scene.unique_id == "1/2/1_23"
