import logging
import queue
from queue import Queue
from typing import List
from xknx.core.thread import BaseThread
from xknx.knxip import CEMIFrame, CEMIMessageCode
from xknx.telegram import Telegram
from xknx.usb.knx_hid_datatypes import EMIID, DataSizeBySequenceNumber, PacketType, ProtocolID, SequenceNumber
from xknx.usb.knx_hid_frame import KNXHIDFrame, KNXHIDFrameData, KNXHIDReportBodyData, PacketInfo, PacketInfoData
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
                hid_frames = self._split_into_hid_frames(data)
                # after successful splitting actually send the frames
                for hid_frame in hid_frames:
                    self.usb_device.write(hid_frame.to_knx())
            except queue.Empty:
                logger.debug("USBSendThread nothing to send")

    def _split_into_hid_frames(self, data: bytes) -> List[KNXHIDFrame]:
        """ """
        hid_frames: List[KNXHIDFrame] = []
        overall_data_length = len(data)
        remaining_data_length = overall_data_length

        # split packets into different HID frames (not sending yet)
        sequence_number = SequenceNumber.FIRST_PACKET.value
        while remaining_data_length > 0:
            sequence_number = SequenceNumber(sequence_number)
            max_data_length = DataSizeBySequenceNumber.of(sequence_number)
            current_data_length = remaining_data_length if remaining_data_length < max_data_length else max_data_length
            current_data = data[:current_data_length]
            # setup KNXHIDFrame that is ready to be sent over USB
            partial = sequence_number > SequenceNumber.FIRST_PACKET
            packet_type = self._get_packet_type(overall_data_length, remaining_data_length, sequence_number)
            packet_info_data = PacketInfoData(sequence_number, packet_type)
            report_body_data = KNXHIDReportBodyData(ProtocolID.KNX_TUNNEL, EMIID.COMMON_EMI, current_data, partial)
            frame_data = KNXHIDFrameData(PacketInfo.from_data(packet_info_data), report_body_data)
            hid_frame = KNXHIDFrame.from_data(frame_data)
            hid_frames.append(hid_frame)
            # update remaining data
            data = data[current_data_length:]
            remaining_data_length = len(data)
            sequence_number += 1
        return hid_frames

    def _get_packet_type(self, overall_length: int, remaining_length: int,
                         sequence_number: SequenceNumber) -> PacketType:
        """ """
        if overall_length <= 53:
            # one frame is necessary
            if sequence_number == SequenceNumber.FIRST_PACKET:
                return PacketType.START_AND_END
            else:
                logger.error(
                    f"don't know which packet type. length: {overall_length}, sequence number: {str(sequence_number)}")
        elif 53 < overall_length <= (53 + 61):
            # two frames are necessary
            if sequence_number == SequenceNumber.FIRST_PACKET:
                return PacketType.START_AND_PARTIAL
            elif sequence_number == SequenceNumber.SECOND_PACKET:
                return PacketType.PARTIAL_AND_END
            else:
                logger.error(
                    f"don't know which packet type. length: {overall_length}, sequence number: {str(sequence_number)}")
        elif overall_length > (53 + 61):
            # at least three frames are necessary
            if sequence_number == SequenceNumber.FIRST_PACKET:
                return PacketType.START_AND_PARTIAL
            elif sequence_number > SequenceNumber.FIRST_PACKET:
                return PacketType.PARTIAL
            elif sequence_number > SequenceNumber.FIRST_PACKET and remaining_length <= 61:
                return PacketType.PARTIAL_AND_END
        return PacketType.START_AND_END
