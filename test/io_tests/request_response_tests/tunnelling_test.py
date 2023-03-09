"""Unit test for KNX/IP Tunnelling Request/Response."""
from unittest.mock import patch

from xknx.cemi import CEMIFrame, CEMILData, CEMIMessageCode
from xknx.dpt import DPTArray
from xknx.io.request_response import Tunnelling
from xknx.io.transport import UDPTransport
from xknx.knxip import (
    HPAI,
    ConnectionStateRequest,
    ErrorCode,
    KNXIPFrame,
    TunnellingAck,
    TunnellingRequest,
)
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestTunnelling:
    """Test class for xknx/io/Tunnelling objects."""

    async def test_tunnelling(self):
        """Test tunnelling from KNX bus."""
        data_endpoint = ("192.168.1.2", 4567)
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        raw_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(
                Telegram(
                    destination_address=GroupAddress("1/2/3"),
                    payload=GroupValueWrite(DPTArray((0x1, 0x2, 0x3))),
                )
            ),
        ).to_knx()
        tunnelling_request = TunnellingRequest(
            communication_channel_id=23,
            sequence_counter=42,
            raw_cemi=raw_cemi,
        )
        tunnelling = Tunnelling(udp_transport, data_endpoint, tunnelling_request)
        tunnelling.timeout_in_seconds = 0

        assert tunnelling.awaited_response_class == TunnellingAck

        exp_knxipframe = KNXIPFrame.init_from_body(tunnelling_request)
        with patch("xknx.io.transport.UDPTransport.send") as mock_udp_send, patch(
            "xknx.io.transport.UDPTransport.getsockname"
        ) as mock_udp_getsockname:
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            await tunnelling.start()
            mock_udp_send.assert_called_with(exp_knxipframe, addr=data_endpoint)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame.init_from_body(ConnectionStateRequest())
        with patch("logging.Logger.warning") as mock_warning:
            tunnelling.response_rec_callback(wrong_knxipframe, HPAI(), None)
            mock_warning.assert_called_with("Could not understand knxipframe")

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame.init_from_body(
            TunnellingAck(status_code=ErrorCode.E_CONNECTION_ID)
        )
        with patch("logging.Logger.debug") as mock_warning:
            tunnelling.response_rec_callback(err_knxipframe, HPAI(), None)
            mock_warning.assert_called_with(
                "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                type(tunnelling).__name__,
                type(err_knxipframe.body).__name__,
                ErrorCode.E_CONNECTION_ID,
            )

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame.init_from_body(TunnellingAck())
        tunnelling.response_rec_callback(res_knxipframe, HPAI(), None)
        assert tunnelling.success
