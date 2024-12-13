"""Example for the telegram monitor callback over unix domain socket."""

import asyncio
import getopt
import socket
import sys

from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import AddressFilter, Telegram


def telegram_received_cb(telegram: Telegram) -> None:
    """Do something with the received telegram."""
    print(f"Telegram received: {telegram}")


def show_help() -> None:
    """Print Help."""
    print("Telegram filter.")
    print("")
    print("Usage:")
    print("")
    print(__file__, "                            Listen to all telegrams")
    print(
        __file__, "-f --filter 1/2/*,1/4/[5-6]    Filter for specific group addresses"
    )
    print(
        __file__, "-host hostname                 Connect to a specific host over ssh"
    )
    print(__file__, "-h --help                      Print help")
    print("")


async def monitor(host, address_filters: list[AddressFilter] | None) -> None:
    """Set telegram_received_cb within XKNX and connect to KNX/IP device in daemon mode."""
    if host is None:
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP,
            gateway_path="/run/knxnet",
        )
    else:

        async def connect_ssh(loop, protocol_factory):
            s1, s2 = socket.socketpair()

            cmd = ["ssh", "--", host, "socat STDIO UNIX-CONNECT:/run/knxnet"]

            await asyncio.create_subprocess_exec(*cmd, stdin=s2, stdout=s2)

            return await loop.create_unix_connection(protocol_factory, sock=s1)

        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP,
            connect_cb=connect_ssh,
        )
    xknx = XKNX(connection_config=connection_config, daemon_mode=True)
    xknx.telegram_queue.register_telegram_received_cb(
        telegram_received_cb, address_filters
    )
    await xknx.start()
    await xknx.stop()


async def main(argv: list[str]) -> None:
    """Parse command line arguments and start monitor."""
    try:
        opts, _ = getopt.getopt(argv, "hf:", ["help", "filter=", "host="])
    except getopt.GetoptError:
        show_help()
        sys.exit(2)
    host = None
    address_filters = None
    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            show_help()
            sys.exit()
        if opt in ["--host"]:
            host = arg
        if opt in ["-f", "--filter"]:
            address_filters = list(map(AddressFilter, arg.split(",")))
    await monitor(host, address_filters)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
