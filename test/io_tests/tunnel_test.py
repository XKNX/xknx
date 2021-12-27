"""Unit test for KNX/IP Tunnelling Request/Response."""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from xknx import XKNX
from xknx.dpt import DPTArray
from xknx.io import Tunnel
from xknx.knxip import (
    HPAI,
    CEMIFrame,
    ConnectRequest,
    ConnectResponse,
    DisconnectRequest,
    DisconnectResponse,
    KNXIPFrame,
    TunnellingAck,
    TunnellingRequest,
)
from xknx.knxip.knxip_enum import CEMIMessageCode
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueWrite


@pytest.mark.asyncio
class TestTunnel:
    """Test class for xknx/io/Tunnel objects."""

    def setup_method(self):
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.xknx = XKNX()
        self.tg_received_mock = Mock()
        self.tunnel = Tunnel(
            self.xknx,
            gateway_ip="192.168.1.2",
            gateway_port=3671,
            local_ip="192.168.1.1",
            local_port=0,
            telegram_received_callback=self.tg_received_mock,
            auto_reconnect=False,
            auto_reconnect_wait=3,
            route_back=False,
        )

    @patch("xknx.io.Tunnel._send_tunnelling_ack")
    def test_tunnel_request_received(self, send_ack_mock):
        """Test Tunnel for calling send_ack on normal frames."""
        # LDataInd GroupValueWrite from 1.1.22 to to 5/1/22 with DPT9 payload 0C 3F
        # communication_channel_id: 0x02   sequence_counter: 0x21
        raw = bytes.fromhex("0610 0420 0017 04 02 21 00 2900bcd011162916030080 0c 3f")
        _cemi = CEMIFrame(self.xknx)
        _cemi.from_knx(raw[10:])
        telegram = _cemi.telegram
        telegram.direction = TelegramDirection.INCOMING

        self.tunnel.udp_client.data_received_callback(raw, ("192.168.1.2", 3671))
        self.tg_received_mock.assert_called_once_with(telegram)
        send_ack_mock.assert_called_once_with(0x02, 0x21)

    @patch("xknx.io.Tunnel._send_tunnelling_ack")
    def test_tunnel_request_received_cemi_too_small(self, send_ack_mock):
        """Test Tunnel sending ACK for unsupported frames."""
        # LDataInd T_Connect from 1.0.250 to 1.0.255 (xknx tunnel endpoint) - ETS Line-Scan
        # <UnsupportedCEMIMessage description="CEMI too small. Length: 10; CEMI: 2900b06010fa10ff0080" />
        # communication_channel_id: 0x02   sequence_counter: 0x81
        raw = bytes.fromhex("0610 0420 0014 04 02 81 00 2900b06010fa10ff0080")

        self.tunnel.udp_client.data_received_callback(raw, ("192.168.1.2", 3671))
        self.tg_received_mock.assert_not_called()
        send_ack_mock.assert_called_once_with(0x02, 0x81)

    @patch("xknx.io.Tunnel._send_tunnelling_ack")
    def test_tunnel_request_received_apci_unsupported(self, send_ack_mock):
        """Test Tunnel sending ACK for unsupported frames."""
        # LDataInd Unsupported Extended APCI from 0.0.1 to 0/0/0 broadcast
        # <UnsupportedCEMIMessage description="APCI not supported: 0b1111111000 in CEMI: 2900b0d0000100000103f8" />
        # communication_channel_id: 0x02   sequence_counter: 0x4f
        raw = bytes.fromhex("0610 0420 0015 04 02 4f 00 2900b0d0000100000103f8")

        self.tunnel.udp_client.data_received_callback(raw, ("192.168.1.2", 3671))
        self.tg_received_mock.assert_not_called()
        send_ack_mock.assert_called_once_with(0x02, 0x4F)

    async def test_tunnel_wait_for_l2_confirmation(self, time_travel):
        """Test tunnel waits for L_DATA.con before sending another L_DATA.req."""
        self.tunnel.udp_client.send = Mock()
        self.tunnel.communication_channel = 1

        test_telegram = Telegram(payload=GroupValueWrite(DPTArray((1,))))
        test_ack = KNXIPFrame.init_from_body(
            TunnellingAck(self.xknx, sequence_counter=23)
        )
        confirmation = KNXIPFrame.init_from_body(
            TunnellingRequest(
                self.xknx,
                communication_channel_id=1,
                sequence_counter=23,
                cemi=CEMIFrame.init_from_telegram(
                    self.xknx, test_telegram, code=CEMIMessageCode.L_DATA_CON
                ),
            )
        )
        task = asyncio.create_task(self.tunnel.send_telegram(test_telegram))
        await time_travel(0)
        self.tunnel.udp_client.handle_knxipframe(test_ack, HPAI())
        await time_travel(0)
        assert not task.done()
        assert self.tunnel.udp_client.send.call_count == 1
        self.tunnel.udp_client.handle_knxipframe(confirmation, HPAI())
        await time_travel(0)
        assert task.done()
        # one call for the outgoing request and one for the ACK for the confirmation
        assert self.tunnel.udp_client.send.call_count == 2
        await task

    async def test_tunnel_connect_send_disconnect(self, time_travel):
        """Test initiating a tunnelling connection."""
        local_addr = ("192.168.1.1", 12345)
        gateway_control_addr = ("192.168.1.2", 3671)
        gateway_data_addr = ("192.168.1.2", 56789)
        self.tunnel.udp_client.connect = AsyncMock()
        self.tunnel.udp_client.getsockname = Mock(return_value=local_addr)
        self.tunnel.udp_client.send = Mock()
        self.tunnel.udp_client.stop = AsyncMock()

        # Connect
        connect_request = ConnectRequest(
            self.xknx,
            control_endpoint=HPAI(*local_addr),
            data_endpoint=HPAI(*local_addr),
        )
        connect_frame = KNXIPFrame.init_from_body(connect_request)

        connection_task = asyncio.create_task(self.tunnel.connect())
        await time_travel(0)
        self.tunnel.udp_client.connect.assert_called_once()
        self.tunnel.udp_client.send.assert_called_once_with(connect_frame)

        connect_response_frame = KNXIPFrame.init_from_body(
            ConnectResponse(
                self.xknx,
                communication_channel=23,
                data_endpoint=HPAI(*gateway_data_addr),
                identifier=7,
            )
        )
        self.tunnel.udp_client.handle_knxipframe(
            connect_response_frame, gateway_control_addr
        )
        await connection_task
        assert self.tunnel._data_endpoint_addr == gateway_data_addr
        assert self.tunnel._src_address == IndividualAddress(7)

        # Send - use data endpoint
        self.tunnel.udp_client.send.reset_mock()
        test_telegram = Telegram(payload=GroupValueWrite(DPTArray((1,))))
        test_telegram_frame = KNXIPFrame.init_from_body(
            TunnellingRequest(
                self.xknx,
                communication_channel_id=23,
                sequence_counter=0,
                cemi=CEMIFrame.init_from_telegram(
                    self.xknx,
                    test_telegram,
                    code=CEMIMessageCode.L_DATA_REQ,
                    src_addr=IndividualAddress(7),
                ),
            )
        )
        asyncio.create_task(self.tunnel.send_telegram(test_telegram))
        await time_travel(0)
        self.tunnel.udp_client.send.assert_called_once_with(
            test_telegram_frame, addr=gateway_data_addr
        )
        # skip ack and confirmation

        # Disconnect
        self.tunnel.udp_client.send.reset_mock()
        disconnect_request = DisconnectRequest(
            self.xknx, communication_channel_id=23, control_endpoint=HPAI(*local_addr)
        )
        disconnect_frame = KNXIPFrame.init_from_body(disconnect_request)

        disconnection_task = asyncio.create_task(self.tunnel.disconnect())
        await time_travel(0)
        self.tunnel.udp_client.send.assert_called_once_with(disconnect_frame)

        disconnect_response_frame = KNXIPFrame.init_from_body(
            DisconnectResponse(
                self.xknx,
                communication_channel_id=23,
            )
        )
        self.tunnel.udp_client.handle_knxipframe(
            disconnect_response_frame, gateway_control_addr
        )
        await disconnection_task
        assert self.tunnel._data_endpoint_addr is None
        self.tunnel.udp_client.stop.assert_called_once()
