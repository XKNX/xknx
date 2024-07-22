"""Types used by XKNX."""

from collections.abc import Callable
import sys
from typing import TYPE_CHECKING, TypeVar

if sys.version_info >= (3, 11):
    from typing import Self as Self
else:
    from typing_extensions import Self as Self

if TYPE_CHECKING:
    from xknx.core.connection_manager import XknxConnectionState
    from xknx.devices import Device
    from xknx.telegram import Telegram

CallbackType = Callable[[], None]

ConnectionChangeCallbackType = Callable[["XknxConnectionState"], None]

DeviceT = TypeVar("DeviceT", bound="Device")
DeviceCallbackType = Callable[[DeviceT], None]

TelegramCallbackType = Callable[["Telegram"], None]
