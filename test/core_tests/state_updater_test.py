"""Unit test for KNX/IP Disconnect Request/Response."""
import asyncio
import unittest
from unittest.mock import patch

import pytest

from xknx import XKNX
from xknx.core import StateUpdater
from xknx.devices import Light

from xknx._test import Testcase

class TestStateupdater(Testcase):
    """Test class for xknx/io/Disconnect objects."""

    @pytest.mark.asyncio
    async def test_state_updater(self):
        """Test State updater."""
        xknx = XKNX()
        light = Light(
            xknx,
            name='TestLight',
            group_address_switch='1/0/9')
        xknx.devices.add(light)

        state_updater = StateUpdater(xknx, timeout=0, start_timeout=0)
        state_updater.run_forever = False

        with patch('xknx.devices.Device.sync') as mock_sync:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_sync.return_value = fut

            await state_updater.start()
            await state_updater.run_task
            mock_sync.assert_called_with()
