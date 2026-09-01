"""Test the xknx command line interface."""

import argparse
from collections.abc import AsyncIterator
import runpy
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

from xknx.cli import main
from xknx.cli._command import Command, connection_config, gateway_argument
from xknx.cli.group._base import GroupCommand
from xknx.cli.group.monitor import print_telegram
from xknx.cli.group.write import parse_raw_value
from xknx.dpt import DPTBinary
from xknx.exceptions import CommunicationError
from xknx.io import DEFAULT_MCAST_PORT, ConnectionType, GatewayDescriptor
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


def _interface_mock() -> Mock:
    """Create a KNX/IP interface mock."""
    mock = Mock()
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock.send_cemi = AsyncMock()
    return mock


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("on", True),
        ("True", True),
        ("off", False),
        ("FALSE", False),
        ("50", 50),
        ("21.5", 21.5),
        ("something", "something"),
    ],
)
def test_parse_raw_value(raw: str, expected: bool | int | float | str) -> None:
    """Test parsing raw command line values."""
    result = parse_raw_value(raw)
    assert result == expected
    assert type(result) is type(expected)


def test_command_discovery() -> None:
    """Test the command tree is built from direct subclasses."""
    top_level = {
        command.name: bool(command.subcommands()) for command in Command.subcommands()
    }
    assert top_level == {"scan": False, "group": True}
    group_commands = {command.name for command in GroupCommand.subcommands()}
    assert group_commands == {"read", "write", "monitor"}


def test_connection_config_automatic() -> None:
    """Test connection config without a gateway option."""
    args = argparse.Namespace(gateway=None, local_ip=None)
    config = connection_config(args)
    assert config.connection_type is ConnectionType.AUTOMATIC
    assert config.local_ip is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10.0.0.1", ("10.0.0.1", DEFAULT_MCAST_PORT)),
        ("10.0.0.1:1234", ("10.0.0.1", 1234)),
        ("[2001:db8::1]", ("2001:db8::1", DEFAULT_MCAST_PORT)),
        ("[2001:db8::1]:3671", ("2001:db8::1", 3671)),
    ],
)
def test_gateway_argument(raw: str, expected: tuple[str, int]) -> None:
    """Test parsing valid gateway arguments."""
    assert gateway_argument(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        ":3671",  # missing host
        "10.0.0.1:0",  # port out of range
        "10.0.0.1:65536",  # port out of range
        "10.0.0.1:notaport",  # invalid port
        "2001:db8::1",  # unbracketed IPv6 mis-splits into an invalid port
    ],
)
def test_gateway_argument_invalid(raw: str) -> None:
    """Test invalid gateway arguments are rejected."""
    with pytest.raises(argparse.ArgumentTypeError):
        gateway_argument(raw)


def test_connection_config_tunneling() -> None:
    """Test connection config with a gateway option."""
    args = argparse.Namespace(gateway=("10.0.0.1", 1234), local_ip="10.0.0.2")
    config = connection_config(args)
    assert config.connection_type is ConnectionType.TUNNELING
    assert config.gateway_ip == "10.0.0.1"
    assert config.gateway_port == 1234
    assert config.local_ip == "10.0.0.2"


@pytest.mark.parametrize(
    "argv",
    [
        [],  # missing subcommand
        ["group"],  # missing group subcommand
        ["group", "read"],  # missing group address
        ["group", "unknown"],  # unknown group subcommand
        ["group", "write", "1/2/3"],  # missing value
        ["unknown"],  # unknown subcommand
        ["--gateway", ":3671", "scan"],  # invalid gateway
        ["--gateway", "10.0.0.1:99999", "group", "read", "1/2/3"],  # port out of range
    ],
)
def test_parser_errors(argv: list[str]) -> None:
    """Test invalid command lines exit with an argparse error."""
    with pytest.raises(SystemExit):
        main(argv)


