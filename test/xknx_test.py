"""Unit test for XKNX Module."""
import asyncio
import os
import unittest
from unittest.mock import patch

from xknx import XKNX

# pylint: disable=too-many-public-methods,invalid-name
from xknx.io import ConnectionConfig, ConnectionType


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
        xknx = XKNX(loop=self.loop, log_to_file=True)

        self.assertTrue(os.path.isfile("xknx.log"))

        os.remove("xknx.log")

    def test_register_telegram_cb(self):
        """Test register telegram callback."""

        async def telegram_received(telegram):
            """Telegram received."""
            pass  # tested in telegram queue

        xknx = XKNX(loop=self.loop, telegram_received_cb=telegram_received)

        self.assertEqual(len(xknx.telegram_queue.telegram_received_cbs), 1)

    def test_register_device_cb(self):
        """Test register telegram callback."""

        async def device_update(device):
            """Device updated."""
            pass  # tested in devices

        xknx = XKNX(loop=self.loop, device_updated_cb=device_update)

        self.assertEqual(len(xknx.devices.device_updated_cbs), 1)

    @patch("xknx.io.KNXIPInterface.start")
    def test_xknx_start(self, start_mock):
        """Test xknx start."""
        xknx = XKNX(loop=self.loop)

        self.loop.run_until_complete(xknx.start(state_updater=True))

        start_mock.assert_called_once()

    @patch("xknx.io.KNXIPInterface.start")
    def test_xknx_start_with_dedicated_connection_config(self, start_mock):
        """Test xknx start with connection config."""
        xknx = XKNX(loop=self.loop)

        connection_config = ConnectionConfig(connection_type=ConnectionType.TUNNELING)
        xknx.connection_config = connection_config

        self.loop.run_until_complete(xknx.start(state_updater=True))

        start_mock.assert_called_once()
        self.assertEqual(xknx.knxip_interface.connection_config, connection_config)

        with patch("xknx.core.TelegramQueue.stop") as tq_stop, patch(
            "xknx.core.StateUpdater.stop"
        ) as updater_stop:
            self.loop.run_until_complete(xknx.stop())
            tq_stop.assert_called_once()
            updater_stop.assert_called_once()
            self.assertIsNone(xknx.knxip_interface)
