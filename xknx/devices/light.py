"""
Module for managing a light via KNX.

It provides functionality for

* switching light 'on' and 'off'.
* setting the brightness.
* setting the color.
* setting the relative color temperature (tunable white).
* setting the absolute color temperature.
* reading the current state from KNX bus.
"""
from enum import Enum
import logging
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterator,
    Optional,
    Tuple,
)

from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueColorRGB,
    RemoteValueColorRGBW,
    RemoteValueDpt2ByteUnsigned,
    RemoteValueScaling,
    RemoteValueSwitch,
)

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

AsyncCallback = Callable[[], Awaitable[None]]

logger = logging.getLogger("xknx.log")


class ColorTempModes(Enum):
    """Color temperature modes for config validation."""

    ABSOLUTE = "DPT-7.600"
    RELATIVE = "DPT-5.001"


class _SwitchAndBrightness:
    def __init__(
        self,
        xknx: "XKNX",
        name: str,
        feature_name: str,
        group_address_switch: Optional[GroupAddressesType] = None,
        group_address_switch_state: Optional[GroupAddressesType] = None,
        group_address_brightness: Optional[GroupAddressesType] = None,
        group_address_brightness_state: Optional[GroupAddressesType] = None,
        after_update_cb: Optional[AsyncCallback] = None,
    ):
        self.switch = RemoteValueSwitch(
            xknx,
            group_address_switch,
            group_address_switch_state,
            device_name=name,
            feature_name=feature_name + "_state",
            after_update_cb=after_update_cb,
        )
        self.brightness = RemoteValueScaling(
            xknx,
            group_address_brightness,
            group_address_brightness_state,
            device_name=name,
            feature_name=feature_name + "_brightness",
            after_update_cb=after_update_cb,
            range_from=0,
            range_to=255,
        )

    @property
    def is_on(self) -> Optional[bool]:
        """Return if light is on."""
        return self.switch.value  # type: ignore

    async def set_on(self) -> None:
        """Switch light on."""
        if self.switch.initialized:
            await self.switch.on()

    async def set_off(self) -> None:
        """Switch light off."""
        if self.switch.initialized:
            await self.switch.off()

    def __eq__(self, other: object) -> bool:
        """Compare for quality."""
        return self.__dict__ == other.__dict__


