from __future__ import annotations

import logging

from xknx.exceptions import UnsupportedCEMIMessage
from xknx.knxip import CEMIFrame
from xknx.telegram import Telegram, TelegramDirection
from xknx.usb.knx_hid_datatypes import (
    EMIID,
    DataSizeBySequenceNumber,
    PacketType,
    ProtocolID,
    SequenceNumber,
)
from xknx.usb.knx_hid_frame import (
    KNXHIDFrame,
    KNXHIDFrameData,
    KNXHIDReportBodyData,
    PacketInfo,
    PacketInfoData,
)

logger = logging.getLogger("xknx.log")


class KNXToTelegram:
    """ """

    def __init__(self) -> None:
        self._knx_data_length = 0
        self._knx_raw: bytes = b""

    def _reset(self):
        """ """
        self._knx_data_length = 0
        self._knx_raw: bytes = b""

    def process(self, data: bytes) -> tuple[bool, Telegram | None]:
        """ """
        if data:
            knx_hid_frame = KNXHIDFrame.from_knx(data)
            if knx_hid_frame.is_valid:
                # 3.4.1.3 Data (KNX HID report body)
                # KNX USB Transfer Protocol Header (only in start packet!)
                if (
                    knx_hid_frame.report_header.packet_info.packet_type
                    == PacketType.START_AND_END
                ):
                    self._knx_raw = knx_hid_frame.report_body.transfer_protocol_body.data[
                        : knx_hid_frame.report_body.transfer_protocol_header.body_length
                    ]
                    return True, self.create_telegram()
                elif (
                    knx_hid_frame.report_header.packet_info.packet_type
                    == PacketType.START_AND_PARTIAL
                ):
                    self._knx_data_length = (
                        knx_hid_frame.report_body.transfer_protocol_header.body_length
                    )
                    self._knx_raw = (
                        knx_hid_frame.report_body.transfer_protocol_body.data
                    )
                elif (
                    knx_hid_frame.report_header.packet_info.packet_type
                    == PacketType.PARTIAL
                ):
                    self._knx_raw += (
                        knx_hid_frame.report_body.transfer_protocol_body.data
                    )
                elif (
                    knx_hid_frame.report_header.packet_info.packet_type
                    == PacketType.PARTIAL_AND_END
                ):
                    self._knx_raw += (
                        knx_hid_frame.report_body.transfer_protocol_body.data
                    )
                    self._knx_raw = self._knx_raw[: self._knx_data_length]
                    return True, self.create_telegram()
            else:
                logger.warning(f"ignoring invalid USB HID frame: {data.hex()}")
                self._reset()
        return False, None

    def create_telegram(self) -> Telegram | None:
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


def get_packet_type(
    overall_length: int, remaining_length: int, sequence_number: SequenceNumber
) -> PacketType:
    """
    Returns the packet type depending on sequence number and bytes in frame.

    The overall size of a HID frame is 64 octets.
    The KNX HID Report Header has 3 octet.
    The KNX USB Transfer Protocol Header in the KNX HID Report Body
    has 8 octets and is only present in the first packet.

    Therefore:
        if the first packet has 64 - 3 - 8 = 53 octets or less, it fits in one frame.
        after the first frame there are 61 usable octets for the payload.
    """
    if overall_length <= DataSizeBySequenceNumber.of(SequenceNumber.FIRST_PACKET):
        # one frame is necessary
        if sequence_number == SequenceNumber.FIRST_PACKET:
            return PacketType.START_AND_END
        else:
            logger.error(
                f"don't know which packet type. length: {overall_length}, sequence number: {str(sequence_number)}"
            )
    elif (
        DataSizeBySequenceNumber.of(SequenceNumber.FIRST_PACKET)
        < overall_length
        <= (
            DataSizeBySequenceNumber.of(SequenceNumber.FIRST_PACKET)
            + DataSizeBySequenceNumber.of(SequenceNumber.SECOND_PACKET)
        )
    ):
        # two frames are necessary
        if sequence_number == SequenceNumber.FIRST_PACKET:
            return PacketType.START_AND_PARTIAL
        elif sequence_number == SequenceNumber.SECOND_PACKET:
            return PacketType.PARTIAL_AND_END
        else:
            logger.error(
                f"don't know which packet type. length: {overall_length}, sequence number: {str(sequence_number)}"
            )
    elif overall_length > (
        DataSizeBySequenceNumber.of(SequenceNumber.FIRST_PACKET)
        + DataSizeBySequenceNumber.of(SequenceNumber.SECOND_PACKET)
    ):
        # at least three frames are necessary
        if sequence_number == SequenceNumber.FIRST_PACKET:
            return PacketType.START_AND_PARTIAL
        # order of evaluation is important, the last condition would also be true, but yield the wrong value
        elif sequence_number > SequenceNumber.FIRST_PACKET and remaining_length <= 61:
            return PacketType.PARTIAL_AND_END
        elif sequence_number > SequenceNumber.FIRST_PACKET:
            return PacketType.PARTIAL
    return PacketType.START_AND_END


class KNXToUSBHIDConverter:
    """
    This class helps splitting (pure) KNX data as bytes and creates KNXHIDFrame(s)
    which represents a USB HID frame of max. 64 octets containing KNX meta information
    and the KNX payload.
    The KNX data is expected to start with the EMI code followed by the payload
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def split_into_hid_frames(data: bytes) -> list[KNXHIDFrame]:
        """ """
        hid_frames: list[KNXHIDFrame] = []
        overall_data_length = len(data)
        remaining_data_length = overall_data_length

        # split packets into different HID frames (not sending yet)
        sequence_number = SequenceNumber.FIRST_PACKET
        while remaining_data_length > 0:
            max_data_length = DataSizeBySequenceNumber.of(sequence_number)
            current_data_length = (
                remaining_data_length
                if remaining_data_length < max_data_length
                else max_data_length
            )
            current_data = data[:current_data_length]
            # setup KNXHIDFrame that is ready to be sent over USB
            partial = sequence_number > SequenceNumber.FIRST_PACKET
            packet_type = get_packet_type(
                overall_data_length, remaining_data_length, sequence_number
            )
            packet_info_data = PacketInfoData(sequence_number, packet_type)
            report_body_data = KNXHIDReportBodyData(
                ProtocolID.KNX_TUNNEL, EMIID.COMMON_EMI, current_data, partial
            )
            frame_data = KNXHIDFrameData(
                PacketInfo.from_data(packet_info_data), report_body_data
            )
            hid_frame = KNXHIDFrame.from_data(frame_data)
            hid_frames.append(hid_frame)
            # update remaining data
            data = data[current_data_length:]
            remaining_data_length = len(data)
            sequence_number = SequenceNumber(sequence_number.value + 1)
        return hid_frames
