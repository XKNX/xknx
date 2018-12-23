"""Unit test for Action objects."""
import asyncio
import unittest
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.devices import (Action, ActionBase, ActionCallback,
                          BinarySensorState, Light)


class TestAction(unittest.TestCase):
    """Class for testing Action objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # TEST COUNTER
    #
    def test_counter(self):
        """Test counter method."""
        xknx = XKNX(loop=self.loop)
        action = ActionBase(xknx, counter=2)
        self.assertTrue(action.test_counter(None))
        self.assertFalse(action.test_counter(1))
        self.assertTrue(action.test_counter(2))
        self.assertFalse(action.test_counter(3))

    def test_no_counter(self):
        """Test counter method with no counter set."""
        xknx = XKNX(loop=self.loop)
        action = ActionBase(xknx, counter=None)
        self.assertTrue(action.test_counter(None))
        self.assertTrue(action.test_counter(1))
        self.assertTrue(action.test_counter(2))
        self.assertTrue(action.test_counter(3))

    #
    # TEST APPLICABLE
    #
    def test_if_applicable_hook_on(self):
        """Test test_if_applicable method with hook set to 'on'."""
        xknx = XKNX(loop=self.loop)
        action = ActionBase(xknx, counter=2, hook="on")
        self.assertTrue(action.test_if_applicable(
            BinarySensorState.ON, 2))
        self.assertFalse(action.test_if_applicable(
            BinarySensorState.ON, 3))
        self.assertFalse(action.test_if_applicable(
            BinarySensorState.OFF, 2))

    def test_if_applicable_hook_off(self):
        """Test test_if_applicable method with hook set to 'off'."""
        xknx = XKNX(loop=self.loop)
        action = ActionBase(xknx, counter=2, hook="off")
        self.assertTrue(action.test_if_applicable(
            BinarySensorState.OFF, 2))
        self.assertFalse(action.test_if_applicable(
            BinarySensorState.OFF, 3))
        self.assertFalse(action.test_if_applicable(
            BinarySensorState.ON, 2))

    #
    # TEST EXECUTE
    #
    def test_execute_base_action(self):
        """Test if execute method of BaseAction shows correct info message."""
        xknx = XKNX(loop=self.loop)
        action = ActionBase(xknx)
        with patch('logging.Logger.info') as mock_info:
            self.loop.run_until_complete(asyncio.Task(action.execute()))
            mock_info.assert_called_with('Execute not implemented for %s', 'ActionBase')

    def test_execute_action(self):
        """Test if execute method of Action calls correct do method of device."""
        xknx = XKNX(loop=self.loop)
        light = Light(
            xknx,
            'Light1',
            group_address_switch='1/6/4')
        xknx.devices.add(light)
        action = Action(xknx, target='Light1', method='on')
        with patch('xknx.devices.Light.do') as mock_do:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_do.return_value = fut
            self.loop.run_until_complete(asyncio.Task(action.execute()))
            mock_do.assert_called_with('on')

    def test_execute_action_callback(self):
        """Test if execute method of ActionCallback calls correct callback method."""
        xknx = XKNX(loop=self.loop)
        callback = Mock()

        async def async_callback():
            """Async callback."""
            callback()

        action = ActionCallback(xknx, async_callback)
        self.loop.run_until_complete(asyncio.Task(action.execute()))
        callback.assert_called_with()
