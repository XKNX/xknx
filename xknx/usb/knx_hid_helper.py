import logging
from typing import List, Tuple, Union
from xknx.knxip import CEMIFrame
from xknx.exceptions import UnsupportedCEMIMessage
from xknx.telegram import Telegram, TelegramDirection
from xknx.usb.knx_hid_frame import KNXHIDFrame, KNXHIDFrameData, KNXHIDReportBodyData, PacketInfo, PacketInfoData
from xknx.usb.knx_hid_datatypes import EMIID, DataSizeBySequenceNumber, PacketType, ProtocolID, SequenceNumber

logger = logging.getLogger("xknx.log")


class KNXToTelegram:
    """ """

    def __init__(self) -> None:
        self._knx_data_length = 0
        self._knx_raw: bytes = bytes()

    def _reset(self):
        """ """
        self._knx_data_length = 0
        self._knx_raw: bytes = bytes()

    def process(self, data: bytes) -> Tuple[bool, Union[Telegram,None]]:
        """ """
        if data:
            knx_hid_frame = KNXHIDFrame.from_knx(data)
            if knx_hid_frame.is_valid:
                # 3.4.1.3 Data (KNX HID report body)
                # KNX USB Transfer Protocol Header (only in start packet!)
                if knx_hid_frame.report_header.packet_info.packet_type == PacketType.START_AND_END:
                    self._knx_raw = knx_hid_frame.report_body.transfer_protocol_body.data[:knx_hid_frame.report_body.transfer_protocol_header.body_length]
                    return True, self.create_telegram()
                elif knx_hid_frame.report_header.packet_info.packet_type == PacketType.START_AND_PARTIAL:
                    self._knx_data_length = knx_hid_frame.report_body.transfer_protocol_header.body_length
                    self._knx_raw = knx_hid_frame.report_body.transfer_protocol_body.data
                elif knx_hid_frame.report_header.packet_info.packet_type == PacketType.PARTIAL:
                    self._knx_raw += knx_hid_frame.report_body.transfer_protocol_body.data
                elif knx_hid_frame.report_header.packet_info.packet_type == PacketType.PARTIAL_AND_END:
                    self._knx_raw += knx_hid_frame.report_body.transfer_protocol_body.data
                    self._knx_raw = self._knx_raw[:self._knx_data_length]
                    return True, self.create_telegram()
            else:
                logger.warning(f"ignoring invalid USB HID frame: {data.hex()}")
                self._reset()
        return False, None

    def create_telegram(self) -> Union[Telegram, None]:
        """ """
        cemi_frame = CEMIFrame()
        try:
            cemi_frame.from_knx(self._knx_raw)
        except UnsupportedCEMIMessage as e:
            logger.warning(str(e))
            return None
        telegram = cemi_frame.telegram
        telegram.direction = TelegramDirection.INCOMING
        logger.debug(f"assembled: {telegram}")
        self._reset()
        return telegram


def get_packet_type(overall_length: int, remaining_length: int, sequence_number: SequenceNumber) -> PacketType:
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


class KNXToUSBHIDConverter:
    """ """

    def __init__(self) -> None:
        pass

    @staticmethod
    def split_into_hid_frames(data: bytes) -> List[KNXHIDFrame]:
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
            packet_type = get_packet_type(overall_data_length, remaining_data_length, sequence_number)
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
