"""Unit test for XKNX Module."""
import os
from unittest.mock import AsyncMock, patch

import pytest
from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType


@pytest.mark.asyncio
class TestXknxModule:
    """Test class for XKNX."""

    def test_log_to_file(self):
        """Test logging enable."""
        XKNX(log_directory="/tmp/")

        assert os.path.isfile("/tmp/xknx.log")

        os.remove("/tmp/xknx.log")

    def test_log_to_file_when_dir_does_not_exist(self):
        """Test logging enable with non existent directory."""
        XKNX(log_directory="/xknx/is/fun")

        assert not os.path.isfile("/xknx/is/fun/xknx.log")

    def test_register_telegram_cb(self):
        """Test register telegram callback."""

        async def telegram_received(telegram):
            """Telegram received."""

        xknx = XKNX(telegram_received_cb=telegram_received)

        assert len(xknx.telegram_queue.telegram_received_cbs) == 1

    def test_register_device_cb(self):
        """Test register telegram callback."""

        async def device_update(device):
            """Device updated."""

        xknx = XKNX(device_updated_cb=device_update)

        assert len(xknx.devices.device_updated_cbs) == 1

    def test_register_connection_state_change_cb(self):
        """Test register con state callback."""

        async def con_state_change(connection_state):
            """Connection State Changed."""

        xknx = XKNX(connection_state_changed_cb=con_state_change)

        assert len(xknx.connection_manager._connection_state_changed_cbs) == 1

    @patch("xknx.io.KNXIPInterface._start", new_callable=AsyncMock)
    async def test_xknx_start(self, start_mock):
        """Test xknx start."""
        xknx = XKNX(state_updater=True)

        await xknx.start()
        start_mock.assert_called_once()
        await xknx.stop()

    @patch("xknx.io.KNXIPInterface._start", new_callable=AsyncMock)
    async def test_xknx_start_as_context_manager(self, ipinterface_mock):
        """Test xknx start."""

        async def run_in_contextmanager():
            async with XKNX(state_updater=True) as xknx:
                assert xknx.started.is_set()
                ipinterface_mock.assert_called_once()

        await run_in_contextmanager()

    @patch("xknx.io.KNXIPInterface._start", new_callable=AsyncMock)
    async def test_xknx_start_and_stop_with_dedicated_connection_config(
        self, start_mock
    ):
        """Test xknx start and stop with connection config."""
        xknx = XKNX()

        connection_config = ConnectionConfig(connection_type=ConnectionType.TUNNELING)
        xknx.connection_config = connection_config

        await xknx.start()

        start_mock.assert_called_once()
        assert xknx.knxip_interface.connection_config == connection_config

        await xknx.stop()
        assert xknx.knxip_interface is None
        assert xknx.telegram_queue._consumer_task.done()
        assert not xknx.state_updater.started
