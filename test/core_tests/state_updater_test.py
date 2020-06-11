"""Unit test for KNX/IP Disconnect Request/Response."""
import anyio
from unittest.mock import patch

import pytest

from xknx import XKNX
from xknx.core import StateUpdater
from xknx.devices import Light

from xknx._test import Testcase, AsyncMock, xknx_running

class TestStateupdater(Testcase):
    """Test class for xknx/io/Disconnect objects."""

    @pytest.mark.anyio
    async def test_state_updater(self):
        """Test State updater."""
        async with xknx_running() as xknx:
            light = Light(
                xknx,
                name='TestLight',
                group_address_switch='1/0/9')
            xknx.devices.add(light)
            state_updater = StateUpdater(xknx, timeout=0, start_timeout=0)

            async def stopper():
                await state_updater.stop()

            with patch('xknx.devices.Device.sync', new_callable=AsyncMock,
                    side_effect=stopper) as mock_sync:
                await state_updater.start()
                await anyio.sleep(0.2)
                mock_sync.assert_called_with()
