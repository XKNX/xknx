import asyncio
from xknx.knxip import KNXIPServiceType, KNXIPFrame, HPAI, ErrorCode


class RequestResponse():

    def __init__(self, xknx, udp_client, awaited_response_class, timeout_in_seconds=1):
        self.xknx = xknx
        self.udpclient = udp_client
        self.awaited_response_class = awaited_response_class

        self.response_recieved_or_timeout = asyncio.Event()
        self.success = False

        self.timeout_in_seconds = timeout_in_seconds
        self.timeout_callback = None
        self.timeout_handle = None


    def start(self):
        task = asyncio.Task(self.async_start())
        self.xknx.loop.run_until_complete(task)


    @asyncio.coroutine
    def async_start(self):

        cb = self.udpclient.register_callback(
            self.response_rec_callback, [self.awaited_response_class.service_type])

        yield from self.send_request()
        yield from self.start_timeout()
        yield from self.response_recieved_or_timeout.wait()
        yield from self.stop_timeout()

        self.udpclient.unregister_callback(cb)
        

    @asyncio.coroutine
    def send_request(self):

        (local_addr, local_port) = self.udpclient.getsockname()

        knxipframe = self.create_knxipframe()
        knxipframe.normalize()

        self.udpclient.send(knxipframe)


    def response_rec_callback(self, knxipframe, _):
        if not isinstance(knxipframe.body, self.awaited_response_class):
            print("Cant understand knxipframe")
            return

        self.response_recieved_or_timeout.set()

        if knxipframe.body.status_code == ErrorCode.E_NO_ERROR:
            self.success = True
            self.on_success_hook(knxipframe)
        else:
            self.on_error_hook(knxipframe)


    def on_success_hook(self, knxipframe):
        pass


    def on_error_hook(self, knxipframe):
        print("Error connection state failed: ", knxipframe.body.status_code)


    def timeout(self):
        self.response_recieved_or_timeout.set()


    @asyncio.coroutine
    def start_timeout(self):
        self.timeout_handle = self.xknx.loop.call_later(
            self.timeout_in_seconds, self.timeout)

    @asyncio.coroutine
    def stop_timeout(self):
        self.timeout_handle.cancel()
