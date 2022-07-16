from enum import IntEnum
import logging
from typing import List, Optional
import platform

import usb

logger = logging.getLogger("xknx.log")
knx_logger = logging.getLogger("xknx.knx")
usb_logger = logging.getLogger("xknx.usb")


class USBVendorId(IntEnum):
    """ Vendor ID's """
    SIEMENS_OCI702 = 0x0908
    JUNG_2130USBREG = 0x135e


class USBProductId(IntEnum):
    """ Product ID's """
    SIEMENS_OCI702 = 0x02dc
    JUNG_2130USBREG = 0X0023


class USBKNXInterfaceData:
    """ """

    def __init__(self, idVendor: int = 0x0000, idProduct: int = 0x0000, serial_number: str = ""):
        """ """
        self.idVendor = idVendor
        self.idProduct = idProduct
        self.serial_number = serial_number


class USBDevice:
    """ Abstraction with basic information of usb devices """

    def __init__(self):
        """"""
        self._device: Optional[usb.Device] = None
        self._manufacturer = ""
        self._product = ""
        self._serial_number = ""
        self._interface: Optional[usb.Interface] = None
        self._active_configuration = None
        self._ep_in: Optional[usb.Endpoint] = None
        self._ep_out: Optional[usb.Endpoint] = None

    @property
    def device(self) -> Optional[usb.core.Device]:
        """ `usb.core.Device` object """
        return self._device

    @property
    def manufacturer(self):
        return self._manufacturer

    @property
    def product(self):
        return self._product

    @property
    def serial_number(self):
        return self._serial_number

    @property
    def active_configuration(self):
        return self._active_configuration

    @device.setter
    def device(self, device: usb.core.Device):
        """ returns `usb.core.Device` object """
        self._device = device

    @manufacturer.setter
    def manufacturer(self, manufacturer: str):
        self._manufacturer = manufacturer

    @product.setter
    def product(self, product: str):
        self._product = product

    @serial_number.setter
    def serial_number(self, serial_number: str):
        self._serial_number = serial_number

    def use(self) -> None:
        """ """
        if self._device:
            usb.logging.info(f"Using device: \n{self._device}")
            # if we have an interrupt port, use that one to communicate (3.3.2.3 HID class pipes)
            # here we assume there is one
            self._active_configuration = self._device.get_active_configuration()
            self._interface = self._active_configuration[(0, 0)]
            self._ep_in = usb.util.find_descriptor(
                self._interface,
                # match the first IN endpoint
                custom_match= \
                    lambda e: \
                        usb.util.endpoint_direction(e.bEndpointAddress) == \
                        usb.util.ENDPOINT_IN)
            self._ep_out = usb.util.find_descriptor(
                self._interface,
                # match the first OUT endpoint
                custom_match= \
                    lambda e: \
                        usb.util.endpoint_direction(e.bEndpointAddress) == \
                        usb.util.ENDPOINT_OUT)
            self._claim_interface()

    def release(self) -> None:
        """ """
        if self._device and self._interface:
            usb.util.release_interface(self._device, self._interface)
            #self._device.attach_kernel_driver(self._interface)

    def read(self) -> bytes:
        """ """
        response = bytes()
        if self._ep_in and self._device:
            response = self._ep_in.read(self._ep_in, self._ep_in.wMaxPacketSize, timeout=3000).tobytes()
            logger.debug(f"read {len(response)} bytes: {response.hex()}")
            #response = self._device.read(self._ep_in, self._ep_in.wMaxPacketSize, timeout=3000).tobytes()
        return response

    def write(self, data: bytes):
        """ """
        if self._device and self._ep_out:
            logger.debug(f"write {len(data)} bytes: {data.hex()}")
            self._ep_out.write(data)

    def _claim_interface(self) -> None:
        """ """
        if self._device:  # if no device is connected, this will be None
            if self._device.is_kernel_driver_active(0):
                try:
                    self._device.detach_kernel_driver(0)
                    usb.util.claim_interface(self._device, self._interface)
                except usb.core.USBError as e:
                    usb_logger.error(f"Could not detach kernel driver: {str(e)}")


