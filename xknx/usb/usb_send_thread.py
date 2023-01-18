from __future__ import annotations

import logging
import queue
from queue import Queue
from typing import TYPE_CHECKING

from xknx.cemi import CEMIFrame
from xknx.core.thread import BaseThread
from xknx.usb.knx_hid_helper import KNXToUSBHIDConverter
from xknx.usb.util import USBDevice

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class USBSendThread(BaseThread):
    """ """

    def __init__(self, xknx: XKNX, usb_device: USBDevice, queue: Queue[CEMIFrame]):
        """ """
        super().__init__(name="USBSendThread")
        self.xknx = xknx
        self.usb_device = usb_device
        self._queue = queue

    def run(self) -> None:
        """ """
        while self._is_active.is_set():
            try:
                cemi_frame = self._queue.get(block=True)
                hid_frames = KNXToUSBHIDConverter.split_into_hid_frames(
                    cemi_frame.to_knx()
                )
                # after successful splitting actually send the frames
                for hid_frame in hid_frames:
                    self.usb_device.write(hid_frame.to_knx())
            except queue.Empty:
                pass
