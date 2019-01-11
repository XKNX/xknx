"""Unit test for RemoteValueDpt3 objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.knx import DPTArray, DPTBinary, Telegram, GroupAddress
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.devices import RemoteValueDpt3, RemoteValueStartStopDimming, RemoteValueStartStopBlinds


class TestRemoteValueDpt3(unittest.TestCase):
    """Test class for RemoteValueDpt3 objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt3(xknx)
        self.assertEqual(remote_value.to_knx(1), DPTBinary(0xf))
        self.assertEqual(remote_value.to_knx(3), DPTBinary(0xe))
        self.assertEqual(remote_value.to_knx(6), DPTBinary(0xd))
        self.assertEqual(remote_value.to_knx(12), DPTBinary(0xc))
        self.assertEqual(remote_value.to_knx(25), DPTBinary(0xb))
        self.assertEqual(remote_value.to_knx(50), DPTBinary(0xa))
        self.assertEqual(remote_value.to_knx(100), DPTBinary(0x9))
        self.assertEqual(remote_value.to_knx(-1), DPTBinary(0x7))
        self.assertEqual(remote_value.to_knx(-3), DPTBinary(0x6))
        self.assertEqual(remote_value.to_knx(-6), DPTBinary(0x5))
        self.assertEqual(remote_value.to_knx(-12), DPTBinary(0x4))
        self.assertEqual(remote_value.to_knx(-25), DPTBinary(0x3))
        self.assertEqual(remote_value.to_knx(-50), DPTBinary(0x2))
        self.assertEqual(remote_value.to_knx(-100), DPTBinary(0x1))
        self.assertEqual(remote_value.to_knx(0), DPTBinary(0x0))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt3(xknx)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xf)), 1)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xe)), 3)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xd)), 6)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xc)), 12)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xb)), 25)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xa)), 50)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x9)), 100)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x8)), 0)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x7)), -1)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x6)), -3)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x5)), -6)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x4)), -12)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x3)), -25)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x2)), -50)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x1)), -100)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x0)), 0)

    def test_to_knx_invert(self):
        """Test to_knx function with inverted operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt3(xknx, invert=True)
        self.assertEqual(remote_value.to_knx(-1), DPTBinary(0xf))
        self.assertEqual(remote_value.to_knx(-3), DPTBinary(0xe))
        self.assertEqual(remote_value.to_knx(-6), DPTBinary(0xd))
        self.assertEqual(remote_value.to_knx(-12), DPTBinary(0xc))
        self.assertEqual(remote_value.to_knx(-25), DPTBinary(0xb))
        self.assertEqual(remote_value.to_knx(-50), DPTBinary(0xa))
        self.assertEqual(remote_value.to_knx(-100), DPTBinary(0x9))
        self.assertEqual(remote_value.to_knx(1), DPTBinary(0x7))
        self.assertEqual(remote_value.to_knx(3), DPTBinary(0x6))
        self.assertEqual(remote_value.to_knx(6), DPTBinary(0x5))
        self.assertEqual(remote_value.to_knx(12), DPTBinary(0x4))
        self.assertEqual(remote_value.to_knx(25), DPTBinary(0x3))
        self.assertEqual(remote_value.to_knx(50), DPTBinary(0x2))
        self.assertEqual(remote_value.to_knx(100), DPTBinary(0x1))
        self.assertEqual(remote_value.to_knx(0), DPTBinary(0x0))

    def test_from_knx_invert(self):
        """Test from_knx function with inverted operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt3(xknx, invert=True)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xf)), -1)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xe)), -3)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xd)), -6)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xc)), -12)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xb)), -25)
        self.assertEqual(remote_value.from_knx(DPTBinary(0xa)), -50)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x9)), -100)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x8)), 0)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x7)), 1)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x6)), 3)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x5)), 6)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x4)), 12)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x3)), 25)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x2)), 50)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x1)), 100)
        self.assertEqual(remote_value.from_knx(DPTBinary(0x0)), 0)

    def test_set(self):
        """Test setting value."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt3(
            xknx,
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(remote_value.set(25)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(0xb)))

    def test_process(self):
        """Test process telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt3(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTBinary(0xb))
        self.assertEqual(remote_value.value, None)
        self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        self.assertEqual(remote_value.value, 25)

    def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt3(
            xknx,
            group_address=GroupAddress("1/2/3"))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray((0x01)))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTBinary(0x10))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
            # pylint: disable=pointless-statement
            remote_value.value


