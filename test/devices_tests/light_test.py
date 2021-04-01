"""Unit test for Light objects."""
from unittest.mock import AsyncMock, patch

import pytest
from xknx import XKNX
from xknx.devices import Light
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


# pylint: disable=no-self-use
@pytest.mark.asyncio
class TestLight:
    """Class for testing Light objects."""

    #
    # TEST SUPPORT DIMMING
    #
    def test_supports_dimm_yes(self):
        """Test supports_dimm attribute with a light with dimmer."""
        xknx = XKNX()
        light = Light(
            xknx,
            "Diningroom.Light_1",
            group_address_switch="1/6/4",
            group_address_brightness="1/6/6",
        )
        assert light.supports_brightness

    def test_supports_dimm_no(self):
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
        """Test sync function / sending group reads to KNX bus. Testing with a Light without dimm functionality."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/3/5",
            group_address_switch_state="1/2/3",
            group_address_brightness_state="1/2/5",
            group_address_color_state="1/2/6",
            group_address_tunable_white_state="1/2/7",
            group_address_color_temperature_state="1/2/8",
            group_address_rgbw_state="1/2/9",
        )
        await light.sync()

        assert xknx.telegrams.qsize() == 6

        telegrams = []
        for _ in range(6):
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
                destination_address=GroupAddress("1/2/9"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/7"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/8"), payload=GroupValueRead()
            ),
        ]

        assert len(telegrams) == 6
        assert telegrams == test_telegrams

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
    # SYNC WITH STATE ADDRESS
    #
    async def test_sync_state_address(self):
        """Test sync function / sending group reads to KNX bus. Testing with a Light with dimm functionality."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_switch_state="1/2/4",
            group_address_brightness="1/2/5",
            group_address_brightness_state="1/2/6",
            group_address_color="1/2/7",
            group_address_color_state="1/2/8",
            group_address_tunable_white="1/2/9",
            group_address_tunable_white_state="1/2/10",
            group_address_color_temperature="1/2/11",
            group_address_color_temperature_state="1/2/12",
            group_address_rgbw="1/2/13",
            group_address_rgbw_state="1/2/14",
        )
        await light.sync()

        assert xknx.telegrams.qsize() == 6

        telegrams = []
        for _ in range(6):
            telegrams.append(xknx.telegrams.get_nowait())

        test_telegrams = [
            Telegram(
                destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/6"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/8"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/14"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/10"), payload=GroupValueRead()
            ),
            Telegram(
                destination_address=GroupAddress("1/2/12"), payload=GroupValueRead()
            ),
        ]

        assert len(telegrams) == 6
        assert telegrams == test_telegrams

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
        # pylint: disable=invalid-name
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
        # pylint: disable=invalid-name
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
        # pylint: disable=invalid-name
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
        # pylint: disable=invalid-name
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
        # pylint: disable=invalid-name
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
        # pylint: disable=invalid-name
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
        # pylint: disable=invalid-name
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
        # pylint: disable=no-self-use
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
        # pylint: disable=invalid-name
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
        # pylint: disable=invalid-name
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
        # pylint: disable=invalid-name
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

    #
    # TEST DO
    #
    async def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_brightness="1/2/5",
            group_address_tunable_white="1/2/9",
            group_address_color_temperature="1/2/11",
        )
        await light.do("on")
        await xknx.devices.process(xknx.telegrams.get_nowait())
        assert light.state
        await light.do("brightness:80")
        await xknx.devices.process(xknx.telegrams.get_nowait())
        assert light.current_brightness == 80
        await light.do("tunable_white:80")
        await xknx.devices.process(xknx.telegrams.get_nowait())
        assert light.current_tunable_white == 80
        await light.do("color_temperature:3750")
        await xknx.devices.process(xknx.telegrams.get_nowait())
        assert light.current_color_temperature == 3750
        await light.do("off")
        await xknx.devices.process(xknx.telegrams.get_nowait())
        assert not light.state

    async def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_brightness="1/2/5",
        )
        with patch("logging.Logger.warning") as mock_warn:
            await light.do("execute")
            assert xknx.telegrams.qsize() == 0
            mock_warn.assert_called_with(
                "Could not understand action %s for device %s", "execute", "TestLight"
            )

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

        assert not light.has_group_address(GroupAddress("1/7/13"))

    def test_unique_id(self):
        """Test unique id functionality."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch="1/2/3",
            group_address_brightness="1/2/5",
            group_address_tunable_white="1/2/9",
            group_address_color_temperature="1/2/11",
        )
        assert light.unique_id == "1/2/3"

    def test_unique_id_colors(self):
        """Test unique id for colors functionality."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="TestLight",
            group_address_switch_green="1/2/3",
            group_address_switch_blue="1/2/4",
            group_address_switch_red="1/2/5",
            group_address_switch_white="1/2/6",
            group_address_brightness="1/2/5",
            group_address_tunable_white="1/2/9",
            group_address_color_temperature="1/2/11",
        )
        assert light.unique_id == "1/2/5_1/2/3_1/2/4_1/2/6"
