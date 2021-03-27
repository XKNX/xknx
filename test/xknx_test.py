"""Unit test for XKNX Module."""
import asyncio
import os
import unittest
from unittest.mock import MagicMock, patch

from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType


# pylint: disable=too-many-public-methods,invalid-name,useless-super-delegation,protected-access
class AsyncMock(MagicMock):
    """Async Mock."""

    # pylint: disable=invalid-overridden-method
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class TestXknxModule(unittest.TestCase):
    """Test class for XKNX."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_log_to_file(self):
        """Test logging enable."""
        XKNX(log_directory="/tmp/")

        self.assertTrue(os.path.isfile("/tmp/xknx.log"))

        os.remove("/tmp/xknx.log")

    def test_log_to_file_when_dir_does_not_exist(self):
        """Test logging enable with non existent directory."""
        XKNX(log_directory="/xknx/is/fun")

        self.assertFalse(os.path.isfile("/xknx/is/fun/xknx.log"))

    def test_register_telegram_cb(self):
        """Test register telegram callback."""

        async def telegram_received(telegram):
            """Telegram received."""

        xknx = XKNX(telegram_received_cb=telegram_received)

        self.assertEqual(len(xknx.telegram_queue.telegram_received_cbs), 1)

    def test_register_device_cb(self):
        """Test register telegram callback."""

        async def device_update(device):
            """Device updated."""

        xknx = XKNX(device_updated_cb=device_update)

        self.assertEqual(len(xknx.devices.device_updated_cbs), 1)

    @patch("xknx.io.KNXIPInterface.start", new_callable=AsyncMock)
    def test_xknx_start(self, start_mock):
        """Test xknx start."""
        xknx = XKNX(state_updater=True)

        self.loop.run_until_complete(xknx.start())

        start_mock.assert_called_once()
        self.loop.run_until_complete(xknx.stop())

    @patch("xknx.io.KNXIPInterface.start", new_callable=AsyncMock)
    def test_xknx_start_as_context_manager(self, ipinterface_mock):
        """Test xknx start."""

        async def run_in_contextmanager():
            async with XKNX(state_updater=True) as xknx:
                self.assertTrue(xknx.started.is_set())
                ipinterface_mock.assert_called_once()

        self.loop.run_until_complete(run_in_contextmanager())

    @patch("xknx.io.KNXIPInterface.start", new_callable=AsyncMock)
    def test_xknx_start_and_stop_with_dedicated_connection_config(self, start_mock):
        """Test xknx start and stop with connection config."""
        xknx = XKNX()

        connection_config = ConnectionConfig(connection_type=ConnectionType.TUNNELING)
        xknx.connection_config = connection_config

        self.loop.run_until_complete(xknx.start())

        start_mock.assert_called_once()
        self.assertEqual(xknx.knxip_interface.connection_config, connection_config)

        self.loop.run_until_complete(xknx.stop())
        self.assertIsNone(xknx.knxip_interface)
        self.assertTrue(xknx.telegram_queue._consumer_task.done())
        self.assertFalse(xknx.state_updater.started)
