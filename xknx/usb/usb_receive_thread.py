import logging
import asyncio
from xknx.core.thread import BaseThread
from xknx.exceptions import UnsupportedCEMIMessage
from xknx.knxip import CEMIFrame
from xknx.telegram import Telegram, TelegramDirection
from xknx.usb.util import USBDevice
from xknx.usb.knx_hid_frame import KNXHIDFrame
from xknx.usb.knx_hid_datatypes import PacketType

logger = logging.getLogger("xknx.log")


class USBReceiveThread(BaseThread):
    """ """

    def __init__(self, xknx, usb_device: USBDevice, queue: asyncio.Queue[Telegram | None]):
        """ """
        super().__init__(name="USBReceiveThread")
        self._xknx = xknx
        self._usb_device: USBDevice = usb_device
        self._receive_queue: asyncio.Queue[Telegram | None] = queue
        self._knx_data_length = 0
        self._knx_raw: bytes = bytes()

    def run(self) -> None:
        """ """
        while self._is_active.is_set():
            usb_data = self._usb_device.read()
            if usb_data:
                # TODO: parse HID frame and concatenate one or more hid frames to KNX frame
                knx_hid_frame = KNXHIDFrame.from_knx(usb_data)
                if knx_hid_frame.is_valid:
                    # 3.4.1.3 Data (KNX HID report body)
                    # KNX USB Transfer Protocol Header (only in start packet!)
                    if knx_hid_frame.report_header.packet_info.packet_type == PacketType.START_AND_END:
                        self._knx_raw = knx_hid_frame.report_body.transfer_protocol_body.data[:knx_hid_frame.report_body.transfer_protocol_header.body_length]
                        self.create_telegram_and_put_in_queue()
                    elif knx_hid_frame.report_header.packet_info.packet_type == PacketType.START_AND_PARTIAL:
                        self._knx_data_length = knx_hid_frame.report_body.transfer_protocol_header.body_length
                        self._knx_raw = knx_hid_frame.report_body.transfer_protocol_body.data
                    elif knx_hid_frame.report_header.packet_info.packet_type == PacketType.PARTIAL:
                        self._knx_raw += knx_hid_frame.report_body.transfer_protocol_body.data
                    if knx_hid_frame.report_header.packet_info.packet_type == PacketType.PARTIAL_AND_END:
                        self._knx_raw += knx_hid_frame.report_body.transfer_protocol_body.data
                        self._knx_raw = self._knx_raw[:self._knx_data_length]
                        self.create_telegram_and_put_in_queue()
                else:
                    logger.debug(f"ignoring invalid USB HID frame: {usb_data.hex()}")

    def create_telegram_and_put_in_queue(self):
        """ """
        cemi_frame = CEMIFrame()
        try:
            cemi_frame.from_knx(self._knx_raw)
        except UnsupportedCEMIMessage as e:
            logger.warning(str(e))
            return
        telegram = cemi_frame.telegram
        telegram.direction = TelegramDirection.INCOMING
        logger.debug(f"receiving: {telegram}")
        self._xknx.telegrams.put_nowait(telegram)
        self._knx_data_length = 0
        self._knx_raw = bytes()
