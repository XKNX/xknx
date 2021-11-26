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
from __future__ import annotations

import asyncio
from enum import Enum
from itertools import chain
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Iterator, Tuple, cast

from xknx.dpt.dpt_color import XYYColor
from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueColorRGB,
    RemoteValueColorRGBW,
    RemoteValueColorXYY,
    RemoteValueDpt2ByteUnsigned,
    RemoteValueNumeric,
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
        xknx: XKNX,
        name: str,
        feature_name: str,
        group_address_switch: GroupAddressesType | None = None,
        group_address_switch_state: GroupAddressesType | None = None,
        group_address_brightness: GroupAddressesType | None = None,
        group_address_brightness_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        after_update_cb: AsyncCallback | None = None,
    ):
        self.switch = RemoteValueSwitch(
            xknx,
            group_address_switch,
            group_address_switch_state,
            sync_state=sync_state,
            device_name=name,
            feature_name=feature_name + "_state",
            after_update_cb=after_update_cb,
        )
        self.brightness = RemoteValueScaling(
            xknx,
            group_address_brightness,
            group_address_brightness_state,
            sync_state=sync_state,
            device_name=name,
            feature_name=feature_name + "_brightness",
            after_update_cb=after_update_cb,
            range_from=0,
            range_to=255,
        )

    @property
    def is_on(self) -> bool | None:
        """Return if light is on."""
        if self.switch.initialized:
            return self.switch.value
        if self.brightness.initialized and self.brightness.value is not None:
            return bool(self.brightness.value)
        return None

    async def set_on(self) -> None:
        """Switch light on."""
        if self.switch.writable:
            await self.switch.on()
            return
        if self.brightness.writable:
            await self.brightness.set(self.brightness.range_to)

    async def set_off(self) -> None:
        """Switch light off."""
        if self.switch.writable:
            await self.switch.off()
            return
        if self.brightness.writable:
            await self.brightness.set(0)

    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        return self.__dict__ == other.__dict__


