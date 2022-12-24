import logging
import queue
from queue import Queue
from xknx.core.thread import BaseThread
from xknx.knxip import CEMIFrame, CEMIMessageCode
from xknx.telegram import Telegram
from xknx.usb.knx_hid_helper import KNXToUSBHIDConverter
from xknx.usb.util import USBDevice

logger = logging.getLogger("xknx.log")


class USBSendThread(BaseThread):
    """ """

    def __init__(self, xknx, usb_device: USBDevice, queue: Queue[Telegram]):
        """ """
        super().__init__(name="USBSendThread")
        self.xknx = xknx
        self.usb_device = usb_device
        self._queue = queue

    def run(self) -> None:
        """ """
        while self._is_active.is_set():
            try:
                telegram = self._queue.get(block=True)
                emi_code = CEMIMessageCode.L_DATA_REQ
                # create a cEMI frame from the telegram
                cemi = CEMIFrame.init_from_telegram(
                    telegram=telegram,
                    code=emi_code
                )
                data = bytes(cemi.to_knx())
                hid_frames = KNXToUSBHIDConverter.split_into_hid_frames(data)
                # after successful splitting actually send the frames
                for hid_frame in hid_frames:
                    self.usb_device.write(hid_frame.to_knx())
            except queue.Empty:
                logger.debug("USBSendThread nothing to send")
                pass