class TestRemoteValueStartStopDimming(unittest.TestCase):
    """Test class for RemoteValueStartStopDimming objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_to_knx_startstop(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopDimming(xknx)
        self.assertEqual(remote_value.to_knx(RemoteValueStartStopDimming.Direction.INCREASE),
                         DPTBinary(9))
        self.assertEqual(remote_value.to_knx(RemoteValueStartStopDimming.Direction.DECREASE),
                         DPTBinary(1))

    def test_from_knx_startstop(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopDimming(xknx)
        self.assertEqual(remote_value.from_knx(DPTBinary(9)),
                         RemoteValueStartStopDimming.Direction.INCREASE)
        self.assertEqual(remote_value.from_knx(DPTBinary(1)),
                         RemoteValueStartStopDimming.Direction.DECREASE)

    def test_to_knx_startstop_invert(self):
        """Test to_knx function with inverted operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopDimming(xknx, invert=True)
        self.assertEqual(remote_value.to_knx(RemoteValueStartStopDimming.Direction.INCREASE),
                         DPTBinary(1))
        self.assertEqual(remote_value.to_knx(RemoteValueStartStopDimming.Direction.DECREASE),
                         DPTBinary(9))

    def test_from_knx_startstop_invert(self):
        """Test from_knx function with inverted operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopDimming(xknx, invert=True)
        self.assertEqual(remote_value.from_knx(DPTBinary(9)),
                         RemoteValueStartStopDimming.Direction.DECREASE)
        self.assertEqual(remote_value.from_knx(DPTBinary(1)),
                         RemoteValueStartStopDimming.Direction.INCREASE)

    def test_to_knx_startstop_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopDimming(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx(1)

    def test_set(self):
        """Test setting value."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopDimming(
            xknx,
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(remote_value.decrease()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(1)))
        self.loop.run_until_complete(asyncio.Task(remote_value.increase()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(9)))

    def test_process(self):
        """Test process telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopDimming(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTBinary(1))
        self.assertEqual(remote_value.value, None)
        self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        self.assertEqual(remote_value.value, RemoteValueStartStopDimming.Direction.DECREASE)

    def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopDimming(
            xknx,
            group_address=GroupAddress("1/2/3"))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray((0x01)))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTBinary(0x10))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
            # pylint: disable=pointless-statement
            remote_value.value


class TestRemoteValueStartStopBlinds(unittest.TestCase):
    """Test class for RemoteValueStartStopBlinds objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_to_knx_startstop(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopBlinds(xknx)
        self.assertEqual(remote_value.to_knx(RemoteValueStartStopBlinds.Direction.DOWN),
                         DPTBinary(9))
        self.assertEqual(remote_value.to_knx(RemoteValueStartStopBlinds.Direction.UP),
                         DPTBinary(1))

    def test_from_knx_startstop(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopBlinds(xknx)
        self.assertEqual(remote_value.from_knx(DPTBinary(9)),
                         RemoteValueStartStopBlinds.Direction.DOWN)
        self.assertEqual(remote_value.from_knx(DPTBinary(1)),
                         RemoteValueStartStopBlinds.Direction.UP)

    def test_to_knx_startstop_invert(self):
        """Test to_knx function with inverted operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopBlinds(xknx, invert=True)
        self.assertEqual(remote_value.to_knx(RemoteValueStartStopBlinds.Direction.DOWN),
                         DPTBinary(1))
        self.assertEqual(remote_value.to_knx(RemoteValueStartStopBlinds.Direction.UP),
                         DPTBinary(9))

    def test_from_knx_startstop_invert(self):
        """Test from_knx function with inverted operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopBlinds(xknx, invert=True)
        self.assertEqual(remote_value.from_knx(DPTBinary(9)),
                         RemoteValueStartStopBlinds.Direction.UP)
        self.assertEqual(remote_value.from_knx(DPTBinary(1)),
                         RemoteValueStartStopBlinds.Direction.DOWN)

    def test_to_knx_startstop_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopBlinds(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx(1)

    def test_set(self):
        """Test setting value."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopBlinds(
            xknx,
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(remote_value.up()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(1)))
        self.loop.run_until_complete(asyncio.Task(remote_value.down()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(9)))

    def test_process(self):
        """Test process telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopBlinds(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTBinary(1))
        self.assertEqual(remote_value.value, None)
        self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        self.assertEqual(remote_value.value, RemoteValueStartStopBlinds.Direction.UP)

    def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueStartStopBlinds(
            xknx,
            group_address=GroupAddress("1/2/3"))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray((0x01)))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTBinary(0x10))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
            # pylint: disable=pointless-statement
            remote_value.value