class Light(Device):
    """Class for managing a light."""

    DEBOUNCE_TIMEOUT = 0.2
    DEFAULT_MIN_KELVIN = 2700  # 370 mireds
    DEFAULT_MAX_KELVIN = 6000  # 166 mireds

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address_switch: GroupAddressesType | None = None,
        group_address_switch_state: GroupAddressesType | None = None,
        group_address_brightness: GroupAddressesType | None = None,
        group_address_brightness_state: GroupAddressesType | None = None,
        group_address_color: GroupAddressesType | None = None,
        group_address_color_state: GroupAddressesType | None = None,
        group_address_rgbw: GroupAddressesType | None = None,
        group_address_rgbw_state: GroupAddressesType | None = None,
        group_address_hue: GroupAddressesType | None = None,
        group_address_hue_state: GroupAddressesType | None = None,
        group_address_saturation: GroupAddressesType | None = None,
        group_address_saturation_state: GroupAddressesType | None = None,
        group_address_xyy_color: GroupAddressesType | None = None,
        group_address_xyy_color_state: GroupAddressesType | None = None,
        group_address_tunable_white: GroupAddressesType | None = None,
        group_address_tunable_white_state: GroupAddressesType | None = None,
        group_address_color_temperature: GroupAddressesType | None = None,
        group_address_color_temperature_state: GroupAddressesType | None = None,
        group_address_switch_red: GroupAddressesType | None = None,
        group_address_switch_red_state: GroupAddressesType | None = None,
        group_address_brightness_red: GroupAddressesType | None = None,
        group_address_brightness_red_state: GroupAddressesType | None = None,
        group_address_switch_green: GroupAddressesType | None = None,
        group_address_switch_green_state: GroupAddressesType | None = None,
        group_address_brightness_green: GroupAddressesType | None = None,
        group_address_brightness_green_state: GroupAddressesType | None = None,
        group_address_switch_blue: GroupAddressesType | None = None,
        group_address_switch_blue_state: GroupAddressesType | None = None,
        group_address_brightness_blue: GroupAddressesType | None = None,
        group_address_brightness_blue_state: GroupAddressesType | None = None,
        group_address_switch_white: GroupAddressesType | None = None,
        group_address_switch_white_state: GroupAddressesType | None = None,
        group_address_brightness_white: GroupAddressesType | None = None,
        group_address_brightness_white_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        min_kelvin: int | None = None,
        max_kelvin: int | None = None,
        device_updated_cb: DeviceCallbackType | None = None,
    ):
        """Initialize Light class."""
        super().__init__(xknx, name, device_updated_cb)

        self.switch = RemoteValueSwitch(
            xknx,
            group_address_switch,
            group_address_switch_state,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="State",
            after_update_cb=self.after_update,
        )

        self.brightness = RemoteValueScaling(
            xknx,
            group_address_brightness,
            group_address_brightness_state,
            sync_state=sync_state,
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
            sync_state=sync_state,
            device_name=self.name,
            after_update_cb=self.after_update,
        )

        self.rgbw = RemoteValueColorRGBW(
            xknx,
            group_address_rgbw,
            group_address_rgbw_state,
            sync_state=sync_state,
            device_name=self.name,
            after_update_cb=self.after_update,
        )

        self.hue = RemoteValueNumeric(
            xknx,
            group_address_hue,
            group_address_hue_state,
            sync_state=sync_state,
            value_type="angle",
            device_name=self.name,
            feature_name="Hue",
            after_update_cb=self.after_update,
        )

        self.saturation = RemoteValueNumeric(
            xknx,
            group_address_saturation,
            group_address_saturation_state,
            sync_state=sync_state,
            value_type="percent",
            device_name=self.name,
            feature_name="Saturation",
            after_update_cb=self.after_update,
        )

        self._xyy_color_valid: XYYColor | None = None
        self.xyy_color = RemoteValueColorXYY(
            xknx,
            group_address_xyy_color,
            group_address_xyy_color_state,
            sync_state=sync_state,
            device_name=self.name,
            after_update_cb=self._xyy_color_from_rv,
        )

        self.tunable_white = RemoteValueScaling(
            xknx,
            group_address_tunable_white,
            group_address_tunable_white_state,
            sync_state=sync_state,
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
            sync_state=sync_state,
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
            sync_state=sync_state,
            after_update_cb=self._individual_color_callback_debounce,
        )

        self.green = _SwitchAndBrightness(
            xknx,
            self.name,
            "green",
            group_address_switch_green,
            group_address_switch_green_state,
            group_address_brightness_green,
            group_address_brightness_green_state,
            sync_state=sync_state,
            after_update_cb=self._individual_color_callback_debounce,
        )

        self.blue = _SwitchAndBrightness(
            xknx,
            self.name,
            "blue",
            group_address_switch_blue,
            group_address_switch_blue_state,
            group_address_brightness_blue,
            group_address_brightness_blue_state,
            sync_state=sync_state,
            after_update_cb=self._individual_color_callback_debounce,
        )

        self.white = _SwitchAndBrightness(
            xknx,
            self.name,
            "white",
            group_address_switch_white,
            group_address_switch_white_state,
            group_address_brightness_white,
            group_address_brightness_white_state,
            sync_state=sync_state,
            after_update_cb=self._individual_color_callback_debounce,
        )

        self.min_kelvin = min_kelvin
        self.max_kelvin = max_kelvin
        self._individual_color_debounce_task_name = (
            f"{id(self)}_individual_color_debounce"
        )
        self._individual_color_debounce_telegram_counter: int
        self._reset_individual_color_debounce_telegrams()

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate the devices RemoteValue classes."""
        return chain(
            self._iter_instant_remote_values(),
            self._iter_debounce_remote_values(),
        )

    def _iter_instant_remote_values(self) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate the devices RemoteValue classes calling after_update_cb immediately."""
        yield self.switch
        yield self.brightness
        yield self.color
        yield self.rgbw
        yield self.hue
        yield self.saturation
        yield self.xyy_color
        yield self.tunable_white
        yield self.color_temperature

    def _iter_debounce_remote_values(self) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate the devices RemoteValue classes debouncing after_update_cb."""
        for color in self._iter_individual_colors():
            yield color.switch
            yield color.brightness

    def _iter_individual_colors(self) -> Iterator[_SwitchAndBrightness]:
        """Iterate the devices individual colors."""
        yield from (self.red, self.green, self.blue, self.white)

    def _reset_individual_color_debounce_telegrams(self) -> None:
        """Reset individual color debounce telegram counter."""
        self._individual_color_debounce_telegram_counter = sum(
            (
                self.red.switch.initialized or self.red.brightness.initialized,
                self.green.switch.initialized or self.green.brightness.initialized,
                self.blue.switch.initialized or self.blue.brightness.initialized,
                self.white.switch.initialized or self.white.brightness.initialized,
            )
        )

    async def _individual_color_callback_debounce(self) -> None:
        """Run callback after all individual colors were updated or timeout passed."""

        async def debouncer() -> None:
            await asyncio.sleep(Light.DEBOUNCE_TIMEOUT)
            self._reset_individual_color_debounce_telegrams()
            await asyncio.shield(self.after_update())

        self._individual_color_debounce_telegram_counter -= 1
        if self._individual_color_debounce_telegram_counter > 0:
            # task registry cancels existing task
            self.xknx.task_registry.register(
                self._individual_color_debounce_task_name, debouncer()
            ).start()
            return
        self.xknx.task_registry.unregister(self._individual_color_debounce_task_name)
        self._reset_individual_color_debounce_telegrams()
        await self.after_update()

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
    def supports_hs_color(self) -> bool:
        """Return if light supports HS-color."""
        return self.hue.initialized and self.saturation.initialized

    @property
    def supports_xyy_color(self) -> bool:
        """Return if light supports xyY-color."""
        return self.xyy_color.initialized

    @property
    def supports_tunable_white(self) -> bool:
        """Return if light supports tunable white / relative color temperature."""
        return self.tunable_white.initialized

    @property
    def supports_color_temperature(self) -> bool:
        """Return if light supports absolute color temperature."""
        return self.color_temperature.initialized

    @property
    def state(self) -> bool | None:
        """Return the current switch state of the device."""
        if self.switch.value is not None:
            return self.switch.value
        if any(c.is_on is not None for c in self._iter_individual_colors()):
            return any(c.is_on for c in self._iter_individual_colors())
        return None

    async def set_on(self) -> None:
        """Switch light on."""
        if self.switch.writable:
            await self.switch.on()
            return
        for color in self._iter_individual_colors():
            await color.set_on()

    async def set_off(self) -> None:
        """Switch light off."""
        if self.switch.writable:
            await self.switch.off()
            return
        for color in self._iter_individual_colors():
            await color.set_off()

    @property
    def current_brightness(self) -> int | None:
        """Return current brightness of light between 0..255."""
        return self.brightness.value

    async def set_brightness(self, brightness: int) -> None:
        """Set brightness of light."""
        if not self.supports_brightness:
            logger.warning("Dimming not supported for device %s", self.get_name())
            return
        await self.brightness.set(brightness)

    @property
    def current_color(self) -> tuple[tuple[int, int, int] | None, int | None]:
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
        return cast(Tuple[int, int, int], colors), self.white.brightness.value

    async def set_color(
        self, color: tuple[int, int, int], white: int | None = None
    ) -> None:
        """
        Set color of a light device.

        If also the white value is given and the device supports RGBW,
        set all four values.
        """
        if white is not None:
            if self.supports_rgbw:
                if self.rgbw.initialized:
                    await self.rgbw.set((*color, white))
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
    def current_hs_color(self) -> tuple[float, float] | None:
        """Return current HS-color of the light.

        Hue is scaled 0-360 (265 possible values from KNX)
        Sat is scaled 0-100
        """
        if (hue := self.hue.value) is not None and (
            (saturation := self.saturation.value) is not None
        ):
            return (hue, saturation)
        return None

    async def set_hs_color(self, hs_color: tuple[float, float]) -> None:
        """Set HS-color of the light."""
        if not self.supports_hs_color:
            logger.warning("HS-color not supported for device %s", self.get_name())
            return
        value_sent = False
        if (hue := hs_color[0]) != self.hue.value:
            await self.hue.set(hue)
            value_sent = True
        if (saturation := hs_color[1]) != self.saturation.value:
            await self.saturation.set(saturation)
            value_sent = True
        if not value_sent:
            # at least one value shall be sent to enable turn-on by hs_color
            await self.hue.set(hue)
            await self.saturation.set(saturation)

    async def _xyy_color_from_rv(self) -> None:
        """Update the current xyY-color from RemoteValue (Callback)."""
        new_xyy = self.xyy_color.value
        if new_xyy is None or self._xyy_color_valid is None:
            self._xyy_color_valid = new_xyy
        else:
            new_color, new_brightness = new_xyy
            if new_color is None:
                new_color = self._xyy_color_valid.color
            if new_brightness is None:
                new_brightness = self._xyy_color_valid.brightness
            self._xyy_color_valid = XYYColor(color=new_color, brightness=new_brightness)
        await self.after_update()

    @property
    def current_xyy_color(self) -> XYYColor | None:
        """Return current xyY-color of the light."""
        return self._xyy_color_valid

    async def set_xyy_color(self, xyy: XYYColor) -> None:
        """Set xyY-color of the light."""
        if not self.supports_xyy_color:
            logger.warning("XYY-color not supported for device %s", self.get_name())
            return
        await self.xyy_color.set(xyy)

    @property
    def current_tunable_white(self) -> int | None:
        """Return current relative color temperature of light."""
        return self.tunable_white.value

    async def set_tunable_white(self, tunable_white: int) -> None:
        """Set relative color temperature of light."""
        if not self.supports_tunable_white:
            logger.warning("Tunable white not supported for device %s", self.get_name())
            return
        await self.tunable_white.set(tunable_white)

    @property
    def current_color_temperature(self) -> int | None:
        """Return current absolute color temperature of light."""
        return self.color_temperature.value

    async def set_color_temperature(self, color_temperature: int) -> None:
        """Set absolute color temperature of light."""
        if not self.supports_color_temperature:
            logger.warning(
                "Absolute Color Temperature not supported for device %s",
                self.get_name(),
            )
            return
        await self.color_temperature.set(color_temperature)

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        for remote_value in self._iter_instant_remote_values():
            await remote_value.process(telegram)
        for remote_value in self._iter_debounce_remote_values():
            await remote_value.process(telegram, always_callback=True)

    def __str__(self) -> str:
        """Return object as readable string."""
        str_brightness = (
            ""
            if not self.supports_brightness
            else f" brightness={self.brightness.group_addr_str()}"
        )

        str_color = (
            "" if not self.supports_color else f" color={self.color.group_addr_str()}"
        )

        str_rgbw = (
            "" if not self.supports_rgbw else f" rgbw={self.rgbw.group_addr_str()}"
        )

        str_hue = (
            ""
            if not self.hue.initialized
            else f" brightness={self.hue.group_addr_str()}"
        )

        str_saturation = (
            ""
            if not self.saturation.initialized
            else f" brightness={self.saturation.group_addr_str()}"
        )

        str_xyy_color = (
            ""
            if not self.supports_xyy_color
            else f" xyy_color={self.xyy_color.group_addr_str()}"
        )
        str_tunable_white = (
            ""
            if not self.supports_tunable_white
            else f" tunable_white={self.tunable_white.group_addr_str()}"
        )

        str_color_temperature = (
            ""
            if not self.supports_color_temperature
            else f" color_temperature={self.color_temperature.group_addr_str()}"
        )

        str_red_state = (
            ""
            if not self.red.switch.initialized
            else f" red_state={self.red.switch.group_addr_str()}"
        )
        str_red_brightness = (
            ""
            if not self.red.brightness.initialized
            else f" red_brightness={self.red.brightness.group_addr_str()}"
        )

        str_green_state = (
            ""
            if not self.green.switch.initialized
            else f" green_state={self.green.switch.group_addr_str()}"
        )
        str_green_brightness = (
            ""
            if not self.green.brightness.initialized
            else f" green_brightness={self.green.brightness.group_addr_str()}"
        )

        str_blue_state = (
            ""
            if not self.blue.switch.initialized
            else f" blue_state={self.blue.switch.group_addr_str()}"
        )
        str_blue_brightness = (
            ""
            if not self.blue.brightness.initialized
            else f" blue_brightness={self.blue.brightness.group_addr_str()}"
        )

        str_white_state = (
            ""
            if not self.white.switch.initialized
            else f" white_state={self.white.switch.group_addr_str()}"
        )
        str_white_brightness = (
            ""
            if not self.white.brightness.initialized
            else f" white_brightness={self.white.brightness.group_addr_str()}"
        )

        return (
            f'<Light name="{self.name}" '
            f"switch={self.switch.group_addr_str()}"
            f"{str_brightness}"
            f"{str_color}"
            f"{str_rgbw}"
            f"{str_hue}"
            f"{str_saturation}"
            f"{str_xyy_color}"
            f"{str_tunable_white}"
            f"{str_color_temperature}"
            f"{str_red_state}"
            f"{str_red_brightness}"
            f"{str_green_state}"
            f"{str_green_brightness}"
            f"{str_blue_state}"
            f"{str_blue_brightness}"
            f"{str_white_state}"
            f"{str_white_brightness}"
            " />"
        )
