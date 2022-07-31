"""
Abstract base for a specific KNX/IP connection (Tunneling or Routing).

* It handles connection and disconnections
* It starts and stops a udp transport
* It packs Telegrams into KNX Frames and passes them to a udp transport
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import Callable, Optional

from xknx.telegram import Telegram

TelegramCallbackType = Callable[[Telegram], Awaitable[Optional[list[Telegram]]]]


class Interface(ABC):
    """Abstract base class for KNX/IP connections."""

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to KNX bus. Returns True on success."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from KNX bus."""

    @abstractmethod
    async def send_telegram(self, telegram: Telegram) -> None:
        """Send Telegram to KNX bus."""