def get_first_matching_usb_device(interface_data: USBKNXInterfaceData) -> Optional[USBDevice]:
    """
    Returns the device with serial number matching `interface_data.serial_number`.
    If there is more than one device with the same serial number, the first is returned.
    If no serial_number is passed, the first device returned from `get_connected_usb_device_list` will be returned.
    If no device can be found a default initialized `USBDevice` will be returned

    Parameters
    ----------
    interface_data: USBKNXInterfaceData
        contains the idVendor, idProduct and the serial number of a specific USB KNX interface

    Raises
    ------
    see function `get_connected_usb_device_list`

    Returns
    -------
    device: USBDevice
        object representing a usb device (if non is found, it's default initialized with None/empty string)
    """
    device = None
    devices = get_connected_usb_device_list(interface_data)
    matching_devices = [device for device in devices if
                        (interface_data.serial_number and device.serial_number == str(interface_data.serial_number))]
    if matching_devices:
        device = matching_devices[0]
    elif devices and not interface_data.serial_number:
        device = devices[0]
    return device


def get_connected_usb_device_list(interface_data: USBKNXInterfaceData) -> List[USBDevice]:
    """
    Enumerates all devices matching the vendor id `idVendor` and product id `idProduct`.

    Raises
    ------
    usb.core.NoBackendError

    Returns
    -------
    device_list: list
        a list of devices matching mentioned vendor/product id
    """
    device_list = []
    try:
        usb_device_list = list(
            usb.core.find(find_all=True, idVendor=interface_data.idVendor, idProduct=interface_data.idProduct,
                          backend=_get_usb_backend()))
        device_list = _create_usb_device_list(usb_device_list)
    except usb.core.NoBackendError as e:
        usb_logger.error(str(e))
        raise
    return device_list


class FindHIDClass(object):
    """
    https://github.com/pyusb/pyusb/blob/master/docs/tutorial.rst
    """

    def __init__(self, class_):
        self._class = class_

    def __call__(self, device):
        # check the device class in the device descriptor
        # in case this value is not the one we are looking for,
        # we continue searching in the interface descriptor
        if device.bDeviceClass == self._class:
            return True
        # continue search in the interface descriptor
        for configuration in device:
            # find_descriptor: what's it?
            interface = usb.util.find_descriptor(
                configuration,
                bInterfaceClass=self._class
            )
            if interface is not None:
                return True
        return False


def get_all_hid_devices() -> List[USBDevice]:
    """
    Can be used to get a list of all potential HID devices that could be a
    valid KNX interface.

    4.1 The HID Class
    ...
    The USB Core Specification defines the HID class code. The bInterfaceClass
    member of an Interface descriptor is always 3 for HID class devices.
    (Source: https://www.usb.org/sites/default/files/hid1_11.pdf)
    
    5.1 Device Descriptor Structure
    Note The bDeviceClass and bDeviceSubClass fields in the Device Descriptor
    should not be used to identify a device as belonging to the HID class. Instead use
    the bInterfaceClass and bInterfaceSubClass fields in the Interface descriptor.
    (Source: https://www.usb.org/sites/default/files/hid1_11.pdf)
    """
    hid_device_class = 0x03
    device_list = []
    try:
        usb_device_list = list(
            usb.core.find(find_all=True, custom_match=FindHIDClass(hid_device_class), backend=_get_usb_backend()))
        device_list = _create_usb_device_list(usb_device_list)
    except usb.core.NoBackendError:
        usb_logger.error("No backend found")
        raise
    return device_list


def _get_usb_backend():
    """ """
    backend = None
    if platform.system() == 'Windows':
        # TODO: here we loaded libusb dll and use it as backend
        #       libusb as backend on windows supports almost no function (install WinUSB with Zadig?)
        usb_logger.warning("TODO: load libusb dll on Windows")
    return backend


def _log_usb_device(index: int, device: usb.core.Device):
    """ """
    usb_logger.info(f"device {index}")
    usb_logger.info(f"    manufacturer  : {device.manufacturer} (idVendor: {device.idVendor:#0{6}x})")
    usb_logger.info(f"    product       : {device.product} (idProduct: {device.idProduct:#0{6}x})")
    usb_logger.info(f"    serial_number : {device.serial_number}")


def _create_usb_device(device: usb.core.Device) -> USBDevice:
    """ """
    usb_device = USBDevice()
    usb_device.device = device
    usb_device.manufacturer = device.manufacturer
    usb_device.product = device.product
    usb_device.serial_number = device.serial_number
    return usb_device


def _create_usb_device_list(usb_device_list: List[usb.core.Device]) -> List[USBDevice]:
    """ """
    device_list = []
    usb_logger.info(f"found {len(usb_device_list)} device(s)")
    for index, device in enumerate(usb_device_list, start=1):
        try:
            _log_usb_device(index, device)
            device_list.append(_create_usb_device(device))
        except ValueError as e:
            usb_logger.error(
                f"Exception reading information of idVendor: {device.idVendor}, idProduct: {device.idProduct}")
            usb_logger.error(str(e))
    return device_list
