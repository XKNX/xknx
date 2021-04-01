"""Unit test for Action objects."""
from unittest.mock import Mock, patch

import pytest
from xknx import XKNX
from xknx.devices import Action, ActionBase, ActionCallback, Light

from test.util import AsyncMock


# pylint: disable=no-self-use
@pytest.mark.asyncio
class TestAction:
    """Class for testing Action objects."""

    #
    # TEST COUNTER
    #
    def test_counter(self):
        """Test counter method."""
        xknx = XKNX()
        action = ActionBase(xknx, counter=2)
        assert action.test_counter(None)
        assert not action.test_counter(1)
        assert action.test_counter(2)
        assert not action.test_counter(3)

    def test_no_counter(self):
        """Test counter method with no counter set."""
        xknx = XKNX()
        action = ActionBase(xknx, counter=None)
        assert action.test_counter(None)
        assert action.test_counter(1)
        assert action.test_counter(2)
        assert action.test_counter(3)

    #
    # TEST APPLICABLE
    #
    def test_if_applicable_hook_on(self):
        """Test test_if_applicable method with hook set to 'on'."""
        xknx = XKNX()
        action = ActionBase(xknx, counter=2, hook="on")
        assert action.test_if_applicable(True, 2)
        assert not action.test_if_applicable(True, 3)
        assert not action.test_if_applicable(False, 2)

    def test_if_applicable_hook_off(self):
        """Test test_if_applicable method with hook set to 'off'."""
        xknx = XKNX()
        action = ActionBase(xknx, counter=2, hook="off")
        assert action.test_if_applicable(False, 2)
        assert not action.test_if_applicable(False, 3)
        assert not action.test_if_applicable(True, 2)

    #
    # TEST EXECUTE
    #
    async def test_execute_base_action(self):
        """Test if execute method of BaseAction shows correct info message."""
        xknx = XKNX()
        action = ActionBase(xknx)
        with patch("logging.Logger.info") as mock_info:
            await action.execute()
            mock_info.assert_called_with("Execute not implemented for %s", "ActionBase")

    @patch("xknx.devices.Light.do", new_callable=AsyncMock)
    async def test_execute_action(self, mock_do):
        """Test if execute method of Action calls correct do method of device."""
        xknx = XKNX()
        light = Light(xknx, "Light1", group_address_switch="1/6/4")
        action = Action(xknx, target=light.name, method="on")

        await action.execute()
        mock_do.assert_called_with("on")

    async def test_execute_action_callback(self):
        """Test if execute method of ActionCallback calls correct callback method."""
        xknx = XKNX()
        callback = Mock()

        async def async_callback():
            """Async callback."""
            callback()

        action = ActionCallback(xknx, async_callback)
        await action.execute()
        callback.assert_called_with()

    async def test_execute_unknown_device(self):
        """Test if execute method of Action calls correct do method of device."""
        xknx = XKNX()

        action = Action(xknx, target="Light1", method="on")
        with patch("logging.Logger.warning") as logger_warning_mock:
            await action.execute()
            logger_warning_mock.assert_called_once_with(
                "Unknown device %s witin action %s.", action.target, action
            )
