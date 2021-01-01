"""Unit test for payload reader."""
import asyncio
import unittest
from unittest.mock import MagicMock, patch

from xknx import XKNX
from xknx.core import PayloadReader
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection
from xknx.telegram.apci import MemoryRead, MemoryResponse


class TestPayloadReader(unittest.TestCase):
    """Test class for payload reader."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def create_telegram_queue_mock(self, xknx: XKNX, response_telegram: Telegram):
        """
        Create a TelegramQueue mock that returns a specific response telegram.
        """
        xknx.telegram_queue = MagicMock()

        def _register_telegram_received_cb(func):
            self.loop.create_task(func(response_telegram))

        xknx.telegram_queue.register_telegram_received_cb.side_effect = (
            _register_telegram_received_cb
        )

    def test_payload_reader_send_success(self):
        """Test payload reader: successful send."""
        xknx = XKNX()

        destination_address = IndividualAddress("1.2.3")
        request_payload = MemoryRead(0xAABB, 3)
        response_payload = MemoryResponse(0xAABB, 3, bytes([0x00, 0x11, 0x33]))

        response_telegram = Telegram(
            source_address=destination_address,
            direction=TelegramDirection.INCOMING,
            payload=response_payload,
        )

        self.create_telegram_queue_mock(xknx, response_telegram)

        payload_reader = PayloadReader(xknx, destination_address)

        payload = self.loop.run_until_complete(
            payload_reader.send(request_payload, response_class=MemoryResponse)
        )

        # Response is received.
        self.assertEqual(payload, response_payload)

    @patch("logging.Logger.warning")
    def test_payload_reader_send_timeout(self, logger_warning_mock):
        """Test payload reader: timeout while waiting for response."""
        xknx = XKNX()

        destination_address = IndividualAddress("1.2.3")
        request_payload = MemoryRead(0xAABB, 3)

        payload_reader = PayloadReader(xknx, destination_address, timeout_in_seconds=0)

        payload = self.loop.run_until_complete(
            payload_reader.send(request_payload, response_class=MemoryResponse)
        )

        # No response received.
        self.assertEqual(payload, None)
        # Warning was logged.
        logger_warning_mock.assert_called_once_with(
            "Error: KNX bus did not respond in time (%s secs) to payload request for: %s",
            0.0,
            IndividualAddress("1.2.3"),
        )
