"""Example for the telegram monitor callback."""
import asyncio
from xknx import XKNX


@asyncio.coroutine
def telegram_received_cb(telegram):
    """Callback invoked after a telegram was received."""
    print("Telegram received: {0}".format(telegram))
    return True


async def main():
    """Set telegram_received_cb within XKNX and connect to KNX/IP device in daemon mode."""
    xknx = XKNX(telegram_received_cb=telegram_received_cb)
    await xknx.start(daemon_mode=True)
    await xknx.stop()


# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