def test_read(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the read command prints the received value."""
    read_mock = AsyncMock(return_value=21.5)
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch("xknx.cli.group.read.read_group_value", read_mock),
    ):
        assert main(["group", "read", "1/2/3", "--type", "temperature"]) == 0
    assert read_mock.call_args.args[1] == "1/2/3"
    assert read_mock.call_args.kwargs["value_type"] == "temperature"
    assert capsys.readouterr().out == "21.5\n"


def test_read_no_response(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the read command without a response."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch("xknx.cli.group.read.read_group_value", AsyncMock(return_value=None)),
    ):
        assert main(["group", "read", "1/2/3"]) == 1
    assert "No response received." in capsys.readouterr().err


def test_write() -> None:
    """Test the write command."""
    write_mock = Mock()
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch("xknx.cli.group.write.group_value_write", write_mock),
    ):
        assert main(["--gateway", "10.0.0.1", "group", "write", "1/2/3", "on"]) == 0
    assert write_mock.call_args.args[1:] == ("1/2/3", True)
    assert write_mock.call_args.kwargs["value_type"] is None


def test_write_with_type_passes_raw_string() -> None:
    """Test the write command passes the raw string to the DPT transcoder."""
    write_mock = Mock()
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch("xknx.cli.group.write.group_value_write", write_mock),
    ):
        assert main(["group", "write", "1/2/3", "on", "--type", "switch"]) == 0
    assert write_mock.call_args.args[1:] == ("1/2/3", "on")
    assert write_mock.call_args.kwargs["value_type"] == "switch"


@pytest.mark.parametrize(
    "value",
    [
        "21.5",  # float requires a transcoder
        "something",  # string requires a transcoder
        "100",  # out of DPTBinary range
        "-1",  # out of DPTBinary range
    ],
)
def test_write_requires_type(value: str, capsys: pytest.CaptureFixture[str]) -> None:
    """Test the write command rejects values without --type before connecting."""
    assert main(["group", "write", "1/2/3", value]) == 1
    assert "--type is required" in capsys.readouterr().err


def test_write_invalid_type(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the write command rejects an unknown DPT type before connecting."""
    assert main(["group", "write", "1/2/3", "1", "--type", "unknown"]) == 1
    assert "Error:" in capsys.readouterr().err


def test_read_invalid_type(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the read command rejects an unknown DPT type before connecting."""
    assert main(["group", "read", "1/2/3", "--type", "unknown"]) == 1
    assert "Error:" in capsys.readouterr().err


def test_scan(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the scan command prints found gateways."""
    gateway = GatewayDescriptor(
        ip_addr="10.0.0.1",
        port=3671,
        name="TestGateway",
        individual_address=IndividualAddress("1.0.0"),
        supports_tunnelling=True,
    )

    async def _scan(
        *, stop_on_found: int | None = None
    ) -> AsyncIterator[GatewayDescriptor]:
        yield gateway

    scanner_mock = Mock()
    scanner_mock.async_scan = _scan
    scanner_mock.found_gateways = {"hpai": gateway}
    with patch("xknx.cli.scan.GatewayScanner", return_value=scanner_mock):
        assert main(["-v", "scan", "--timeout", "1"]) == 0
    out = capsys.readouterr().out
    assert "TestGateway" in out
    assert "1.0.0 10.0.0.1:3671" in out
    assert "tunnelling: UDP" in out


def test_scan_no_gateways(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the scan command without results."""

    async def _scan(
        *, stop_on_found: int | None = None
    ) -> AsyncIterator[GatewayDescriptor]:
        return
        yield

    scanner_mock = Mock()
    scanner_mock.async_scan = _scan
    scanner_mock.found_gateways = {}
    with patch("xknx.cli.scan.GatewayScanner", return_value=scanner_mock):
        assert main(["-vv", "scan"]) == 0
    assert "No gateways found." in capsys.readouterr().out


def test_monitor() -> None:
    """Test the monitor command runs until interrupted."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch("xknx.xknx.XKNX.loop_until_sigint", AsyncMock()) as loop_mock,
    ):
        assert main(["group", "monitor", "--filter", "1/2/*,1/4/5-6"]) == 0
    loop_mock.assert_called_once()


def test_keyboard_interrupt_exit_code() -> None:
    """Test an interrupted command exits with 130."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch(
            "xknx.cli.group.read.read_group_value",
            AsyncMock(side_effect=KeyboardInterrupt),
        ),
    ):
        assert main(["group", "read", "1/2/3"]) == 130


def test_scan_rejects_gateway(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the scan command rejects the --gateway option."""
    assert main(["--gateway", "10.0.0.1", "scan"]) == 2
    assert "--gateway is not applicable" in capsys.readouterr().err


def test_print_telegram(capsys: pytest.CaptureFixture[str]) -> None:
    """Test printing received telegrams."""
    telegram = Telegram(
        destination_address=GroupAddress("1/2/3"),
        direction=TelegramDirection.INCOMING,
        payload=GroupValueWrite(DPTBinary(1)),
    )
    print_telegram(telegram)
    out = capsys.readouterr().out
    assert "1/2/3" in out
    assert "| 1" in out

    read_telegram = Telegram(
        destination_address=GroupAddress("1/2/3"),
        direction=TelegramDirection.INCOMING,
        payload=GroupValueRead(),
    )
    print_telegram(read_telegram)
    assert "GroupValueRead" in capsys.readouterr().out


def test_communication_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Test XKNX exceptions are reported with exit code 1."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch(
            "xknx.cli.group.read.read_group_value",
            AsyncMock(side_effect=CommunicationError("boom")),
        ),
    ):
        assert main(["group", "read", "1/2/3"]) == 1
    assert "Error: boom" in capsys.readouterr().err


def test_main_module() -> None:
    """Test `python -m xknx --help`."""
    with (
        patch.object(sys, "argv", ["xknx", "--help"]),
        pytest.raises(SystemExit),
    ):
        runpy.run_module("xknx", run_name="__main__")
