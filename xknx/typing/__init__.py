"""Types used by XKNX."""

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from xknx.devices import Device
    from xknx.telegram import Telegram

CallbackType = Callable[[], None]

DeviceT = TypeVar("DeviceT", bound="Device")
DeviceCallbackType = Callable[[DeviceT], None]

TelegramCallbackType = Callable[["Telegram"], None]