# pylint: disable=too-many-public-methods, too-many-instance-attributes
class Light(Device):
    """Class for managing a light."""

    # pylint: disable=too-many-locals
    DEFAULT_MIN_KELVIN = 2700  # 370 mireds
    DEFAULT_MAX_KELVIN = 6000  # 166 mireds

    def __init__(
        self,
        xknx: "XKNX",
        name: str,
        group_address_switch: Optional[GroupAddressesType] = None,
        group_address_switch_state: Optional[GroupAddressesType] = None,
        group_address_brightness: Optional[GroupAddressesType] = None,
        group_address_brightness_state: Optional[GroupAddressesType] = None,
        group_address_color: Optional[GroupAddressesType] = None,
        group_address_color_state: Optional[GroupAddressesType] = None,
        group_address_rgbw: Optional[GroupAddressesType] = None,
        group_address_rgbw_state: Optional[GroupAddressesType] = None,
        group_address_tunable_white: Optional[GroupAddressesType] = None,
        group_address_tunable_white_state: Optional[GroupAddressesType] = None,
        group_address_color_temperature: Optional[GroupAddressesType] = None,
        group_address_color_temperature_state: Optional[GroupAddressesType] = None,
        group_address_switch_red: Optional[GroupAddressesType] = None,
        group_address_switch_red_state: Optional[GroupAddressesType] = None,
        group_address_brightness_red: Optional[GroupAddressesType] = None,
        group_address_brightness_red_state: Optional[GroupAddressesType] = None,
        group_address_switch_green: Optional[GroupAddressesType] = None,
        group_address_switch_green_state: Optional[GroupAddressesType] = None,
        group_address_brightness_green: Optional[GroupAddressesType] = None,
        group_address_brightness_green_state: Optional[GroupAddressesType] = None,
        group_address_switch_blue: Optional[GroupAddressesType] = None,
        group_address_switch_blue_state: Optional[GroupAddressesType] = None,
        group_address_brightness_blue: Optional[GroupAddressesType] = None,
        group_address_brightness_blue_state: Optional[GroupAddressesType] = None,
        group_address_switch_white: Optional[GroupAddressesType] = None,
        group_address_switch_white_state: Optional[GroupAddressesType] = None,
        group_address_brightness_white: Optional[GroupAddressesType] = None,
        group_address_brightness_white_state: Optional[GroupAddressesType] = None,
        min_kelvin: Optional[int] = None,
        max_kelvin: Optional[int] = None,
        device_updated_cb: Optional[DeviceCallbackType] = None,
    ):
        """Initialize Light class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, name, device_updated_cb)

        self.switch = RemoteValueSwitch(
            xknx,
            group_address_switch,
            group_address_switch_state,
            device_name=self.name,
            feature_name="State",
            after_update_cb=self.after_update,
        )

        self.brightness = RemoteValueScaling(
            xknx,
            group_address_brightness,
            group_address_brightness_state,
            device_name=self.name,
            feature_name="Brightness",
            after_update_cb=self.after_update,
            range_from=0,
            range_to=255,
        )

        self.color = RemoteValueColorRGB(
            xknx,
            group_address_color,
            group_address_color_state,
            device_name=self.name,
            after_update_cb=self.after_update,
        )

        self.rgbw = RemoteValueColorRGBW(
            xknx,
            group_address_rgbw,
            group_address_rgbw_state,
            device_name=self.name,
            after_update_cb=self.after_update,
        )

        self.tunable_white = RemoteValueScaling(
            xknx,
            group_address_tunable_white,
            group_address_tunable_white_state,
            device_name=self.name,
            feature_name="Tunable white",
            after_update_cb=self.after_update,
            range_from=0,
            range_to=255,
        )

        self.color_temperature = RemoteValueDpt2ByteUnsigned(
            xknx,
            group_address_color_temperature,
            group_address_color_temperature_state,
            device_name=self.name,
            feature_name="Color temperature",
            after_update_cb=self.after_update,
        )

        self.red = _SwitchAndBrightness(
            xknx,
            self.name,
            "red",
            group_address_switch_red,
            group_address_switch_red_state,
            group_address_brightness_red,
            group_address_brightness_red_state,
            self.after_update,
        )

        self.green = _SwitchAndBrightness(
            xknx,
            self.name,
            "green",
            group_address_switch_green,
            group_address_switch_green_state,
            group_address_brightness_green,
            group_address_brightness_green_state,
            self.after_update,
        )

        self.blue = _SwitchAndBrightness(
            xknx,
            self.name,
            "blue",
            group_address_switch_blue,
            group_address_switch_blue_state,
            group_address_brightness_blue,
            group_address_brightness_blue_state,
            self.after_update,
        )

        self.white = _SwitchAndBrightness(
            xknx,
            self.name,
            "white",
            group_address_switch_white,
            group_address_switch_white_state,
            group_address_brightness_white,
            group_address_brightness_white_state,
            self.after_update,
        )

        self.min_kelvin = min_kelvin
        self.max_kelvin = max_kelvin

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any]]:
        """Iterate the devices RemoteValue classes."""
        yield self.switch
        yield self.brightness
        yield self.color
        yield self.rgbw
        yield self.tunable_white
        yield self.color_temperature
        for color in self._iter_individual_colors():
            yield color.switch
            yield color.brightness

    def _iter_individual_colors(self) -> Iterator[_SwitchAndBrightness]:
        """Iterate the devices individual colors."""
        yield from (self.red, self.green, self.blue, self.white)

    @property
    def supports_brightness(self) -> bool:
        """Return if light supports brightness."""
        return self.brightness.initialized

    @property
    def supports_color(self) -> bool:
        """Return if light supports color."""
        return self.color.initialized or all(
            c.brightness.initialized for c in (self.red, self.green, self.blue)
        )

    @property
    def supports_rgbw(self) -> bool:
        """Return if light supports RGBW."""
        return self.rgbw.initialized or all(
            c.brightness.initialized for c in self._iter_individual_colors()
        )

    @property
    def supports_tunable_white(self) -> bool:
        """Return if light supports tunable white / relative color temperature."""
        return self.tunable_white.initialized

    @property
    def supports_color_temperature(self) -> bool:
        """Return if light supports absolute color temperature."""
        return self.color_temperature.initialized

    @classmethod
    def read_color_from_config(
        cls, color: str, config: Any
    ) -> Tuple[
        Optional[GroupAddressesType],
        Optional[GroupAddressesType],
        Optional[GroupAddressesType],
        Optional[GroupAddressesType],
    ]:
        """Load color configuration from configuration structure."""
        if "individual_colors" in config and color in config["individual_colors"]:
            sub_config = config["individual_colors"][color]
            return (
                sub_config.get("group_address_switch"),
                sub_config.get("group_address_switch_state"),
                sub_config.get("group_address_brightness"),
                sub_config.get("group_address_brightness_state"),
            )
        return None, None, None, None

    @classmethod
    def from_config(cls, xknx: "XKNX", name: str, config: Dict[str, Any]) -> "Light":
        """Initialize object from configuration structure."""
        group_address_switch = config.get("group_address_switch")
        group_address_switch_state = config.get("group_address_switch_state")
        group_address_brightness = config.get("group_address_brightness")
        group_address_brightness_state = config.get("group_address_brightness_state")
        group_address_color = config.get("group_address_color")
        group_address_color_state = config.get("group_address_color_state")
        group_address_rgbw = config.get("group_address_rgbw")
        group_address_rgbw_state = config.get("group_address_rgbw_state")
        group_address_tunable_white = config.get("group_address_tunable_white")
        group_address_tunable_white_state = config.get(
            "group_address_tunable_white_state"
        )
        group_address_color_temperature = config.get("group_address_color_temperature")
        group_address_color_temperature_state = config.get(
            "group_address_color_temperature_state"
        )
        min_kelvin = config.get("min_kelvin", Light.DEFAULT_MIN_KELVIN)
        max_kelvin = config.get("max_kelvin", Light.DEFAULT_MAX_KELVIN)

        (
            red_switch,
            red_switch_state,
            red_brightness,
            red_brightness_state,
        ) = cls.read_color_from_config("red", config)
        (
            green_switch,
            green_switch_state,
            green_brightness,
            green_brightness_state,
        ) = cls.read_color_from_config("green", config)
        (
            blue_switch,
            blue_switch_state,
            blue_brightness,
            blue_brightness_state,
        ) = cls.read_color_from_config("blue", config)
        (
            white_switch,
            white_switch_state,
            white_brightness,
            white_brightness_state,
        ) = cls.read_color_from_config("white", config)

        return cls(
            xknx,
            name,
            group_address_switch=group_address_switch,
            group_address_switch_state=group_address_switch_state,
            group_address_brightness=group_address_brightness,
            group_address_brightness_state=group_address_brightness_state,
            group_address_color=group_address_color,
            group_address_color_state=group_address_color_state,
            group_address_rgbw=group_address_rgbw,
            group_address_rgbw_state=group_address_rgbw_state,
            group_address_tunable_white=group_address_tunable_white,
            group_address_tunable_white_state=group_address_tunable_white_state,
            group_address_color_temperature=group_address_color_temperature,
            group_address_color_temperature_state=group_address_color_temperature_state,
            group_address_switch_red=red_switch,
            group_address_switch_red_state=red_switch_state,
            group_address_brightness_red=red_brightness,
            group_address_brightness_red_state=red_brightness_state,
            group_address_switch_green=green_switch,
            group_address_switch_green_state=green_switch_state,
            group_address_brightness_green=green_brightness,
            group_address_brightness_green_state=green_brightness_state,
            group_address_switch_blue=blue_switch,
            group_address_switch_blue_state=blue_switch_state,
            group_address_brightness_blue=blue_brightness,
            group_address_brightness_blue_state=blue_brightness_state,
            group_address_switch_white=white_switch,
            group_address_switch_white_state=white_switch_state,
            group_address_brightness_white=white_brightness,
            group_address_brightness_white_state=white_brightness_state,
            min_kelvin=min_kelvin,
            max_kelvin=max_kelvin,
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        str_brightness = (
            ""
            if not self.supports_brightness
            else f' brightness="{self.brightness.group_addr_str()}"'
        )

        str_color = (
            "" if not self.supports_color else f' color="{self.color.group_addr_str()}"'
        )

        str_rgbw = (
            "" if not self.supports_rgbw else f' rgbw="{self.rgbw.group_addr_str()}"'
        )

        str_tunable_white = (
            ""
            if not self.supports_tunable_white
            else f' tunable white="{self.tunable_white.group_addr_str()}"'
        )

        str_color_temperature = (
            ""
            if not self.supports_color_temperature
            else ' color temperature="{}"'.format(
                self.color_temperature.group_addr_str()
            )
        )

        str_red_state = (
            ""
            if not self.red.switch.initialized
            else f' red_state="{self.red.switch.group_addr_str()}"'
        )
        str_red_brightness = (
            ""
            if not self.red.brightness.initialized
            else f' red_brightness="{self.red.brightness.group_addr_str()}"'
        )

        str_green_state = (
            ""
            if not self.green.switch.initialized
            else f' green_state="{self.green.switch.group_addr_str()}"'
        )
        str_green_brightness = (
            ""
            if not self.green.brightness.initialized
            else f' green_brightness="{self.green.brightness.group_addr_str()}"'
        )

        str_blue_state = (
            ""
            if not self.blue.switch.initialized
            else f' blue_state="{self.blue.switch.group_addr_str()}"'
        )
        str_blue_brightness = (
            ""
            if not self.blue.brightness.initialized
            else f' blue_brightness="{self.blue.brightness.group_addr_str()}"'
        )

        str_white_state = (
            ""
            if not self.white.switch.initialized
            else f' white_state="{self.white.switch.group_addr_str()}"'
        )
        str_white_brightness = (
            ""
            if not self.white.brightness.initialized
            else f' white_brightness="{self.white.brightness.group_addr_str()}"'
        )

        return '<Light name="{}" ' 'switch="{}"{}{}{}{}{}{}{}{}{}{}{}{}{} />'.format(
            self.name,
            self.switch.group_addr_str(),
            str_brightness,
            str_color,
            str_rgbw,
            str_tunable_white,
            str_color_temperature,
            str_red_state,
            str_red_brightness,
            str_green_state,
            str_green_brightness,
            str_blue_state,
            str_blue_brightness,
            str_white_state,
            str_white_brightness,
        )

    @property
    def state(self) -> Optional[bool]:
        """Return the current switch state of the device."""
        if self.switch.value is not None:
            return self.switch.value  # type: ignore
        if any(c.switch.value is not None for c in self._iter_individual_colors()):
            return any(c.switch.value for c in self._iter_individual_colors())
        return None

    async def set_on(self) -> None:
        """Switch light on."""
        if self.switch.initialized:
            await self.switch.on()
        for color in self._iter_individual_colors():
            await color.set_on()

    async def set_off(self) -> None:
        """Switch light off."""
        if self.switch.initialized:
            await self.switch.off()
        for color in self._iter_individual_colors():
            await color.set_off()

    @property
    def current_brightness(self) -> Optional[int]:
        """Return current brightness of light."""
        return self.brightness.value  # type: ignore

    async def set_brightness(self, brightness: int) -> None:
        """Set brightness of light."""
        if not self.supports_brightness:
            logger.warning("Dimming not supported for device %s", self.get_name())
            return
        await self.brightness.set(brightness)

    @property
    def current_color(self) -> Tuple[Optional[Tuple[int, int, int]], Optional[int]]:
        """
        Return current color of light.

        If the device supports RGBW, get the current RGB+White values instead.
        """
        if self.supports_rgbw:
            if self.rgbw.initialized:
                if not self.rgbw.value:
                    return None, None
                return self.rgbw.value[:3], self.rgbw.value[3]
        if self.color.initialized:
            return self.color.value, None
        # individual RGB addresses - white will return None when it is not initialized
        colors = (
            self.red.brightness.value,
            self.green.brightness.value,
            self.blue.brightness.value,
        )
        if None in colors:
            return None, self.white.brightness.value
        return colors, self.white.brightness.value

    async def set_color(
        self, color: Tuple[int, int, int], white: Optional[int] = None
    ) -> None:
        """
        Set color of a light device.

        If also the white value is given and the device supports RGBW,
        set all four values.
        """
        if white is not None:
            if self.supports_rgbw:
                if self.rgbw.initialized:
                    await self.rgbw.set(list(color) + [white])
                    return
                if all(
                    c.brightness.initialized for c in self._iter_individual_colors()
                ):
                    await self.red.brightness.set(color[0])
                    await self.green.brightness.set(color[1])
                    await self.blue.brightness.set(color[2])
                    await self.white.brightness.set(white)
                    return
            logger.warning("RGBW not supported for device %s", self.get_name())
        else:
            if self.supports_color:
                if self.color.initialized:
                    await self.color.set(color)
                    return
                if all(
                    c.brightness.initialized for c in (self.red, self.green, self.blue)
                ):
                    await self.red.brightness.set(color[0])
                    await self.green.brightness.set(color[1])
                    await self.blue.brightness.set(color[2])
                    return
            logger.warning("Colors not supported for device %s", self.get_name())

    @property
    def current_tunable_white(self) -> Optional[int]:
        """Return current relative color temperature of light."""
        return self.tunable_white.value  # type: ignore

    async def set_tunable_white(self, tunable_white: int) -> None:
        """Set relative color temperature of light."""
        if not self.supports_tunable_white:
            logger.warning("Tunable white not supported for device %s", self.get_name())
            return
        await self.tunable_white.set(tunable_white)

    @property
    def current_color_temperature(self) -> Optional[int]:
        """Return current absolute color temperature of light."""
        return self.color_temperature.value  # type: ignore

    async def set_color_temperature(self, color_temperature: int) -> None:
        """Set absolute color temperature of light."""
        if not self.supports_color_temperature:
            logger.warning(
                "Absolute Color Temperature not supported for device %s",
                self.get_name(),
            )
            return
        await self.color_temperature.set(color_temperature)

    async def do(self, action: str) -> None:
        """Execute 'do' commands."""
        if action == "on":
            await self.set_on()
        elif action == "off":
            await self.set_off()
        elif action.startswith("brightness:"):
            await self.set_brightness(int(action[11:]))
        elif action.startswith("tunable_white:"):
            await self.set_tunable_white(int(action[14:]))
        elif action.startswith("color_temperature:"):
            await self.set_color_temperature(int(action[18:]))
        else:
            logger.warning(
                "Could not understand action %s for device %s", action, self.get_name()
            )

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        for remote_value in self._iter_remote_values():
            await remote_value.process(telegram)
