"""Unit test for Scene objects."""

import asyncio
import unittest
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.devices import Scene
from xknx.knx import DPTArray, GroupAddress, Telegram

MOCK_WARN = Mock()


class TestScene(unittest.TestCase):
    """Test class for Scene objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # SYNC
    #
    def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX(loop=self.loop)
        scene = Scene(
            xknx,
            'TestScene',
            group_address='1/2/1',
            scene_number=23)
        self.loop.run_until_complete(asyncio.Task(scene.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 0)

    #
    # TEST RUN SCENE
    #
    def test_run(self):
        """Test running scene."""
        xknx = XKNX(loop=self.loop)
        scene = Scene(
            xknx,
            'TestScene',
            group_address='1/2/1',
            scene_number=23)
        self.loop.run_until_complete(asyncio.Task(scene.run()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/1'), payload=DPTArray(0x17)))

    def test_do(self):
        """Test running scene with do command."""
        xknx = XKNX(loop=self.loop)
        scene = Scene(
            xknx,
            'TestScene',
            group_address='1/2/1',
            scene_number=23)
        self.loop.run_until_complete(asyncio.Task(scene.do("run")))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/1'), payload=DPTArray(0x17)))

    @patch('logging.Logger.warning', MOCK_WARN)
    def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX(loop=self.loop)
        scene = Scene(
            xknx,
            'TestScene',
            group_address='1/2/1',
            scene_number=23)
        self.loop.run_until_complete(asyncio.Task(scene.do("execute")))
        self.assertEqual(xknx.telegrams.qsize(), 0)
        MOCK_WARN.assert_called_with('Could not understand action %s for device %s', 'execute', 'TestScene')

    #
    # TEST has_group_address
    #
    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX(loop=self.loop)
        scene = Scene(
            xknx,
            'TestScene',
            group_address='1/2/1',
            scene_number=23)
        self.assertTrue(scene.has_group_address(GroupAddress('1/2/1')))
        self.assertFalse(scene.has_group_address(GroupAddress('2/2/2')))
