"""Unit test for Light objects."""
from unittest.mock import AsyncMock, patch

import pytest
from xknx import XKNX
from xknx.devices import Light
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


@pytest.mark.asyncio
class TestLight:
    """Class for testing Light objects."""

    #
    # TEST SUPPORT DIMMING
    #
    def test_supports_dimm_true(self):
        """Test supports_dimm attribute with a light with dimmer."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch="1/6/4",
            group_address_brightness="1/6/6",
        )
        assert light.supports_brightness

    def test_supports_dimm_false(self):
        """Test supports_dimm attribute with a Light without dimmer."""
        xknx = XKNX()
        light = Light(xknx, "Diningroom.Light_1", group_address_switch="1/6/4")
        assert not light.supports_brightness

    #
    # TEST SUPPORT COLOR
    #
    def test_supports_color_true(self):
        """Test supports_color true."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch="1/6/4",
            group_address_color="1/6/5",
        )
        assert light.supports_color

    def test_supports_color_false(self):
        """Test supports_color false."""
        xknx = XKNX()
        light = Light(xknx, "Diningroom.Light_1", group_address_switch="1/6/4")
        assert not light.supports_color

    def test_supports_individual_color_true(self):
        """Test supports_color true."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
        )
        assert light.supports_color

    def test_supports_individual_color_only_brightness_true(self):
        """Test supports_color true."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Individual colors only brightness",
            group_address_brightness_red="1/1/3",
            group_address_brightness_green="1/1/7",
            group_address_brightness_blue="1/1/11",
        )
        assert light.supports_color

    def test_supports_individual_color_false(self):
        """Test supports_color false."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
        )
        assert not light.supports_color

    #
    # TEST SUPPORT COLOR RGBW
    #
    def test_supports_rgbw_true(self):
        """Test supports_rgbw true."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch="1/6/4",
            group_address_rgbw="1/6/5",
            group_address_color="1/6/6",
        )
        assert light.supports_rgbw

    def test_supports_rgbw_false(self):
        """Test supports_color false."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch="1/6/4",
            group_address_color="1/6/6",
        )
        assert not light.supports_rgbw

    def test_supports_individual_rgbw_true(self):
        """Test supports_rgbw true."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_white_state="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_white_state="1/1/16",
        )
        assert light.supports_rgbw

    def test_supports_individual_color_only_brightness_rgbw_true(self):
        """Test supports_color true."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Individual colors only brightness",
            group_address_brightness_red="1/1/3",
            group_address_brightness_green="1/1/7",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_white="1/1/12",
        )
        assert light.supports_rgbw

    def test_supports_individual_rgbw_false(self):
        """Test supports_color false."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
        )
        assert not light.supports_rgbw

    def test_supports_hs_color_true(self):
        """Test supports_hs_color true."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Hue and saturation",
            group_address_switch="1/6/4",
            group_address_hue="1/6/5",
            group_address_saturation="1/6/6",
        )
        assert light.supports_hs_color

    def test_supports_hs_color_false(self):
        """Test supports_hs_color false."""
        xknx = XKNX()
        light_hue = Light(
            xknx,
            "Light hue only",
            group_address_switch="1/6/4",
            group_address_hue="1/6/5",
        )
        assert not light_hue.supports_hs_color

        light_saturation = Light(
            xknx,
            "Light saturation only",
            group_address_switch="1/6/4",
            group_address_saturation="1/6/5",
        )
        assert not light_saturation.supports_hs_color

    def test_supports_xyy_color_true(self):
        """Test supports_xyy_color true."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch="1/6/4",
            group_address_xyy_color="1/6/5",
        )
        assert light.supports_xyy_color

    def test_supports_xyy_color_false(self):
        """Test supports_xyy_color false."""
        xknx = XKNX()
        light = Light(xknx, "Diningroom.Light_1", group_address_switch="1/6/4")
        assert not light.supports_xyy_color

    #
    # TEST SUPPORT TUNABLE WHITE
    #
    def test_supports_tw_yes(self):
        """Test supports_tw attribute with a light with tunable white function."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch="1/6/4",
            group_address_tunable_white="1/6/6",
        )
        assert light.supports_tunable_white

    def test_supports_tw_no(self):
        """Test supports_tw attribute with a Light without tunable white function."""
        xknx = XKNX()
        light = Light(xknx, "Diningroom.Light_1", group_address_switch="1/6/4")
        assert not light.supports_tunable_white

    #
    # TEST SUPPORT COLOR TEMPERATURE
    #
    def test_supports_color_temp_true(self):
        """Test supports_color_temp attribute with a light with color temperature function."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch="1/6/4",
            group_address_color_temperature="1/6/6",
        )
        assert light.supports_color_temperature

    def test_supports_color_temp_false(self):
        """Test supports_color_temp attribute with a Light without color temperature function."""
        xknx = XKNX()
        light = Light(xknx, "Diningroom.Light_1", group_address_switch="1/6/4")
        assert not light.supports_color_temperature

    #
    # SYNC
    #
    async def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/3/5",
            group_address_switch_state="1/2/3",
            group_address_brightness_state="1/2/5",
            group_address_color_state="1/2/6",
            group_address_xyy_color_state="1/2/4",
            group_address_tunable_white_state="1/2/7",
            group_address_color_temperature_state="1/2/8",
            group_address_rgbw_state="1/2/9",
        )
        expected_telegrams = 7

        await light.sync()
        assert xknx.telegrams.qsize() == expected_telegrams

        telegrams = []
        for _ in range(expected_telegrams):
            telegrams.append(xknx.telegrams.get_nowait())

        test_telegrams = [
            Telegram(
                destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/5"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/6"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/9"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/7"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/8"), payload=GroupValueRead()
            ),
        ]
        assert len(set(telegrams)) == expected_telegrams
        assert set(telegrams) == set(test_telegrams)

    async def test_sync_individual_color(self):
        """Test sync function / sending group reads to KNX bus. Testing with a Light without dimm functionality."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_white_state="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_white_state="1/1/16",
        )
        await light.sync()

        assert xknx.telegrams.qsize() == 8

        telegrams = [xknx.telegrams.get_nowait() for _ in range(8)]

        test_telegrams = [
            Telegram(
                destination_address=GroupAddress("1/1/2"),
                payload=GroupValueRead(),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/4"),
                payload=GroupValueRead(),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/6"),
                payload=GroupValueRead(),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/8"),
                payload=GroupValueRead(),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/10"),
                payload=GroupValueRead(),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/12"),
                payload=GroupValueRead(),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/14"),
                payload=GroupValueRead(),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/16"),
                payload=GroupValueRead(),
            ),
        ]
        assert len(set(telegrams)) == 8
        assert set(telegrams) == set(test_telegrams)

    #
    # TEST SET ON
    #
    async def test_set_on(self):
        """Test switching on a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_brightness="1/2/5",
        )
        await light.set_on()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

    async def test_set_on_individual_color(self):
        """Test switching on a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_white_state="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_white_state="1/1/16",
        )
        assert light.state is None
        for color in light._iter_individual_colors():
            assert color.is_on is None

        await light.set_on()
        assert xknx.telegrams.qsize() == 4

        telegrams = [xknx.telegrams.get_nowait() for _ in range(4)]

        test_telegrams = [
            Telegram(
                destination_address=GroupAddress("1/1/1"),
                payload=GroupValueWrite(DPTBinary(True)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/5"),
                payload=GroupValueWrite(DPTBinary(True)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/9"),
                payload=GroupValueWrite(DPTBinary(True)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/13"),
                payload=GroupValueWrite(DPTBinary(True)),
            ),
        ]
        assert len(set(telegrams)) == 4
        assert set(telegrams) == set(test_telegrams)

        for telegram in telegrams:
            await light.process(telegram)

        assert light.state is True
        for color in light._iter_individual_colors():
            assert color.is_on is True

    async def test_set_on_individual_color_only_brightness(self):
        """Test switching on a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Individual colors only brightness",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
            group_address_brightness_white="1/1/15",
            group_address_brightness_white_state="1/1/16",
        )
        assert light.state is None
        for color in light._iter_individual_colors():
            assert color.is_on is None

        await light.set_on()
        assert xknx.telegrams.qsize() == 4

        telegrams = [xknx.telegrams.get_nowait() for _ in range(4)]

        test_telegrams = [
            Telegram(
                destination_address=GroupAddress("1/1/3"),
                payload=GroupValueWrite(DPTArray((0xFF,))),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/7"),
                payload=GroupValueWrite(DPTArray((0xFF,))),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/11"),
                payload=GroupValueWrite(DPTArray((0xFF,))),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/15"),
                payload=GroupValueWrite(DPTArray((0xFF,))),
            ),
        ]
        assert len(set(telegrams)) == 4
        assert set(telegrams) == set(test_telegrams)

        for telegram in telegrams:
            await light.process(telegram)

        assert light.state is True
        for color in light._iter_individual_colors():
            assert color.is_on is True

    #
    # TEST SET OFF
    #
    async def test_set_off(self):
        """Test switching off a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_brightness="1/2/5",
        )
        await light.set_off()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

        await light.process(telegram)
        assert light.state is False

    async def test_set_off_individual_color(self):
        """Test switching off a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_white_state="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_white_state="1/1/16",
        )
        await light.set_off()
        assert xknx.telegrams.qsize() == 4

        telegrams = [xknx.telegrams.get_nowait() for _ in range(4)]

        test_telegrams = [
            Telegram(
                destination_address=GroupAddress("1/1/1"),
                payload=GroupValueWrite(DPTBinary(False)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/5"),
                payload=GroupValueWrite(DPTBinary(False)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/9"),
                payload=GroupValueWrite(DPTBinary(False)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/13"),
                payload=GroupValueWrite(DPTBinary(False)),
            ),
        ]
        assert len(set(telegrams)) == 4
        assert set(telegrams) == set(test_telegrams)

        for telegram in telegrams:
            await light.process(telegram)
        assert light.state is False
        for color in light._iter_individual_colors():
            assert color.is_on is False

    async def test_set_off_individual_color_only_brightness(self):
        """Test switching off a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
            group_address_brightness_white="1/1/15",
            group_address_brightness_white_state="1/1/16",
        )
        await light.set_off()
        assert xknx.telegrams.qsize() == 4

        telegrams = [xknx.telegrams.get_nowait() for _ in range(4)]

        test_telegrams = [
            Telegram(
                destination_address=GroupAddress("1/1/3"),
                payload=GroupValueWrite(DPTArray((0,))),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/7"),
                payload=GroupValueWrite(DPTArray((0,))),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/11"),
                payload=GroupValueWrite(DPTArray((0,))),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/15"),
                payload=GroupValueWrite(DPTArray((0,))),
            ),
        ]
        assert len(set(telegrams)) == 4
        assert set(telegrams) == set(test_telegrams)

        for telegram in telegrams:
            await light.process(telegram)
        assert light.state is False
        for color in light._iter_individual_colors():
            assert color.is_on is False

    #
    # TEST SET BRIGHTNESS
    #
    async def test_set_brightness(self):
        """Test setting the brightness of a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_brightness="1/2/5",
        )
        await light.set_brightness(23)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray(23)),
        )

    async def test_set_brightness_not_dimmable(self):
        """Test setting the brightness of a non dimmable Light."""
        xknx = XKNX()
        light = Light(xknx, name="TestLight", group_address_switch="1/2/3")
        with patch("logging.Logger.warning") as mock_warn:
            await light.set_brightness(23)
            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "Dimming not supported for device %s", "TestLight"
            )

    #
    # TEST SET COLOR
    #
    async def test_set_color(self):
        """Test setting the color of a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_color="1/2/5",
        )
        await light.set_color((23, 24, 25))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray((23, 24, 25))),
        )
        await xknx.devices.process(telegram)
        assert light.current_color == ((23, 24, 25), None)

    async def test_set_color_not_possible(self):
        """Test setting the color of a non light without color."""
        xknx = XKNX()
        light = Light(xknx, name="TestLight", group_address_switch="1/2/3")
        with patch("logging.Logger.warning") as mock_warn:
            await light.set_color((23, 24, 25))
            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "Colors not supported for device %s", "TestLight"
            )

    async def test_set_individual_color(self):
        """Test setting the color of a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
        )
        await light.set_color([23, 24, 25])
        assert xknx.telegrams.qsize() == 3
        telegrams = [xknx.telegrams.get_nowait() for _ in range(3)]

        test_telegrams = [
            Telegram(
                destination_address=GroupAddress("1/1/3"),
                payload=GroupValueWrite(DPTArray(23)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/7"),
                payload=GroupValueWrite(DPTArray(24)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/11"),
                payload=GroupValueWrite(DPTArray(25)),
            ),
        ]

        assert len(set(telegrams)) == 3
        assert set(telegrams) == set(test_telegrams)

        await xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/1/4"),
                payload=GroupValueWrite(DPTArray(23)),
            )
        )
        await xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/1/8"),
                payload=GroupValueWrite(DPTArray(24)),
            )
        )
        await xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/1/12"),
                payload=GroupValueWrite(DPTArray(25)),
            )
        )
        assert light.current_color == ((23, 24, 25), None)

    async def test_set_individual_color_not_possible(self):
        """Test setting the color of a non light without color."""
        xknx = XKNX()
        light = Light(
            xknx,
            "TestLight",
            group_address_switch_red="1/1/1",
        )
        with patch("logging.Logger.warning") as mock_warn:
            await light.set_color((23, 24, 25))
            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "Colors not supported for device %s", "TestLight"
            )

    #
    # TEST SET COLOR AS RGBW
    #
    async def test_set_color_rgbw(self):
        """Test setting RGBW value of a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_color="1/2/4",
            group_address_rgbw="1/2/5",
        )
        await light.set_color((23, 24, 25), 26)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray((23, 24, 25, 26, 0, 15))),
        )
        await xknx.devices.process(telegram)
        assert light.current_color == ((23, 24, 25), 26)

    async def test_set_color_rgbw_not_possible(self):
        """Test setting RGBW value of a non light without color."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_color="1/2/4",
        )
        with patch("logging.Logger.warning") as mock_warn:
            await light.set_color((23, 24, 25), 26)

            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "RGBW not supported for device %s", "TestLight"
            )

    async def test_set_individual_color_rgbw(self):
        """Test setting RGBW value of a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_white_state="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_white_state="1/1/16",
        )
        await light.set_color([23, 24, 25], white=26)
        assert xknx.telegrams.qsize() == 4
        telegrams = [xknx.telegrams.get_nowait() for _ in range(4)]

        test_telegrams = [
            Telegram(
                destination_address=GroupAddress("1/1/3"),
                payload=GroupValueWrite(DPTArray(23)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/7"),
                payload=GroupValueWrite(DPTArray(24)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/11"),
                payload=GroupValueWrite(DPTArray(25)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/15"),
                payload=GroupValueWrite(DPTArray(26)),
            ),
        ]

        assert len(set(telegrams)) == 4
        assert set(telegrams) == set(test_telegrams)

        await xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/1/4"),
                payload=GroupValueWrite(DPTArray(23)),
            )
        )
        await xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/1/8"),
                payload=GroupValueWrite(DPTArray(24)),
            )
        )
        await xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/1/12"),
                payload=GroupValueWrite(DPTArray(25)),
            )
        )
        await xknx.devices.process(
            Telegram(
                destination_address=GroupAddress("1/1/16"),
                payload=GroupValueWrite(DPTArray(26)),
            )
        )
        assert light.current_color == ((23, 24, 25), 26)

    async def test_set_individual_color_rgbw_not_possible(self):
        """Test setting RGBW value of a non light without color."""
        xknx = XKNX()
        light = Light(
            xknx,
            "TestLight",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
        )
        with patch("logging.Logger.warning") as mock_warn:
            await light.set_color((23, 24, 25), 26)

            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "RGBW not supported for device %s", "TestLight"
            )

    #
    # TEST SET COLOR AS HS
    #
    async def test_set_hs_color(self):
        """Test setting HS value of a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_hue="1/2/4",
            group_address_saturation="1/2/5",
        )
        await light.set_hs_color((359, 99))
        assert xknx.telegrams.qsize() == 2

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueWrite(DPTArray((0xFE,))),
        )
        await xknx.devices.process(telegram)

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray((0xFC,))),
        )
        await xknx.devices.process(telegram)

        assert light.current_hs_color == (359, 99)

        # change only one
        await light.set_hs_color((18, 99))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueWrite(DPTArray((0x0D,))),
        )
        await xknx.devices.process(telegram)

        await light.set_hs_color((18, 3))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray((0x08,))),
        )
        await xknx.devices.process(telegram)

        # call set_hs_color with current color shall trigger both values
        await light.set_hs_color((18, 3))
        assert xknx.telegrams.qsize() == 2

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueWrite(DPTArray((0x0D,))),
        )
        await xknx.devices.process(telegram)

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray((0x08,))),
        )
        await xknx.devices.process(telegram)

    async def test_set_hs_color_not_possible(self):
        """Test setting HS value of a light not supporting it."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_color="1/2/4",
        )
        with patch("logging.Logger.warning") as mock_warn:
            await light.set_hs_color((22, 25))

            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "HS-color not supported for device %s", "TestLight"
            )

    #
    # TEST SET COLOR AS XYY
    #
    async def test_set_xyy_color(self):
        """Test setting XYY value of a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_xyy_color="1/2/4",
        )
        await light.set_xyy_color(((0.52, 0.31), 25))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueWrite(DPTArray((0x85, 0x1E, 0x4F, 0x5C, 0x19, 0x03))),
        )
        await xknx.devices.process(telegram)
        assert light.current_xyy_color == ((0.52, 0.31), 25)

    async def test_set_xyy_color_not_possible(self):
        """Test setting XYY value of a light not supporting it."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_color="1/2/4",
        )
        with patch("logging.Logger.warning") as mock_warn:
            await light.set_xyy_color(((0.5, 0.3), 25))

            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "XYY-color not supported for device %s", "TestLight"
            )

    #
    # TEST SET TUNABLE WHITE
    #
    async def test_set_tw(self):
        """Test setting the tunable white value of a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_tunable_white="1/2/5",
        )
        await light.set_tunable_white(23)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray(23)),
        )

    async def test_set_tw_unsupported(self):
        """Test setting the tunable white value of a non tw Light."""
        xknx = XKNX()
        light = Light(xknx, name="TestLight", group_address_switch="1/2/3")
        with patch("logging.Logger.warning") as mock_warn:
            await light.set_tunable_white(23)
            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "Tunable white not supported for device %s", "TestLight"
            )

    #
    # TEST SET COLOR TEMPERATURE
    #
    async def test_set_color_temp(self):
        """Test setting the color temperature value of a Light."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_color_temperature="1/2/5",
        )
        await light.set_color_temperature(4000)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(
                DPTArray(
                    (
                        0x0F,
                        0xA0,
                    )
                )
            ),
        )

    async def test_set_color_temp_unsupported(self):
        """Test setting the color temperature value of an unsupported Light."""
        xknx = XKNX()
        light = Light(xknx, name="TestLight", group_address_switch="1/2/3")
        with patch("logging.Logger.warning") as mock_warn:
            await light.set_color_temperature(4000)
            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "Absolute Color Temperature not supported for device %s", "TestLight"
            )

    #
    # TEST PROCESS
    #
    async def test_process_switch(self):
        """Test process / reading telegrams from telegram queue. Test if switch position is processed correctly."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_brightness="1/2/5",
        )
        assert light.state is None

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await light.process(telegram)
        assert light.state is True

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        await light.process(telegram)
        assert light.state is False

    async def test_process_color_switch(self):
        """Test process / reading telegrams from telegram queue. Test if switch position is processed correctly."""
        xknx = XKNX()
        light = Light(
            xknx,
            "TestLight",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
        )
        assert light.state is None

        telegram = Telegram(
            destination_address=GroupAddress("1/1/2"),
            payload=GroupValueWrite(DPTBinary(True)),
        )
        await light.process(telegram)
        assert light.state is True

        telegram = Telegram(
            destination_address=GroupAddress("1/1/2"),
            payload=GroupValueWrite(DPTBinary(False)),
        )
        await light.process(telegram)
        assert light.state is False

    async def test_process_switch_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback is called."""

        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_brightness="1/2/5",
        )
        after_update_callback = AsyncMock()
        light.register_device_updated_cb(after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await light.process(telegram)
        after_update_callback.assert_called_with(light)

    async def test_process_dimm(self):
        """Test process / reading telegrams from telegram queue. Test if brightness is processed."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_brightness="1/2/5",
        )
        assert light.current_brightness is None

        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray(23)),
        )
        await light.process(telegram)
        assert light.current_brightness == 23

    async def test_process_dimm_wrong_payload(self):
        """Test process wrong telegrams. (wrong payload type)."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_brightness="1/2/5",
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        with pytest.raises(CouldNotParseTelegram):
            await light.process(telegram)

    async def test_process_dimm_payload_invalid_length(self):
        """Test process wrong telegrams. (wrong payload length)."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_brightness="1/2/5",
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray((23, 24))),
        )
        with pytest.raises(CouldNotParseTelegram):
            await light.process(telegram)

    async def test_process_color(self):
        """Test process / reading telegrams from telegram queue. Test if color is processed."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_color="1/2/5",
        )
        assert light.current_color == (None, None)
        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray((23, 24, 25))),
        )
        await light.process(telegram)
        assert light.current_color == ((23, 24, 25), None)

    async def test_process_individual_color(self):
        """Test process / reading telegrams from telegram queue. Test if color is processed."""
        xknx = XKNX()
        light = Light(
            xknx,
            "TestLight",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
        )
        assert light.current_color == (None, None)

        telegrams = [
            Telegram(
                destination_address=GroupAddress("1/1/4"),
                payload=GroupValueWrite(DPTArray(42)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/8"),
                payload=GroupValueWrite(DPTArray(43)),
            ),
            Telegram(
                destination_address=GroupAddress("1/1/12"),
                payload=GroupValueWrite(DPTArray(44)),
            ),
        ]

        for telegram in telegrams:
            await light.process(telegram)
        assert light.current_color == ((42, 43, 44), None)

    async def test_process_color_rgbw(self):
        """Test process / reading telegrams from telegram queue. Test if RGBW is processed."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_color="1/2/4",
            group_address_rgbw="1/2/5",
        )
        assert light.current_color == (None, None)
        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray((23, 24, 25, 26, 0, 15))),
        )
        await light.process(telegram)
        assert light.current_color == ((23, 24, 25), 26)

    async def test_process_individual_color_rgbw(self):
        """Test process / reading telegrams from telegram queue. Test if RGBW is processed."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_white_state="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_white_state="1/1/16",
        )
        assert light.current_color == (None, None)
        telegram = Telegram(
            destination_address=GroupAddress("1/1/16"),
            payload=GroupValueWrite(DPTArray(42)),
        )
        await light.process(telegram)
        assert light.current_color == (None, 42)

    async def test_process_xyy_color(self):
        """Test process / reading telegrams from telegram queue. Test if color is processed."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_xyy_color="1/2/5",
        )
        assert light.current_xyy_color is None
        # initial with invalid brightness
        await light.process(
            Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTArray((0x2E, 0x14, 0x40, 0x00, 0x55, 0x02))),
            )
        )
        assert light.current_xyy_color == ((0.18, 0.25), None)
        # add valid brightness
        await light.process(
            Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTArray((0x2E, 0x14, 0x40, 0x00, 0x55, 0x03))),
            )
        )
        assert light.current_xyy_color == ((0.18, 0.25), 85)
        # invalid color
        await light.process(
            Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTArray((0xD1, 0xEB, 0xB0, 0xA3, 0xA5, 0x01))),
            )
        )
        assert light.current_xyy_color == ((0.18, 0.25), 165)
        # both valid
        await light.process(
            Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTArray((0xD1, 0xEB, 0xB0, 0xA3, 0xA5, 0x03))),
            )
        )
        assert light.current_xyy_color == ((0.82, 0.69), 165)
        # invalid brightness
        await light.process(
            Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTArray((0x2E, 0x14, 0x40, 0x00, 0x00, 0x02))),
            )
        )
        assert light.current_xyy_color == ((0.18, 0.25), 165)

    async def test_process_tunable_white(self):
        """Test process / reading telegrams from telegram queue. Test if tunable white is processed."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_tunable_white="1/2/5",
        )
        assert light.current_tunable_white is None

        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray(23)),
        )
        await light.process(telegram)
        assert light.current_tunable_white == 23

    async def test_process_tunable_white_wrong_payload(self):
        """Test process wrong telegrams. (wrong payload type)."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_tunable_white="1/2/5",
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        with pytest.raises(CouldNotParseTelegram):
            await light.process(telegram)

    async def test_process_tunable_white_payload_invalid_length(self):
        """Test process wrong telegrams. (wrong payload length)."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_tunable_white="1/2/5",
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray((23, 24))),
        )
        with pytest.raises(CouldNotParseTelegram):
            await light.process(telegram)

    async def test_process_color_temperature(self):
        """Test process / reading telegrams from telegram queue. Test if color temperature is processed."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_color_temperature="1/2/5",
        )
        assert light.current_color_temperature is None

        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(
                DPTArray(
                    (
                        0x0F,
                        0xA0,
                    )
                )
            ),
        )
        await light.process(telegram)
        assert light.current_color_temperature == 4000

    async def test_process_color_temperature_wrong_payload(self):
        """Test process wrong telegrams. (wrong payload type)."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_color_temperature="1/2/5",
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        with pytest.raises(CouldNotParseTelegram):
            await light.process(telegram)

    async def test_process_color_temperature_payload_invalid_length(self):
        """Test process wrong telegrams. (wrong payload length)."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_color_temperature="1/2/5",
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTArray(23)),
        )
        with pytest.raises(CouldNotParseTelegram):
            await light.process(telegram)

    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Office.Light_1",
            group_address_switch="1/7/1",
            group_address_switch_state="1/7/2",
            group_address_brightness="1/7/3",
            group_address_brightness_state="1/7/4",
            group_address_color="1/7/5",
            group_address_color_state="1/7/6",
            group_address_tunable_white="1/7/7",
            group_address_tunable_white_state="1/7/8",
            group_address_color_temperature="1/7/9",
            group_address_color_temperature_state="1/7/10",
            group_address_rgbw="1/7/11",
            group_address_rgbw_state="1/7/12",
            group_address_hue="1/7/81",
            group_address_hue_state="1/7/82",
            group_address_saturation="1/7/83",
            group_address_saturation_state="1/7/84",
            group_address_xyy_color="1/7/13",
            group_address_xyy_color_state="1/7/14",
            group_address_switch_red="1/1/1",
            group_address_switch_red_state="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_red_state="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_green_state="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_green_state="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_blue_state="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_blue_state="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_white_state="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_white_state="1/1/16",
        )
        assert light.has_group_address(GroupAddress("1/7/1"))
        assert light.has_group_address(GroupAddress("1/7/2"))
        assert light.has_group_address(GroupAddress("1/7/3"))
        assert light.has_group_address(GroupAddress("1/7/4"))
        assert light.has_group_address(GroupAddress("1/7/5"))
        assert light.has_group_address(GroupAddress("1/7/6"))
        assert light.has_group_address(GroupAddress("1/7/7"))
        assert light.has_group_address(GroupAddress("1/7/8"))
        assert light.has_group_address(GroupAddress("1/7/9"))
        assert light.has_group_address(GroupAddress("1/7/10"))
        assert light.has_group_address(GroupAddress("1/7/11"))
        assert light.has_group_address(GroupAddress("1/7/12"))
        # hue
        assert light.has_group_address(GroupAddress("1/7/81"))
        assert light.has_group_address(GroupAddress("1/7/82"))
        # saturation
        assert light.has_group_address(GroupAddress("1/7/83"))
        assert light.has_group_address(GroupAddress("1/7/84"))
        # xyy
        assert light.has_group_address(GroupAddress("1/7/13"))
        assert light.has_group_address(GroupAddress("1/7/14"))
        # individual
        assert light.has_group_address(GroupAddress("1/1/1"))
        assert light.has_group_address(GroupAddress("1/1/2"))
        assert light.has_group_address(GroupAddress("1/1/3"))
        assert light.has_group_address(GroupAddress("1/1/4"))
        assert light.has_group_address(GroupAddress("1/1/5"))
        assert light.has_group_address(GroupAddress("1/1/6"))
        assert light.has_group_address(GroupAddress("1/1/7"))
        assert light.has_group_address(GroupAddress("1/1/8"))
        assert light.has_group_address(GroupAddress("1/1/9"))
        assert light.has_group_address(GroupAddress("1/1/10"))
        assert light.has_group_address(GroupAddress("1/1/11"))
        assert light.has_group_address(GroupAddress("1/1/12"))
        assert light.has_group_address(GroupAddress("1/1/13"))
        assert light.has_group_address(GroupAddress("1/1/14"))
        assert light.has_group_address(GroupAddress("1/1/15"))
        assert light.has_group_address(GroupAddress("1/1/16"))

        assert not light.has_group_address(GroupAddress("1/7/15"))
