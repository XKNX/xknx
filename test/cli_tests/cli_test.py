"""Test the xknx command line interface."""

import argparse
import asyncio
from collections.abc import AsyncIterator
import os
import runpy
import signal
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

from xknx.cli import group, main
from xknx.cli._command import connection_config, gateway_argument
from xknx.cli.group import GroupCommand
from xknx.cli.group.monitor import MonitorCommand, print_telegram
from xknx.cli.group.write import parse_raw_value
from xknx.dpt import (
    DPTArray,
    DPTBinary,
    DPTColorRGB,
    DPTString,
    DPTSwitch,
    DPTTemperature,
)
from xknx.exceptions import CommunicationError, ConfirmationError, ConversionError
from xknx.io import DEFAULT_MCAST_PORT, ConnectionType, GatewayDescriptor
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove xknx environment variables."""
    monkeypatch.delenv("XKNX_GATEWAY", raising=False)
    monkeypatch.delenv("XKNX_LOCAL_IP", raising=False)


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


def test_command_registry() -> None:
    """Test the registered group commands."""
    assert [command.name for command in group.COMMANDS] == ["read", "write", "monitor"]
    assert all(issubclass(command, GroupCommand) for command in group.COMMANDS)


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
        ("gateway.example", ("gateway.example", DEFAULT_MCAST_PORT)),
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
        "2001:db8::1",  # IPv6 is not supported by the KNX/IP interface
        "[2001:db8::1]:3671",  # IPv6 is not supported by the KNX/IP interface
        "gateway.example/path",  # not plain 'host[:port]'
        "user@gateway.example",  # not plain 'host[:port]'
        "gateway.example?x=1",  # not plain 'host[:port]'
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
        ["scan", "--gateway", "10.0.0.1"],  # scan takes no --gateway
        ["group", "read", "1/2/3", "--gateway", ":3671"],  # invalid gateway
        ["group", "read", "1/2/3", "--gateway", "10.0.0.1:99999"],  # port out of range
        ["--gateway", "10.0.0.1", "group", "read", "1/2/3"],  # option before command
        ["group", "read", "1/2/300"],  # group address out of range
        ["group", "read", "i-test"],  # internal group address
        ["group", "write", "i-test", "on"],  # internal group address
        ["group", "read", "1/2/3", "--type", "unknown"],  # unknown DPT type
        ["group", "write", "1/2/3", "1", "--type", "unknown"],  # unknown DPT type
        ["group", "monitor", "--filter", "1-2-3/1"],  # invalid filter pattern
        ["scan", "--timeout", "0"],  # timeout must be positive
        ["scan", "--timeout", "-1"],  # timeout must be positive
        ["scan", "--timeout", "abc"],  # invalid timeout
    ],
)
def test_parser_errors(argv: list[str]) -> None:
    """Test invalid command lines exit with an argparse error."""
    with pytest.raises(SystemExit) as exc_info:
        main(argv)
    assert exc_info.value.code == 2


def test_read(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the read command prints the received value."""
    read_mock = AsyncMock(return_value=21.5)
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch("xknx.cli.group.read.read_group_value", read_mock),
    ):
        assert main(["group", "read", "1/2/3", "--type", "temperature"]) == 0
    assert read_mock.call_args.args[1] == GroupAddress("1/2/3")
    assert read_mock.call_args.kwargs["value_type"] is DPTTemperature
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
    """Test the write command sends and awaits a GroupValueWrite telegram."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch(
            "xknx.cemi.cemi_handler.CEMIHandler.send_telegram", AsyncMock()
        ) as send_mock,
    ):
        assert main(["group", "write", "1/2/3", "on", "--gateway", "10.0.0.1"]) == 0
    telegram = send_mock.call_args.args[0]
    assert telegram.destination_address == GroupAddress("1/2/3")
    assert telegram.payload == GroupValueWrite(DPTBinary(True))


def test_defaults_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the gateway and local IP default to environment variables."""
    monkeypatch.setenv("XKNX_GATEWAY", "10.0.0.1:1234")
    monkeypatch.setenv("XKNX_LOCAL_IP", "10.0.0.2")
    with (
        patch(
            "xknx.xknx.knx_interface_factory", return_value=_interface_mock()
        ) as factory_mock,
        patch("xknx.cemi.cemi_handler.CEMIHandler.send_telegram", AsyncMock()),
    ):
        assert main(["group", "write", "1/2/3", "on"]) == 0
    config = factory_mock.call_args.kwargs["connection_config"]
    assert config.connection_type is ConnectionType.TUNNELING
    assert config.gateway_ip == "10.0.0.1"
    assert config.gateway_port == 1234
    assert config.local_ip == "10.0.0.2"


