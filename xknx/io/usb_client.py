import logging
from queue import Queue

from xknx.exceptions.exception import USBDeviceNotFoundError
from xknx.io.connection import ConnectionConfigUSB
from xknx.telegram import Telegram
from xknx.usb.util import USBDevice
from xknx.usb import get_all_known_knx_usb_devices, get_first_matching_usb_device, USBKNXInterfaceData, USBSendThread, USBReceiveThread

logger = logging.getLogger("xknx.log")


class USBClient:
    """ """

    def __init__(self, xknx, connection_config: ConnectionConfigUSB) -> None:
        self.xknx = xknx
        self.connection_config = connection_config
        self.idVendor = self.connection_config.idVendor
        self.idProduct = self.connection_config.idProduct
        self.usb_device: USBDevice | None = None
        self._usb_send_thread: USBSendThread | None = None
        self._usb_receive_thread: USBReceiveThread | None = None
        self._send_queue: Queue[Telegram] = Queue()

    @property
    def interface_data(self):
        return USBKNXInterfaceData(self.idVendor, self.idProduct)

    def start(self) -> None:
        if self.idVendor == 0x0000 and self.idProduct == 0x0000:
            all_knx_usb_devices = get_all_known_knx_usb_devices()
            if len(all_knx_usb_devices) > 0:
                self.usb_device = all_knx_usb_devices[0]
        else:
            self.usb_device = get_first_matching_usb_device(self.interface_data)

        if not self.usb_device:
            message = f"Could not find a/any KNX device (idVendor: {self.idVendor}, idProduct: {self.idProduct})"
            logger.error(message)
            raise USBDeviceNotFoundError(message)

        self.usb_device.use()
        self._usb_send_thread = USBSendThread(self.xknx, self.usb_device, self._send_queue)
        self._usb_receive_thread = USBReceiveThread(self.xknx, self.usb_device, self.xknx.telegrams)
        self._usb_send_thread.start()
        self._usb_receive_thread.start()

    def stop(self) -> None:
        """ """
        self._usb_send_thread.stop()
        self._usb_receive_thread.stop()
        self._usb_send_thread.join(timeout=5.0)
        self._usb_receive_thread.join(timeout=5.0)
        logger.debug(f"{self._usb_send_thread.name} stopped")
        logger.debug(f"{self._usb_receive_thread.name} stopped")
        if self.usb_device:
            self.usb_device.release()
        self.usb_device = None

    def connect(self) -> bool:
        """ """
        self.usb_device.use()  # claims the interface and sets up the endpoints for read/write
        return True

    def disconnect(self) -> None:
        """ """
        self.usb_device.release()

    def send_telegram(self, telegram: Telegram) -> None:
        """ """
        logger.debug(f"sending: {telegram}")
        self._send_queue.put(telegram)
