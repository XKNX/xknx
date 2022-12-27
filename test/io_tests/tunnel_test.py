"""Test for KNX/IP Tunnelling connections."""
import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock, Mock, call, patch

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray
from xknx.exceptions import CommunicationError
from xknx.io import TCPTunnel, UDPTunnel
from xknx.io.const import CONNECTIONSTATE_REQUEST_TIMEOUT, HEARTBEAT_RATE
from xknx.io.gateway_scanner import GatewayDescriptor
from xknx.knxip import (
    HPAI,
    CEMIFrame,
    ConnectionStateRequest,
    ConnectionStateResponse,
    ConnectRequest,
    ConnectResponse,
    DescriptionRequest,
    DescriptionResponse,
    DisconnectRequest,
    DisconnectResponse,
    ErrorCode,
    KNXIPFrame,
    TunnellingAck,
    TunnellingRequest,
)
from xknx.knxip.knxip_enum import CEMIMessageCode, HostProtocol
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueWrite


class TestUDPTunnel:
    """Test class for xknx/io/Tunnel objects."""

    def setup_method(self):
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.xknx = XKNX()
        self.tg_received_mock = AsyncMock()
        self.tunnel = UDPTunnel(
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

    @pytest.mark.parametrize(
        "raw",
        [
            # L_Data.ind GroupValueWrite from 1.1.22 to to 5/1/22 with DPT9 payload 0C 3F
            # communication_channel_id: 0x02   sequence_counter: 0x21
            bytes.fromhex("0610 0420 0017 04 02 21 00 2900bcd011162916030080 0c 3f"),
            # L_Data.ind T_Connect from 1.0.250 to 1.0.255 (xknx tunnel endpoint)
            # communication_channel_id: 0x02   sequence_counter: 0x21
            bytes.fromhex("0610 0420 0014 04 02 21 00 2900b06010fa10ff0080"),
        ],
    )
    @patch("xknx.io.UDPTunnel._send_tunnelling_ack")
    async def test_tunnel_request_received(self, send_ack_mock, raw):
        """Test Tunnel for calling send_ack on normal frames."""
        _cemi = CEMIFrame()
        _cemi.from_knx(raw[10:])
        telegram = _cemi.telegram
        telegram.direction = TelegramDirection.INCOMING
        self.tunnel.expected_sequence_number = 0x21

        self.tunnel.transport.data_received_callback(raw, ("192.168.1.2", 3671))
        await asyncio.sleep(0)
        self.tg_received_mock.assert_called_once_with(telegram)
        send_ack_mock.assert_called_once_with(raw[7], raw[8])

    @patch("xknx.io.UDPTunnel._send_tunnelling_ack")
    @patch("xknx.io.UDPTunnel._send_cemi")
    async def test_tunnel_request_received_callback(
        self,
        send_cemi_mock,
        send_ack_mock,
    ):
        """Test Tunnel for responding to L_DATA.req with confirmation and indication."""
        # L_Data.req T_Connect from 1.0.250 to 1.0.255 (xknx tunnel endpoint) - ETS Line-Scan
        # communication_channel_id: 0x02   sequence_counter: 0x81
        raw_req = bytes.fromhex("0610 0420 0014 04 02 81 00 1100b06010fa10ff0080")

        _cemi = CEMIFrame()
        _cemi.from_knx(raw_req[10:])
        test_telegram = _cemi.telegram
        test_telegram.direction = TelegramDirection.INCOMING
        self.tunnel.expected_sequence_number = 0x81

        response_telegram = Telegram(source_address=self.tunnel._src_address)

        async def tg_received_mock(telegram):
            """Mock for telegram_received_callback."""
            assert telegram == test_telegram
            return [response_telegram]

        self.tunnel.telegram_received_callback = tg_received_mock
        self.tunnel.transport.data_received_callback(raw_req, ("192.168.1.2", 3671))

        await asyncio.sleep(0)
        confirmation_cemi = _cemi
        confirmation_cemi.code = CEMIMessageCode.L_DATA_CON
        response_cemi = CEMIFrame.init_from_telegram(
            response_telegram,
            code=CEMIMessageCode.L_DATA_IND,
            src_addr=self.tunnel._src_address,
        )
        assert send_cemi_mock.call_args_list == [
            call(confirmation_cemi),
            call(response_cemi),
        ]
        send_ack_mock.assert_called_once_with(raw_req[7], raw_req[8])

    async def test_repeated_tunnel_request(self, time_travel):
        """Test Tunnel for receiving repeated TunnellingRequest frames."""
        self.tunnel.transport.send = Mock()
        self.tunnel.communication_channel = 1
        self.tunnel.expected_sequence_number = 10

        test_telegram = Telegram(payload=GroupValueWrite(DPTArray((1,))))
        cemi = CEMIFrame.init_from_telegram(
            test_telegram, code=CEMIMessageCode.L_DATA_IND
        )
        test_frame = KNXIPFrame.init_from_body(
            TunnellingRequest(
                communication_channel_id=1,
                sequence_counter=10,
                raw_cemi=cemi.to_knx(),
            )
        )
        test_ack = KNXIPFrame.init_from_body(TunnellingAck(sequence_counter=10))
        test_frame_9 = deepcopy(test_frame)
        test_frame_9.body.sequence_counter = 9

        # first frame - ACK and processed
        self.tunnel._request_received(test_frame, None, None)
        await time_travel(0)
        assert self.tunnel.transport.send.call_args_list == [call(test_ack, addr=None)]
        self.tunnel.transport.send.reset_mock()
        assert self.tunnel.expected_sequence_number == 11
        assert self.tg_received_mock.call_count == 1
        # same sequence number as before - ACK, not processed
        self.tunnel._request_received(test_frame, None, None)
        await time_travel(0)
        assert self.tunnel.transport.send.call_args_list == [call(test_ack, addr=None)]
        self.tunnel.transport.send.reset_mock()
        assert self.tunnel.expected_sequence_number == 11
        assert self.tg_received_mock.call_count == 1
        # wrong sequence number - no ACK, not processed
        # reconnect if `auto_reconnect` was True
        with pytest.raises(CommunicationError):
            self.tunnel._request_received(test_frame_9, None, None)
        await time_travel(0)
        assert self.tunnel.transport.send.call_args_list == []
        self.tunnel.transport.send.reset_mock()
        assert self.tunnel.expected_sequence_number == 11
        assert self.tg_received_mock.call_count == 1

    @patch("xknx.io.UDPTunnel._send_tunnelling_ack")
    def test_tunnel_request_received_cemi_too_small(self, send_ack_mock):
        """Test Tunnel sending ACK for unsupported frames."""
        # <UnsupportedCEMIMessage description="CEMI too small. Length: 9; CEMI: 2900b06010fa10ff00" />
        # communication_channel_id: 0x02   sequence_counter: 0x81
        raw = bytes.fromhex("0610 0420 0013 04 02 81 00 2900b06010fa10ff00")
        self.tunnel.expected_sequence_number = 0x81

        self.tunnel.transport.data_received_callback(raw, ("192.168.1.2", 3671))
        self.tg_received_mock.assert_not_called()
        send_ack_mock.assert_called_once_with(0x02, 0x81)

    @patch("xknx.io.UDPTunnel._send_tunnelling_ack")
    def test_tunnel_request_received_apci_unsupported(self, send_ack_mock):
        """Test Tunnel sending ACK for unsupported frames."""
        # LDataInd Unsupported Extended APCI from 0.0.1 to 0/0/0 broadcast
        # <UnsupportedCEMIMessage description="APCI not supported: 0b1111111000 in CEMI: 2900b0d0000100000103f8" />
        # communication_channel_id: 0x02   sequence_counter: 0x4f
        raw = bytes.fromhex("0610 0420 0015 04 02 4f 00 2900b0d0000100000103f8")
        self.tunnel.expected_sequence_number = 0x4F

        self.tunnel.transport.data_received_callback(raw, ("192.168.1.2", 3671))
        self.tg_received_mock.assert_not_called()
        send_ack_mock.assert_called_once_with(0x02, 0x4F)

    async def test_tunnel_send_and_wait_for_l2_confirmation(self, time_travel):
        """Test tunnel waits for L_DATA.con before sending another L_DATA.req."""
        self.tunnel.transport.send = Mock()
        self.tunnel.communication_channel = 1
        self.tunnel.expected_sequence_number = 23

        test_telegram = Telegram(payload=GroupValueWrite(DPTArray((1,))))
        cemi = CEMIFrame.init_from_telegram(
            test_telegram, code=CEMIMessageCode.L_DATA_CON
        )
        test_ack = KNXIPFrame.init_from_body(TunnellingAck(sequence_counter=23))
        confirmation = KNXIPFrame.init_from_body(
            TunnellingRequest(
                communication_channel_id=1,
                sequence_counter=23,
                raw_cemi=cemi.to_knx(),
            )
        )
        task = asyncio.create_task(self.tunnel.send_telegram(test_telegram))
        await time_travel(0)
        self.tunnel.transport.handle_knxipframe(test_ack, HPAI())
        await time_travel(0)
        assert not task.done()
        assert self.tunnel.transport.send.call_count == 1
        self.tunnel.transport.handle_knxipframe(confirmation, HPAI())
        await time_travel(0)
        assert task.done()
        # one call for the outgoing request and one for the ACK for the confirmation
        assert self.tunnel.transport.send.call_count == 2
        await task

    async def test_tunnel_send_retry(self, time_travel):
        """Test tunnel resends the telegram when no ACK was received."""
        self.tunnel.transport.send = Mock()
        self.tunnel.communication_channel = 1
        self.tunnel.sequence_number = 23
        self.tunnel.expected_sequence_number = 15

        test_telegram = Telegram(payload=GroupValueWrite(DPTArray((1,))))
        cemi = CEMIFrame.init_from_telegram(
            test_telegram,
            code=CEMIMessageCode.L_DATA_REQ,
            src_addr=self.tunnel._src_address,
        )
        request = KNXIPFrame.init_from_body(
            TunnellingRequest(
                communication_channel_id=self.tunnel.communication_channel,
                sequence_counter=self.tunnel.sequence_number,
                raw_cemi=cemi.to_knx(),
            )
        )
        test_ack = KNXIPFrame.init_from_body(
            TunnellingAck(sequence_counter=self.tunnel.sequence_number)
        )
        confirmation_cemi = CEMIFrame.init_from_telegram(
            test_telegram, code=CEMIMessageCode.L_DATA_CON
        )
        confirmation = KNXIPFrame.init_from_body(
            TunnellingRequest(
                communication_channel_id=1,
                sequence_counter=15,
                raw_cemi=confirmation_cemi.to_knx(),
            )
        )
        confirmation_ack = KNXIPFrame.init_from_body(TunnellingAck(sequence_counter=15))

        task = asyncio.create_task(self.tunnel.send_telegram(test_telegram))
        await time_travel(0)
        assert self.tunnel.transport.send.call_args_list == [call(request, addr=None)]
        self.tunnel.transport.send.reset_mock()
        # no ACK received, resend same telegram
        await time_travel(1)
        assert self.tunnel.transport.send.call_args_list == [call(request, addr=None)]
        self.tunnel.transport.send.reset_mock()
        self.tunnel.transport.handle_knxipframe(test_ack, HPAI())
        await time_travel(0)
        assert not task.done()
        self.tunnel.transport.handle_knxipframe(confirmation, HPAI())
        await time_travel(0)
        assert task.done()
        assert self.tunnel.transport.send.call_args_list == [
            call(confirmation_ack, addr=None)
        ]
        self.tunnel.transport.send.reset_mock()
        await task

        # Test raise after 2 missed ACKs (reconnect if `auto_reconnect` was True)
        with pytest.raises(CommunicationError):
            task = asyncio.create_task(self.tunnel.send_telegram(test_telegram))
            # no ACKs received, for 2x wait time (with advancing the loop in between)
            await time_travel(1)
            await time_travel(1)
            assert self.tunnel.transport.send.call_count == 2
            self.tunnel.transport.send.reset_mock()
            await task

    @pytest.mark.parametrize(
        "route_back,data_endpoint_addr,local_endpoint",
        [
            (False, ("192.168.1.2", 56789), HPAI("192.168.1.1", 12345)),
            (True, None, HPAI()),
        ],
    )
    async def test_tunnel_connect_send_disconnect(
        self, time_travel, route_back, data_endpoint_addr, local_endpoint
    ):
        """Test initiating a tunnelling connection."""
        local_addr = ("192.168.1.1", 12345)
        remote_addr = ("192.168.1.2", 3671)
        self.tunnel.route_back = route_back
        gateway_data_endpoint = (
            HPAI(*data_endpoint_addr) if data_endpoint_addr else HPAI()
        )
        self.tunnel.transport.connect = AsyncMock()
        self.tunnel.transport.getsockname = Mock(return_value=local_addr)
        self.tunnel.transport.send = Mock()
        self.tunnel.transport.stop = Mock()

        # Connect
        connect_request = ConnectRequest(
            control_endpoint=local_endpoint,
            data_endpoint=local_endpoint,
        )
        connect_frame = KNXIPFrame.init_from_body(connect_request)

        connection_task = asyncio.create_task(self.tunnel.connect())
        await time_travel(0)
        self.tunnel.transport.connect.assert_called_once()
        self.tunnel.transport.send.assert_called_once_with(connect_frame)

        connect_response_frame = KNXIPFrame.init_from_body(
            ConnectResponse(
                communication_channel=23,
                data_endpoint=gateway_data_endpoint,
                identifier=7,
            )
        )
        self.tunnel.transport.handle_knxipframe(connect_response_frame, remote_addr)
        await connection_task
        assert self.tunnel._data_endpoint_addr == data_endpoint_addr
        assert self.tunnel._src_address == IndividualAddress(7)

        # Send - use data endpoint
        self.tunnel.transport.send.reset_mock()
        test_telegram = Telegram(payload=GroupValueWrite(DPTArray((1,))))
        cemi = CEMIFrame.init_from_telegram(
            test_telegram,
            code=CEMIMessageCode.L_DATA_REQ,
            src_addr=IndividualAddress(7),
        )
        test_telegram_frame = KNXIPFrame.init_from_body(
            TunnellingRequest(
                communication_channel_id=23,
                sequence_counter=0,
                raw_cemi=cemi.to_knx(),
            )
        )
        asyncio.create_task(self.tunnel.send_telegram(test_telegram))
        await time_travel(0)
        self.tunnel.transport.send.assert_called_once_with(
            test_telegram_frame, addr=data_endpoint_addr
        )
        # skip ack and confirmation

        # Disconnect
        self.tunnel.transport.send.reset_mock()
        disconnect_request = DisconnectRequest(
            communication_channel_id=23,
            control_endpoint=local_endpoint,
        )
        disconnect_frame = KNXIPFrame.init_from_body(disconnect_request)

        disconnection_task = asyncio.create_task(self.tunnel.disconnect())
        await time_travel(0)
        self.tunnel.transport.send.assert_called_once_with(disconnect_frame)

        disconnect_response_frame = KNXIPFrame.init_from_body(
            DisconnectResponse(communication_channel_id=23)
        )
        self.tunnel.transport.handle_knxipframe(disconnect_response_frame, remote_addr)
        await disconnection_task
        assert self.tunnel._data_endpoint_addr is None
        self.tunnel.transport.stop.assert_called_once()

    async def test_tunnel_request_description(self, time_travel):
        """Test tunnel requesting and returning description of connected interface."""
        local_addr = ("192.168.1.1", 12345)
        self.tunnel.transport.send = Mock()
        self.tunnel.transport.getsockname = Mock(return_value=local_addr)

        description_request = KNXIPFrame.init_from_body(
            DescriptionRequest(control_endpoint=self.tunnel.local_hpai)
        )
        description_response = KNXIPFrame.init_from_body(DescriptionResponse())

        task = asyncio.create_task(self.tunnel.request_description())
        await time_travel(0)
        self.tunnel.transport.send.assert_called_once_with(description_request)
        self.tunnel.transport.handle_knxipframe(description_response, HPAI())
        await time_travel(0)
        assert task.done()
        assert isinstance(task.result(), GatewayDescriptor)
        assert self.tunnel.transport.send.call_count == 1
        await task


class TestTCPTunnel:
    """Test class for xknx/io/TCPTunnel objects."""

    def setup_method(self):
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.xknx = XKNX()
        self.tg_received_mock = AsyncMock()
        self.tunnel = TCPTunnel(
            self.xknx,
            gateway_ip="192.168.1.2",
            gateway_port=3671,
            telegram_received_callback=self.tg_received_mock,
            auto_reconnect=False,
            auto_reconnect_wait=3,
        )

    async def test_tunnel_send_and_wait_for_l2_confirmation(self, time_travel):
        """Test tunnel waits for L_DATA.con before sending another L_DATA.req."""
        self.tunnel.transport.send = Mock()
        self.tunnel.communication_channel = 1

        test_telegram = Telegram(payload=GroupValueWrite(DPTArray((1,))))
        cemi = CEMIFrame.init_from_telegram(
            test_telegram, code=CEMIMessageCode.L_DATA_CON
        )
        confirmation = KNXIPFrame.init_from_body(
            TunnellingRequest(
                communication_channel_id=1,
                sequence_counter=23,
                raw_cemi=cemi.to_knx(),
            )
        )
        task = asyncio.create_task(self.tunnel.send_telegram(test_telegram))
        await time_travel(0)
        assert not task.done()
        assert self.tunnel.transport.send.call_count == 1
        self.tunnel.transport.handle_knxipframe(confirmation, HPAI())
        await time_travel(0)
        assert task.done()
        # one call for the outgoing request. No Acks for TCP.
        assert self.tunnel.transport.send.call_count == 1
        await task

    async def test_tunnel_heartbeat(self, time_travel):
        """Test tunnel sends heartbeat frame."""
        local_addr = ("192.168.1.1", 12345)
        remote_hpai = HPAI(
            ip_addr="192.168.1.2", port=3671, protocol=HostProtocol.IPV4_TCP
        )
        self.tunnel.transport.connect = AsyncMock()
        self.tunnel.transport.getsockname = Mock(return_value=(local_addr))
        self.tunnel.transport.send = Mock()
        self.tunnel.transport.stop = Mock()
        self.tunnel._tunnel_lost = Mock()

        # Connect
        connection_task = asyncio.create_task(self.tunnel.connect())
        await time_travel(0)
        self.tunnel.transport.connect.assert_called_once()

        connect_response_frame = KNXIPFrame.init_from_body(
            ConnectResponse(
                communication_channel=23,
                data_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
                identifier=7,
            )
        )
        self.tunnel.transport.handle_knxipframe(connect_response_frame, remote_hpai)
        await connection_task
        self.tunnel.transport.send.reset_mock()

        # Send heartbeat
        heartbeat_request = KNXIPFrame.init_from_body(
            ConnectionStateRequest(
                communication_channel_id=23,
                control_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
            )
        )
        heartbeat_response = KNXIPFrame.init_from_body(
            ConnectionStateResponse(
                communication_channel_id=23,
                status_code=ErrorCode.E_NO_ERROR,
            )
        )
        await time_travel(HEARTBEAT_RATE)
        self.tunnel.transport.send.assert_called_once_with(heartbeat_request)
        self.tunnel.transport.send.reset_mock()
        self.tunnel.transport.handle_knxipframe(heartbeat_response, remote_hpai)
        # test no retry-heartbeat was sent
        await time_travel(CONNECTIONSTATE_REQUEST_TIMEOUT)
        self.tunnel.transport.send.assert_not_called()
        # next regular heartbeat
        await time_travel(HEARTBEAT_RATE - CONNECTIONSTATE_REQUEST_TIMEOUT)
        self.tunnel.transport.send.assert_called_once_with(heartbeat_request)
        self.tunnel.transport.send.reset_mock()
        self.tunnel._tunnel_lost.assert_not_called()

    async def test_tunnel_heartbeat_no_answer(self, time_travel):
        """Test tunnel sends heartbeat frame."""
        local_addr = ("192.168.1.1", 12345)
        remote_hpai = HPAI(
            ip_addr="192.168.1.2", port=3671, protocol=HostProtocol.IPV4_TCP
        )
        self.tunnel.transport.connect = AsyncMock()
        self.tunnel.transport.getsockname = Mock(return_value=(local_addr))
        self.tunnel.transport.send = Mock()
        self.tunnel.transport.stop = Mock()
        self.tunnel._tunnel_lost = Mock()

        # Connect
        connection_task = asyncio.create_task(self.tunnel.connect())
        await time_travel(0)
        self.tunnel.transport.connect.assert_called_once()

        connect_response_frame = KNXIPFrame.init_from_body(
            ConnectResponse(
                communication_channel=23,
                data_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
                identifier=7,
            )
        )
        self.tunnel.transport.handle_knxipframe(connect_response_frame, remote_hpai)
        await connection_task
        self.tunnel.transport.send.reset_mock()

        # Send heartbeat
        heartbeat_request = KNXIPFrame.init_from_body(
            ConnectionStateRequest(
                communication_channel_id=23,
                control_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
            )
        )
        await time_travel(HEARTBEAT_RATE)
        self.tunnel.transport.send.assert_called_once_with(heartbeat_request)
        self.tunnel.transport.send.reset_mock()
        # no answer - repeat 3 times
        await time_travel(CONNECTIONSTATE_REQUEST_TIMEOUT)
        self.tunnel.transport.send.assert_called_once_with(heartbeat_request)
        self.tunnel.transport.send.reset_mock()
        await time_travel(CONNECTIONSTATE_REQUEST_TIMEOUT)
        self.tunnel.transport.send.assert_called_once_with(heartbeat_request)
        self.tunnel.transport.send.reset_mock()
        await time_travel(CONNECTIONSTATE_REQUEST_TIMEOUT)
        self.tunnel.transport.send.assert_called_once_with(heartbeat_request)
        self.tunnel.transport.send.reset_mock()
        await time_travel(CONNECTIONSTATE_REQUEST_TIMEOUT)
        # no answer - tunnel lost
        self.tunnel._tunnel_lost.assert_called_once()

    async def test_tunnel_heartbeat_error(self, time_travel):
        """Test tunnel sends heartbeat frame."""
        local_addr = ("192.168.1.1", 12345)
        remote_hpai = HPAI(
            ip_addr="192.168.1.2", port=3671, protocol=HostProtocol.IPV4_TCP
        )
        self.tunnel.transport.connect = AsyncMock()
        self.tunnel.transport.getsockname = Mock(return_value=(local_addr))
        self.tunnel.transport.send = Mock()
        self.tunnel.transport.stop = Mock()
        self.tunnel._tunnel_lost = Mock()

        # Connect
        connection_task = asyncio.create_task(self.tunnel.connect())
        await time_travel(0)
        self.tunnel.transport.connect.assert_called_once()

        connect_response_frame = KNXIPFrame.init_from_body(
            ConnectResponse(
                communication_channel=23,
                data_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
                identifier=7,
            )
        )
        self.tunnel.transport.handle_knxipframe(connect_response_frame, remote_hpai)
        await connection_task
        self.tunnel.transport.send.reset_mock()

        # Send heartbeat
        heartbeat_request = KNXIPFrame.init_from_body(
            ConnectionStateRequest(
                communication_channel_id=23,
                control_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
            )
        )
        heartbeat_error_response = KNXIPFrame.init_from_body(
            ConnectionStateResponse(
                communication_channel_id=23,
                status_code=ErrorCode.E_CONNECTION_ID,
            )
        )
        await time_travel(HEARTBEAT_RATE)
        self.tunnel.transport.send.assert_called_once_with(heartbeat_request)
        self.tunnel.transport.send.reset_mock()
        self.tunnel.transport.handle_knxipframe(heartbeat_error_response, remote_hpai)
        # repeat 3 times
        await time_travel(0)
        self.tunnel.transport.send.assert_called_once_with(heartbeat_request)
        self.tunnel.transport.send.reset_mock()
        self.tunnel.transport.handle_knxipframe(heartbeat_error_response, remote_hpai)
        await time_travel(0)
        self.tunnel.transport.send.assert_called_once_with(heartbeat_request)
        self.tunnel.transport.send.reset_mock()
        self.tunnel.transport.handle_knxipframe(heartbeat_error_response, remote_hpai)
        await time_travel(0)
        self.tunnel.transport.send.assert_called_once_with(heartbeat_request)
        self.tunnel.transport.send.reset_mock()
        self.tunnel.transport.handle_knxipframe(heartbeat_error_response, remote_hpai)
        await time_travel(0)
        # third retry had an error - tunnel lost
        self.tunnel._tunnel_lost.assert_called_once()