def test_argument_overrides_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test an explicit --gateway wins over the environment variable."""
    monkeypatch.setenv("XKNX_GATEWAY", "10.0.0.1")
    with (
        patch(
            "xknx.xknx.knx_interface_factory", return_value=_interface_mock()
        ) as factory_mock,
        patch("xknx.cemi.cemi_handler.CEMIHandler.send_telegram", AsyncMock()),
    ):
        assert main(["group", "write", "1/2/3", "on", "--gateway", "10.0.0.9"]) == 0
    assert factory_mock.call_args.kwargs["connection_config"].gateway_ip == "10.0.0.9"


def test_invalid_environment_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test an invalid $XKNX_GATEWAY exits with an argparse error."""
    monkeypatch.setenv("XKNX_GATEWAY", ":3671")
    with pytest.raises(SystemExit):
        main(["group", "read", "1/2/3"])


def test_write_with_type_converts_value() -> None:
    """Test the write command sends the DPT-encoded payload."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch(
            "xknx.cemi.cemi_handler.CEMIHandler.send_telegram", AsyncMock()
        ) as send_mock,
    ):
        assert main(["group", "write", "1/2/3", "21.5", "--type", "temperature"]) == 0
    telegram = send_mock.call_args.args[0]
    assert telegram.payload == GroupValueWrite(DPTArray((0x0C, 0x33)))


@pytest.mark.parametrize(
    ("argv_value", "argv_type", "expected_payload"),
    [
        ("true", "switch", DPTBinary(True)),  # JSON boolean
        ("1", "switch", DPTBinary(True)),  # JSON number
        ("0", "switch", DPTBinary(False)),  # JSON number
        ("on", "switch", DPTBinary(True)),  # plain string - not JSON
        ("comfort", "hvac_mode", DPTArray((0x01,))),  # enum name string
        ('{"red": 255, "green": 0, "blue": 0}', "232.600", DPTArray((255, 0, 0))),
        # string DPT values are literal text, never JSON-decoded
        ("null", "string", DPTString.to_knx("null")),
        ("true", "string", DPTString.to_knx("true")),
        ("1e2", "string", DPTString.to_knx("1e2")),
    ],
)
def test_write_value_parsing(
    argv_value: str, argv_type: str, expected_payload: DPTBinary | DPTArray
) -> None:
    """Test typed write values parse as JSON with a plain string fallback."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch(
            "xknx.cemi.cemi_handler.CEMIHandler.send_telegram", AsyncMock()
        ) as send_mock,
    ):
        assert main(["group", "write", "1/2/3", argv_value, "--type", argv_type]) == 0
    assert send_mock.call_args.args[0].payload == GroupValueWrite(expected_payload)


def test_write_invalid_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the write command rejects malformed JSON before connecting."""
    with patch("xknx.xknx.knx_interface_factory") as factory_mock:
        assert main(["group", "write", "1/2/3", '{"red": ', "--type", "232.600"]) == 2
    factory_mock.assert_not_called()
    assert "Error: invalid JSON value" in capsys.readouterr().err


def test_write_raw_hex_payload() -> None:
    """Test a typeless hex value - as printed by read - writes a raw payload."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch(
            "xknx.cemi.cemi_handler.CEMIHandler.send_telegram", AsyncMock()
        ) as send_mock,
    ):
        assert main(["group", "write", "1/2/3", "0c33"]) == 0
    telegram = send_mock.call_args.args[0]
    assert telegram.payload == GroupValueWrite(DPTArray((0x0C, 0x33)))


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (21.5, "21.5\n"),
        (DPTSwitch.from_knx(DPTBinary(True)), "on\n"),
        (
            DPTColorRGB.from_knx(DPTArray((255, 0, 0))),
            '{"red": 255, "green": 0, "blue": 0}\n',
        ),
        ((12, 51), "0c33\n"),  # raw payload read without --type
    ],
)
def test_read_output_format(
    value: object, expected: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test read output can be passed back to write."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch("xknx.cli.group.read.read_group_value", AsyncMock(return_value=value)),
    ):
        assert main(["group", "read", "1/2/3"]) == 0
    assert capsys.readouterr().out == expected


