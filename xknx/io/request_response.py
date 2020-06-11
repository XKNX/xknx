"""
Base class for sending a specific type of KNX/IP Packet to a KNX/IP device and wait for the corresponding answer.

Will report if the corresponding answer was not received.
"""
import anyio

from xknx.knxip import ErrorCode


class RequestResponse():
    """Class for sending a specific type of KNX/IP Packet to a KNX/IP device and wait for the corresponding answer."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, xknx, udp_client, awaited_response_class, timeout_in_seconds=1):
        """Initialize RequstResponse class."""
        self.xknx = xknx
        self.udpclient = udp_client
        self.awaited_response_class = awaited_response_class
        self.success = False
        self.timeout_in_seconds = timeout_in_seconds

    def create_knxipframe(self):
        """Create KNX/IP Frame object to be sent to device."""
        raise NotImplementedError('create_knxipframe has to be implemented')

    async def start(self):
        """Start. Send request and wait for an answer."""
        with self.udpclient.receiver(self.awaited_response_class.service_type) as recv:
            await self.send_request()
            try:
                async with anyio.fail_after(self.timeout_in_seconds):
                    async for msg in recv:
                        if await self.response_rec_callback(msg):
                            break
            except TimeoutError:
                self.xknx.logger.warning("Error: KNX bus did not respond in time to request of type '%s'",
                                         self.__class__.__name__)

    async def send_request(self):
        """Build knxipframe (within derived class) and send via UDP."""
        knxipframe = self.create_knxipframe()
        knxipframe.normalize()
        await self.udpclient.send(knxipframe)

    async def response_rec_callback(self, knxipframe, _=None):
        """Verify and handle knxipframe. Callback from internal udpclient."""
        if not isinstance(knxipframe.body, self.awaited_response_class):
            self.xknx.logger.warning("Cant understand knxipframe")
            return False
        if knxipframe.body.status_code == ErrorCode.E_NO_ERROR:
            self.success = True
            self.on_success_hook(knxipframe)
        else:
            self.on_error_hook(knxipframe)
        return True

    def on_success_hook(self, knxipframe):
        """Do something after having received a valid answer. May be overwritten in derived class."""
        # self.xknx.logger.debug('Success: received correct answer from KNX bus: %s', knxipframe.body.status_code)
        pass

    def on_error_hook(self, knxipframe):
        """Do something after having received error within given time. May be overwritten in derived class."""
        self.xknx.logger.warning("Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                                 self.__class__.__name__,
                                 self.awaited_response_class.__name__, knxipframe.body.status_code)
