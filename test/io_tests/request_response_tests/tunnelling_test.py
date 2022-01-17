"""Unit test for KNX/IP Tunnelling Request/Response."""
from unittest.mock import patch

import pytest
from xknx import XKNX
from xknx.dpt import DPTArray
from xknx.io.request_response import Tunnelling
from xknx.io.transport import UDPTransport
from xknx.knxip import (
    HPAI,
    ErrorCode,
    KNXIPFrame,
    KNXIPServiceType,
    TunnellingAck,
    TunnellingRequest,
)
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


@pytest.mark.asyncio
class TestTunnelling:
    """Test class for xknx/io/Tunnelling objects."""

    async def test_tunnelling(self):
        """Test tunnelling from KNX bus."""
        xknx = XKNX()
        communication_channel_id = 23
        data_endpoint = ("192.168.1.2", 4567)
        udp_transport = UDPTransport(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x1, 0x2, 0x3))),
        )
        sequence_counter = 42
        src_address = IndividualAddress("2.2.2")
        tunnelling = Tunnelling(
            xknx,
            udp_transport,
            data_endpoint,
            telegram,
            src_address,
            sequence_counter,
            communication_channel_id,
        )
        tunnelling.timeout_in_seconds = 0

        assert tunnelling.awaited_response_class == TunnellingAck
        assert tunnelling.communication_channel_id == communication_channel_id

        # Expected KNX/IP-Frame:
        tunnelling_request = TunnellingRequest(
            xknx,
            communication_channel_id=communication_channel_id,
            sequence_counter=sequence_counter,
        )
        tunnelling_request.pdu.telegram = telegram
        tunnelling_request.pdu.src_addr = src_address
        exp_knxipframe = KNXIPFrame.init_from_body(tunnelling_request)
        with patch("xknx.io.transport.UDPTransport.send") as mock_udp_send, patch(
            "xknx.io.transport.UDPTransport.getsockname"
        ) as mock_udp_getsockname:
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            await tunnelling.start()
            mock_udp_send.assert_called_with(exp_knxipframe, addr=data_endpoint)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame(xknx)
        wrong_knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_REQUEST)
        with patch("logging.Logger.warning") as mock_warning:
            tunnelling.response_rec_callback(wrong_knxipframe, HPAI(), None)
            mock_warning.assert_called_with("Could not understand knxipframe")

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame(xknx)
        err_knxipframe.init(KNXIPServiceType.TUNNELLING_ACK)
        err_knxipframe.body.status_code = ErrorCode.E_CONNECTION_ID
        with patch("logging.Logger.debug") as mock_warning:
            tunnelling.response_rec_callback(err_knxipframe, HPAI(), None)
            mock_warning.assert_called_with(
                "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                type(tunnelling).__name__,
                type(err_knxipframe.body).__name__,
                ErrorCode.E_CONNECTION_ID,
            )

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame(xknx)
        res_knxipframe.init(KNXIPServiceType.TUNNELLING_ACK)
        tunnelling.response_rec_callback(res_knxipframe, HPAI(), None)
        assert tunnelling.success
