"""Unit test for Scene objects."""

from unittest.mock import Mock

import pytest

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
        scene = Scene(xknx, name="TestScene", group_address="1/2/1", scene_number=23)
        await scene.sync()
        assert xknx.telegrams.qsize() == 0

    #
    # TEST RUN SCENE
    #
    async def test_run(self) -> None:
        """Test running scene."""
        xknx = XKNX()
        scene = Scene(xknx, name="TestScene", group_address="1/2/1", scene_number=23)
        await scene.run()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTArray(0x16)),
        )

    #
    # TEST LEARN SCENE
    #
    async def test_learn(self) -> None:
        """Test storing a scene."""
        xknx = XKNX()
        scene = Scene(xknx, name="TestScene", group_address="1/2/1", scene_number=23)
        await scene.learn()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/1"),
            payload=GroupValueWrite(DPTArray(0x96)),
        )

    #
    # TEST has_group_address
    #
    def test_has_group_address(self) -> None:
        """Test has_group_address."""
        xknx = XKNX()
        scene = Scene(xknx, name="TestScene", group_address="1/2/1", scene_number=23)
        assert scene.has_group_address(GroupAddress("1/2/1"))
        assert not scene.has_group_address(GroupAddress("2/2/2"))

    async def test_process_callback(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test process / reading telegrams from telegram queue. Test if callback is called."""

        xknx = XKNX()
        after_update_callback = Mock()
        scene = Scene(
            xknx,
            name="TestScene",
            group_address="1/2/3",
            scene_number=1,
            device_updated_cb=after_update_callback,
        )

        scene.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x00,))),
            )
        )
        after_update_callback.assert_called_with(scene)

        after_update_callback.reset_mock()
        scene.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x01,))),  # different scene number
            )
        )
        after_update_callback.assert_not_called()

        assert not scene.learn_requested

        after_update_callback.reset_mock()
        scene.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x80,))),  # same scene number, learn
            )
        )
        # a request to store the scene calls the callback too - `learn_requested`
        # tells it apart from an activation
        after_update_callback.assert_called_with(scene)
        assert scene.learn_requested
        assert not caplog.records

        after_update_callback.reset_mock()
        scene.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x81,))),  # different scene number
            )
        )
        # another scene neither calls the callback nor changes `learn_requested`
        after_update_callback.assert_not_called()
        assert scene.learn_requested

        after_update_callback.reset_mock()
        scene.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x00,))),  # same number, activate
            )
        )
        after_update_callback.assert_called_with(scene)
        assert not scene.learn_requested
