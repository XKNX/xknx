"""Example for the telegram monitor callback."""

from __future__ import annotations

import asyncio
import getopt  # pylint: disable=deprecated-module
import sys
from typing import TYPE_CHECKING

from xknx import XKNX
from xknx.io.connection import ConnectionConfig
from xknx.telegram import AddressFilter, IndividualAddress, Telegram
from xknx.telegram.apci import GroupValueResponse, GroupValueWrite

if TYPE_CHECKING:
    from xknxproject.models import KNXProject


def show_help() -> None:
    """Print Help."""
    print("Listen to telegrams on the KNX bus.")
    print()
    print("Options:")
    print()
    print("Option           Argument example")
    print("-i --ia          1.0.253                 Individual address to connect to")
    print(
        "-f --filter      1/2/*,1/4/[5-6]         Filter for specific group addresses"
    )
    print(
        "-k --knxproject  myproject.knxproj       Load KNX project file for address resolution"
    )
    print("-h --help                                Print help")
    print()
    print("Example:")
    print('python example_telegram_monitor.py -i "1.0.253" -f 1/2/*,1/4/[5-6]')
    print("This will listen to all telegrams for group addresses 1/2/* and 1/4/[5-6].")


def load_project(file_path: str) -> KNXProject:
    """Load KNX project from file."""
    # pylint: disable=import-outside-toplevel
    try:
        from xknxproject import XKNXProj
        from xknxproject.exceptions import InvalidPasswordException
    except ImportError:
        print(
            "xknxproject package is not installed. Please install it with 'pip install xknxproject'."
        )
        sys.exit(1)

    xknxproj = XKNXProj(file_path)
    try:
        return xknxproj.parse()
    except InvalidPasswordException:
        password = input(
            "Project file is password protected. Please enter the password: "
        )
        xknxproj.password = password
        return xknxproj.parse()


async def monitor(
    ia: IndividualAddress | None,
    address_filters: list[AddressFilter] | None,
    knx_project: KNXProject | None = None,
) -> None:
    """Set telegram_received_cb within XKNX and connect to KNX/IP device in daemon mode."""
    xknx = XKNX(
        connection_config=ConnectionConfig(individual_address=ia),
        daemon_mode=True,
    )

    if knx_project is not None:
        dpt_dict = {
            ga: data["dpt"]
            for ga, data in knx_project["group_addresses"].items()
            if data["dpt"] is not None
        }
        xknx.group_address_dpt.set(dpt_dict)

    def telegram_received_cb(telegram: Telegram) -> None:
        """Do something with the received telegram."""
        ia_string = str(telegram.source_address)
        ga_string = str(telegram.destination_address)
        payload: str | int | tuple[int, ...]
        if isinstance(telegram.payload, GroupValueWrite | GroupValueResponse):
            payload = telegram.payload.value.value
        else:
            payload = str(telegram.payload.__class__.__name__)
        print(
            f"{telegram.direction.value:8} {ia_string:20} | {ga_string:24} | {payload}"
        )
        if knx_project:
            ia_name = ""
            ga_name = ""
            data_str = ""
            if (device := knx_project["devices"].get(ia_string)) is not None:
                ia_name = f"{device['manufacturer_name']} {device['name']}"
            if (ga_data := knx_project["group_addresses"].get(ga_string)) is not None:
                ga_name = ga_data["name"]
            if (data := telegram.decoded_data) is not None:
                data_str = f"{data.value} {data.transcoder.unit or ''}"
            print(f"{'':8} {ia_name[:20]:20} | {ga_name[:24]:24} | {data_str}")

    xknx.telegram_queue.register_telegram_received_cb(
        telegram_received_cb, address_filters
    )
    await xknx.start()
    await xknx.stop()


async def main(argv: list[str]) -> None:
    """Parse command line arguments and start monitor."""
    try:
        opts, _ = getopt.getopt(
            argv, "hf:i:k:", ["help", "filter=", "interface=", "knxproject="]
        )
    except getopt.GetoptError:
        show_help()
        sys.exit(2)

    address_filters = None
    ia = None
    knx_project = None
    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            show_help()
            sys.exit()
        if opt in ["-f", "--filter"]:
            address_filters = list(map(AddressFilter, arg.split(",")))
        if opt in ["-i", "--interface"]:
            ia = IndividualAddress(arg)
        if opt in ["-k", "--knxproject"]:
            knx_project = load_project(arg)

    await monitor(ia, address_filters, knx_project)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
