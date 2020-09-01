"""
Abstraction for handling KNX/IP routing.

Routing uses UDP Multicast to broadcast and receive KNX/IP messages.
"""
from xknx.knxip import APCICommand, KNXIPFrame, KNXIPServiceType
from xknx.telegram import TelegramDirection

from .udp_client import UDPClient


class Routing:
    """Class for handling KNX/IP routing."""

    def __init__(self, xknx, telegram_received_callback, local_ip):
        """Initialize Routing class."""
        self.xknx = xknx
        self.telegram_received_callback = telegram_received_callback
        self.local_ip = local_ip

        self.udpclient = UDPClient(
            self.xknx,
            (local_ip, 0),
            (self.xknx.multicast_group, self.xknx.multicast_port),
            multicast=True,
        )

        self.udpclient.register_callback(
            self.response_rec_callback, [KNXIPServiceType.ROUTING_INDICATION]
        )

    def response_rec_callback(self, knxipframe, _):
        """Verify and handle knxipframe. Callback from internal udpclient."""
        if knxipframe.header.service_type_ident != KNXIPServiceType.ROUTING_INDICATION:
            self.xknx.logger.warning("Service type not implemented: %s", knxipframe)
        elif knxipframe.body.cemi is None:
            # ignore unsupported CEMI frame
            return
        elif knxipframe.body.cemi.src_addr == self.xknx.own_address:
            self.xknx.logger.debug("Ignoring own packet")
        elif knxipframe.body.cemi.cmd not in (
            APCICommand.GROUP_READ,
            APCICommand.GROUP_WRITE,
            APCICommand.GROUP_RESPONSE,
        ):
            self.xknx.logger.warning("APCI not implemented: %s", knxipframe)
        else:
            telegram = knxipframe.body.cemi.telegram
            telegram.direction = TelegramDirection.INCOMING

            if self.telegram_received_callback is not None:
                self.telegram_received_callback(telegram)

    async def send_telegram(self, telegram):
        """Send Telegram to routing connected device."""
        knxipframe = KNXIPFrame(self.xknx)
        knxipframe.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe.body.cemi.src_addr = self.xknx.own_address
        knxipframe.body.cemi.telegram = telegram
        knxipframe.body.cemi.sender = self.xknx.own_address
        knxipframe.normalize()
        await self.send_knxipframe(knxipframe)

    async def send_knxipframe(self, knxipframe):
        """Send KNXIPFrame to connected routing device."""
        self.udpclient.send(knxipframe)

    async def start(self):
        """Start routing."""
        await self.udpclient.connect()

    async def stop(self):
        """Stop routing."""
        await self.udpclient.stop()
