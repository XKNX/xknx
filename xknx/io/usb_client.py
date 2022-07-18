import logging
from typing import List

from ..usb import get_first_matching_usb_device, USBKNXInterfaceData
from xknx.exceptions.exception import USBDeviceNotFoundError
from xknx.io.connection import ConnectionConfigUSB
from xknx.knxip import CEMIFrame, CEMIMessageCode
from xknx.telegram import Telegram
from xknx.usb.util import USBDevice
from xknx.usb.knx_hid_datatypes import EMIID, DataSizeBySequenceNumber, PacketType, ProtocolID, SequenceNumber
from xknx.usb.knx_hid_frame import KNXHIDFrame, KNXHIDFrameData, KNXHIDReportBodyData, PacketInfo, PacketInfoData


logger = logging.getLogger("xknx.log")


class USBClient:
    """ """
    def __init__(self, xknx, connection_config: ConnectionConfigUSB) -> None:
        self.xknx = xknx
        self.connection_config = connection_config
        self.idVendor = self.connection_config.idVendor
        self.idProduct = self.connection_config.idProduct
        self.usb_device: USBDevice | None = None

    @property
    def interface_data(self):
        return USBKNXInterfaceData(self.idVendor, self.idProduct)

    def start(self) -> None:
        self.usb_device = get_first_matching_usb_device(self.interface_data)

        if not self.usb_device:
            message = f"Device with idVendor: {self.idVendor}, idProduct: {self.idProduct} not found"
            logger.error(message)
            raise USBDeviceNotFoundError(message)

        self.usb_device.use()

    def stop(self) -> None:
        """ """
        if self.usb_device:
            self.usb_device.release()
        self.usb_device = None

    def connect(self) -> bool:
        """ """
        self.usb_device.use()  # claims the interface and sets up the endpoints for read/write

    def disconnect(self) -> None:
        """ """
        self.usb_device.release()

    def send_telegram(self, telegram: Telegram) -> None:
        """ """
        logger.debug(f"sending: {telegram}")
        emi_code = CEMIMessageCode.L_DATA_REQ
        # create a cEMI frame from the telegram
        cemi = CEMIFrame.init_from_telegram(
            telegram=telegram,
            code=emi_code,
            src_addr=self.xknx.own_address,
        )
        data = bytes(cemi.to_knx())
        hid_frames = self._split_into_hid_frames(data)
        # after successful splitting actually send the frames
        for hid_frame in hid_frames:
            self.usb_device.write(hid_frame.to_knx())

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

    def _get_packet_type(self, overall_length: int, remaining_length: int, sequence_number: SequenceNumber) -> PacketType:
        """ """
        if overall_length <= 53:
            # one frame is necessary
            if sequence_number == SequenceNumber.FIRST_PACKET:
                return PacketType.START_AND_END
            else:
                logger.error(f"don't know which packet type. length: {overall_length}, sequence number: {str(sequence_number)}")
        elif 53 < overall_length <= (53 + 61):
            # two frames are necessary
            if sequence_number == SequenceNumber.FIRST_PACKET:
                return PacketType.START_AND_PARTIAL
            elif sequence_number == SequenceNumber.SECOND_PACKET:
                return PacketType.PARTIAL_AND_END
            else:
                logger.error(f"don't know which packet type. length: {overall_length}, sequence number: {str(sequence_number)}")
        elif overall_length > (53 + 61):
            # at least three frames are necessary
            if sequence_number == SequenceNumber.FIRST_PACKET:
                return PacketType.START_AND_PARTIAL
            elif sequence_number > SequenceNumber.FIRST_PACKET:
                return PacketType.PARTIAL
            elif sequence_number > SequenceNumber.FIRST_PACKET and remaining_length <= 61:
                return PacketType.PARTIAL_AND_END
        return PacketType.START_AND_END
