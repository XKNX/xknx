import logging
import asyncio
from xknx.core.thread import BaseThread
from xknx.knxip import CEMIFrame, CEMIMessageCode
from xknx.telegram import Telegram
from xknx.usb.util import USBDevice
from xknx.usb.knx_hid_frame import KNXHIDFrame

logger = logging.getLogger("xknx.log")


class USBReceiveThread(BaseThread):
    """ """

    def __init__(self, xknx, usb_device: USBDevice, queue: asyncio.Queue[Telegram | None]):
        """ """
        super().__init__(name="USBReceiveThread")
        self._xknx = xknx
        self._usb_device: USBDevice = usb_device
        self._receive_queue = queue

    def run(self) -> None:
        """ """
        while self._is_active.is_set():
            usb_data = self._usb_device.read()
            if usb_data:
                # TODO: parse HID frame and concatenate one or more hid frames to KNX frame
                knx_hid_frame = KNXHIDFrame.from_knx(usb_data)
                if knx_hid_frame.is_valid:
                    cemi_frame = CEMIFrame()
                    cemi_frame.from_knx(knx_hid_frame.report_body.transfer_protocol_body.data[
                                        :knx_hid_frame.report_body.transfer_protocol_header.body_length])
                    logger.debug(f"receiving: {cemi_frame.telegram}")
                    self._xknx.telegrams.put_nowait(cemi_frame.telegram)
                else:
                    logger.debug(f"ignoring invalid USB HID frame: {usb_data.hex()}")
