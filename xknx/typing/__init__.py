"""Types used by XKNX."""

from collections.abc import Callable
import sys
from typing import TYPE_CHECKING, TypedDict

if sys.version_info >= (3, 13):
    # TypeVar(..., default=...) - PEP 696 - is only in stdlib typing since 3.13
    from typing import TypeVar as TypeVar
else:
    from typing_extensions import TypeVar as TypeVar

if TYPE_CHECKING:
    from xknx.core.connection_manager import XknxConnectionState
    from xknx.devices import Device
    from xknx.telegram import Telegram

CallbackType = Callable[[], None]

ConnectionChangeCallbackType = Callable[["XknxConnectionState"], None]

DeviceT = TypeVar("DeviceT", bound="Device")
DeviceCallbackType = Callable[[DeviceT], None]

TelegramCallbackType = Callable[["Telegram"], None]


class DPTMainSubDict(TypedDict):
    """DPT type dictionary in accordance to xknxproject DPTType data."""

    main: int
    sub: int | None


DPTParsable = str | int | DPTMainSubDict
