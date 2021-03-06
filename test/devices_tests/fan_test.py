"""Unit test for Fan objects."""
import asyncio
import unittest
from unittest.mock import patch

from xknx import XKNX
from xknx.devices import Fan
from xknx.devices.fan import FanSpeedMode
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


class TestFan(unittest.TestCase):
    """Class for testing Fan objects."""

    # pylint: disable=too-many-public-methods

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # SYNC
    #
    def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed_state="1/2/3")
        self.loop.run_until_complete(fan.sync())

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(
                destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
            ),
        )

    def test_sync_step(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        fan = Fan(
            xknx,
            name="TestFan",
            group_address_speed_state="1/2/3",
            mode=FanSpeedMode.Step,
        )
        self.loop.run_until_complete(fan.sync())

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(
                destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
            ),
        )

    #
    # SYNC WITH STATE ADDRESS
    #
    def test_sync_state_address(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        fan = Fan(
            xknx,
            name="TestFan",
            group_address_speed="1/2/3",
            group_address_speed_state="1/2/4",
        )
        self.loop.run_until_complete(fan.sync())

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(
                destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
            ),
        )

    #
    #
    # TEST SET SPEED
    #
    def test_set_speed(self):
        """Test setting the speed of a Fan."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")
        self.loop.run_until_complete(fan.set_speed(55))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        # 140 is 55% as byte (0...255)
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray(140)),
            ),
        )

    #
    #
    # TEST SET SPEED STEP
    #
    def test_set_speed_step(self):
        """Test setting the speed of a Fan."""
        xknx = XKNX()
        fan = Fan(
            xknx, name="TestFan", group_address_speed="1/2/3", mode=FanSpeedMode.Step
        )
        self.loop.run_until_complete(fan.set_speed(2))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray(2)),
            ),
        )

    #
    # TEST PROCESS
    #
    def test_process_speed(self):
        """Test process / reading telegrams from telegram queue. Test if speed is processed."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")
        self.assertEqual(fan.current_speed, None)

        # 140 is 55% as byte (0...255)
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(140)),
        )
        self.loop.run_until_complete(fan.process(telegram))
        self.assertEqual(fan.current_speed, 55)

    def test_process_speed_wrong_payload(self):  # pylint: disable=invalid-name
        """Test process wrong telegrams. (wrong payload type)."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        with self.assertRaises(CouldNotParseTelegram):
            self.loop.run_until_complete(fan.process(telegram))

    def test_process_fan_payload_invalid_length(self):
        """Test process wrong telegrams. (wrong payload length)."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((23, 24))),
        )
        with self.assertRaises(CouldNotParseTelegram):
            self.loop.run_until_complete(fan.process(telegram))

    #
    # TEST PROCESS STEP MODE
    #
    def test_process_speed_step(self):
        """Test process / reading telegrams from telegram queue. Test if speed is processed."""
        xknx = XKNX()
        fan = Fan(
            xknx, name="TestFan", group_address_speed="1/2/3", mode=FanSpeedMode.Step
        )
        self.assertEqual(fan.current_speed, None)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(2)),
        )
        self.loop.run_until_complete(fan.process(telegram))
        self.assertEqual(fan.current_speed, 2)

    #
    # TEST DO
    #
    def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")
        self.loop.run_until_complete(fan.do("speed:50"))
        self.loop.run_until_complete(xknx.devices.process(xknx.telegrams.get_nowait()))
        self.assertEqual(fan.current_speed, 50)
        self.loop.run_until_complete(fan.do("speed:25"))
        self.loop.run_until_complete(xknx.devices.process(xknx.telegrams.get_nowait()))
        self.assertEqual(fan.current_speed, 25)

    def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")
        with patch("logging.Logger.warning") as mock_warn:
            self.loop.run_until_complete(fan.do("execute"))
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with(
                "Could not understand action %s for device %s", "execute", "TestFan"
            )

    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        fan = Fan(
            xknx,
            "TestFan",
            group_address_speed="1/7/1",
            group_address_speed_state="1/7/2",
        )
        self.assertTrue(fan.has_group_address(GroupAddress("1/7/1")))
        self.assertTrue(fan.has_group_address(GroupAddress("1/7/2")))
        self.assertFalse(fan.has_group_address(GroupAddress("1/7/3")))
