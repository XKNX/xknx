"""Types used by XKNX."""

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from xknx.devices import Device

CallbackType = Callable[[], None]

DeviceT = TypeVar("DeviceT", bound="Device")
DeviceCallbackType = Callable[[DeviceT], None]
