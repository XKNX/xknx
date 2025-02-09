"""Unit test for XKNX Module."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from xknx import XKNX
from xknx.exceptions import CommunicationError
from xknx.io import ConnectionConfig, ConnectionType


class TestXknxModule:
    """Test class for XKNX."""

    def test_log_to_file(self) -> None:
        """Test logging enable."""
        XKNX(log_directory="/tmp/")
        _path = Path("/tmp/xknx.log")
        assert _path.is_file()
        _path.unlink()

    def test_log_to_file_when_dir_does_not_exist(self) -> None:
        """Test logging enable with non existent directory."""
        XKNX(log_directory="/xknx/is/fun")
        assert not Path("/xknx/is/fun/xknx.log").is_file()

    def test_register_telegram_cb(self) -> None:
        """Test register telegram callback."""
        xknx = XKNX(telegram_received_cb=AsyncMock())
        assert len(xknx.telegram_queue.telegram_received_cbs) == 1

    def test_register_device_cb(self) -> None:
        """Test register telegram callback."""
        xknx = XKNX(device_updated_cb=AsyncMock())
        assert len(xknx.devices.device_updated_cbs) == 1

    def test_register_connection_state_change_cb(self) -> None:
        """Test register con state callback."""
        xknx = XKNX(connection_state_changed_cb=Mock())
        assert len(xknx.connection_manager._connection_state_changed_cbs) == 1

    @patch("xknx.io.KNXIPInterface._start", new_callable=AsyncMock)
    async def test_xknx_start(self, start_mock: AsyncMock) -> None:
        """Test xknx start."""
        xknx = XKNX(state_updater=True)

        await xknx.start()
        start_mock.assert_called_once()
        await xknx.stop()

    @patch("xknx.io.KNXIPInterface._start", new_callable=AsyncMock)
    async def test_xknx_start_as_context_manager(
        self, ipinterface_mock: AsyncMock
    ) -> None:
        """Test xknx start."""
        async with XKNX(state_updater=True) as xknx:
            assert xknx.started.is_set()
            ipinterface_mock.assert_called_once()

    @patch("xknx.io.KNXIPInterface._start", new_callable=AsyncMock)
    async def test_xknx_start_and_stop_with_dedicated_connection_config(
        self, start_mock: AsyncMock
    ) -> None:
        """Test xknx start and stop with connection config."""
        connection_config = ConnectionConfig(connection_type=ConnectionType.TUNNELING)
        xknx = XKNX(connection_config=connection_config)

        await xknx.start()

        start_mock.assert_called_once()
        assert xknx.knxip_interface.connection_config == connection_config

        await xknx.stop()
        assert xknx.knxip_interface._interface is None
        assert xknx.telegram_queue._consumer_task.done()
        assert not xknx.state_updater.started

    @pytest.mark.parametrize(
        "connection_config",
        [
            ConnectionConfig(
                connection_type=ConnectionType.ROUTING, local_ip="127.0.0.1"
            ),
            ConnectionConfig(
                connection_type=ConnectionType.TUNNELING, gateway_ip="127.0.0.2"
            ),
        ],
    )
    @patch(
        "xknx.io.transport.UDPTransport.connect",
        new_callable=AsyncMock,
        side_effect=OSError,
    )
    async def test_xknx_start_initial_connection_error(
        self, transport_connect_mock: AsyncMock, connection_config: ConnectionConfig
    ) -> None:
        """Test xknx start raising when socket can't be set up."""
        xknx = XKNX(
            state_updater=True,
            connection_config=connection_config,
        )
        with pytest.raises(CommunicationError):
            await xknx.start()
        transport_connect_mock.assert_called_once()
        assert xknx.telegram_queue._consumer_task is None  # not started
        assert not xknx.state_updater.started
        assert not xknx.started.is_set()