def test_write_confirmation_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Test a write without bus confirmation exits with an error."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch(
            "xknx.cemi.cemi_handler.CEMIHandler.send_telegram",
            AsyncMock(side_effect=ConfirmationError("L_DATA_CON timed out")),
        ),
    ):
        assert main(["group", "write", "1/2/3", "on"]) == 1
    assert "Error:" in capsys.readouterr().err


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
    with patch("xknx.xknx.knx_interface_factory") as factory_mock:
        assert main(["group", "write", "1/2/3", value]) == 2
    factory_mock.assert_not_called()
    assert "--type is required" in capsys.readouterr().err


def test_write_invalid_value_for_type(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the write command rejects an unconvertible value before connecting."""
    with patch("xknx.xknx.knx_interface_factory") as factory_mock:
        assert main(["group", "write", "1/2/3", "nope", "--type", "temperature"]) == 2
    factory_mock.assert_not_called()
    err = capsys.readouterr().err
    assert "Error: Could not serialize DPTTemperature" in err
    assert "<ConversionError" not in err


TEST_GATEWAY = GatewayDescriptor(
    ip_addr="10.0.0.1",
    port=3671,
    name="TestGateway",
    individual_address=IndividualAddress("1.0.0"),
    supports_tunnelling=True,
)


def _scanner_mock(
    gateways: list[GatewayDescriptor], error: Exception | None = None
) -> Mock:
    """Create a GatewayScanner mock yielding the given gateways."""

    async def _scan() -> AsyncIterator[GatewayDescriptor]:
        if error is not None:
            raise error
        for gateway in gateways:
            yield gateway

    scanner_mock = Mock()
    scanner_mock.async_scan = _scan
    return scanner_mock


def test_scan(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the scan command with an explicit local IP prints found gateways."""
    with patch(
        "xknx.cli.scan.GatewayScanner", return_value=_scanner_mock([TEST_GATEWAY])
    ) as scanner_cls:
        assert main(["scan", "--local-ip", "10.0.0.2", "--timeout", "1"]) == 0
    assert scanner_cls.call_args.kwargs["local_ip"] == "10.0.0.2"
    assert scanner_cls.call_args.kwargs["timeout_in_seconds"] == 1.0
    out = capsys.readouterr().out
    assert "TestGateway" in out
    assert "1.0.0 10.0.0.1:3671" in out
    assert "tunnelling: UDP" in out


def test_scan_local_ip_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Test scan errors are raised when an explicit local IP was given."""
    with patch(
        "xknx.cli.scan.GatewayScanner",
        return_value=_scanner_mock([], error=CommunicationError("bind failed")),
    ):
        assert main(["scan", "--local-ip", "10.0.0.2"]) == 1
    assert "Error: bind failed" in capsys.readouterr().err


def test_scan_all_interfaces(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the scan command scans all non-loopback interfaces by default."""
    local_ips = [
        Mock(ip="10.0.0.2"),
        Mock(ip="127.0.0.1"),  # loopback is skipped
        Mock(ip="192.168.0.2"),
        Mock(ip="172.20.0.2"),
    ]
    scanners = [
        _scanner_mock([], error=CommunicationError("bind failed")),  # ignored
        _scanner_mock([TEST_GATEWAY]),
        _scanner_mock([TEST_GATEWAY]),  # same gateway heard on another interface
    ]
    with (
        patch("xknx.cli.scan.get_local_ips", return_value=local_ips),
        patch("xknx.cli.scan.GatewayScanner", side_effect=scanners) as scanner_cls,
    ):
        assert main(["-v", "scan"]) == 0
    assert scanner_cls.call_count == 3
    out = capsys.readouterr().out
    assert out.count("TestGateway") == 1  # deduplicated


def test_scan_no_gateways(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the scan command without results."""
    with (
        patch("xknx.cli.scan.get_local_ips", return_value=[Mock(ip="10.0.0.2")]),
        patch("xknx.cli.scan.GatewayScanner", return_value=_scanner_mock([])),
    ):
        assert main(["-vv", "scan"]) == 1
    assert "No gateways found." in capsys.readouterr().err


def test_scan_no_usable_interface(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the scan command reports when no usable interface exists."""
    with patch(
        "xknx.cli.scan.get_local_ips", return_value=[Mock(ip="127.0.0.1")]
    ):  # only loopback
        assert main(["scan"]) == 1
    assert "no usable network interface" in capsys.readouterr().err


def test_scan_all_interfaces_failed(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the scan command reports interface errors when nothing is found."""
    with (
        patch("xknx.cli.scan.get_local_ips", return_value=[Mock(ip="10.0.0.2")]),
        patch(
            "xknx.cli.scan.GatewayScanner",
            return_value=_scanner_mock([], error=CommunicationError("bind failed")),
        ),
    ):
        assert main(["scan"]) == 1
    err = capsys.readouterr().err
    assert "Scan failed on 10.0.0.2: bind failed" in err
    assert "No gateways found." in err


def test_monitor() -> None:
    """Test the monitor command runs until interrupted."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch(
            "xknx.cli.group.monitor.MonitorCommand._wait_for_sigint", AsyncMock()
        ) as wait_mock,
    ):
        assert (
            main(["group", "monitor", "--filter", "1/2/*", "--filter", "1/4/5-6,8"])
            == 0
        )
    wait_mock.assert_called_once()


async def test_wait_for_sigint() -> None:
    """Test the SIGINT handler is installed locally and removed afterwards."""
    loop = asyncio.get_running_loop()
    task = asyncio.create_task(MonitorCommand._wait_for_sigint())
    await asyncio.sleep(0)  # let the handler install
    os.kill(os.getpid(), signal.SIGINT)
    await asyncio.wait_for(task, timeout=1)
    # the handler was removed - a second SIGINT would raise KeyboardInterrupt
    assert loop.remove_signal_handler(signal.SIGINT) is False


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


def test_scan_ignores_gateway_environment(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test the scan command is not affected by $XKNX_GATEWAY."""
    monkeypatch.setenv("XKNX_GATEWAY", ":not even valid")
    with (
        patch("xknx.cli.scan.get_local_ips", return_value=[Mock(ip="10.0.0.2")]),
        patch("xknx.cli.scan.GatewayScanner", return_value=_scanner_mock([])),
    ):
        assert main(["scan"]) == 1
    assert "No gateways found." in capsys.readouterr().err


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

    array_telegram = Telegram(
        destination_address=GroupAddress("1/2/3"),
        direction=TelegramDirection.INCOMING,
        payload=GroupValueWrite(DPTArray((0x0C, 0x33))),
    )
    print_telegram(array_telegram)
    # raw payloads print like `group read` output
    assert "| 0c33" in capsys.readouterr().out

    read_telegram = Telegram(
        destination_address=GroupAddress("1/2/3"),
        direction=TelegramDirection.INCOMING,
        payload=GroupValueRead(),
    )
    print_telegram(read_telegram)
    assert "GroupValueRead" in capsys.readouterr().out


def test_runtime_conversion_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Test a ConversionError at runtime - e.g. an undecodable payload - exits 1."""
    with (
        patch("xknx.xknx.knx_interface_factory", return_value=_interface_mock()),
        patch(
            "xknx.cli.group.read.read_group_value",
            AsyncMock(side_effect=ConversionError("Payload invalid")),
        ),
    ):
        assert main(["group", "read", "1/2/3", "--type", "temperature"]) == 1
    assert "Error: Payload invalid" in capsys.readouterr().err


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
