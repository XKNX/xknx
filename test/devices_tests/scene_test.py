"""Unit test for Scene objects."""

from unittest.mock import patch
import pytest

from xknx import XKNX
from xknx.devices import Scene
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram

from xknx._test import Testcase

class TestScene(Testcase):
    """Test class for Scene objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    #
    # SYNC
    #
    @pytest.mark.anyio
    async def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        scene = Scene(
            xknx,
            'TestScene',
            group_address='1/2/1',
            scene_number=23)
        await scene.sync(False)
        self.assertEqual(xknx.telegrams_out.qsize(), 0)

    #
    # TEST RUN SCENE
    #
    @pytest.mark.anyio
    async def test_run(self):
        """Test running scene."""
        xknx = XKNX()
        scene = Scene(
            xknx,
            'TestScene',
            group_address='1/2/1',
            scene_number=23)
        await scene.run()
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/1'), payload=DPTArray(0x16)))

    @pytest.mark.anyio
    async def test_do(self):
        """Test running scene with do command."""
        xknx = XKNX()
        scene = Scene(
            xknx,
            'TestScene',
            group_address='1/2/1',
            scene_number=23)
        await scene.do("run")
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/1'), payload=DPTArray(0x16)))

    @pytest.mark.anyio
    async def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        scene = Scene(
            xknx,
            'TestScene',
            group_address='1/2/1',
            scene_number=23)
        with patch('logging.Logger.warning') as mockWarn:
            await scene.do("execute")
            mockWarn.assert_called_with('Could not understand action %s for device %s', 'execute', 'TestScene')
        assert xknx.telegrams_out.qsize() == 0

    #
    # TEST has_group_address
    #
    @pytest.mark.anyio
    async def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        scene = Scene(
            xknx,
            'TestScene',
            group_address='1/2/1',
            scene_number=23)
        self.assertTrue(scene.has_group_address(GroupAddress('1/2/1')))
        self.assertFalse(scene.has_group_address(GroupAddress('2/2/2')))
