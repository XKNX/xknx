import time
import logging
from typing import List, Optional
import platform

import usb

logger = logging.getLogger("xknx.log")
knx_logger = logging.getLogger("xknx.knx")
usb_logger = logging.getLogger("xknx.usb")


# https://raw.githubusercontent.com/calimero-project/calimero-core/master/resources/knxUsbVendorProductIds
KNOWN_DEVICES = [
    # KNX USB interfaces by Vendor ID
    # Created 2020-06-20
    #  VID ,   PID
    (0x0111, 0x1022),  # Makel Elektrik
    # Future Technology Devices International Limited
    (0x0403, 0x6898),  # Tokka
    # b+b
    (0x04CC, 0x0301),  # b+b Automations- und Steuerungstechnik
    # Siemens OCI700 interface (Synco family)
    (0x0681, 0x0014),  # Siemens HVAC
    # Siemens Automation & Drives
    (0x0908, 0x02DD),  # Siemens
    (0x0908, 0x02DC),  # Siemens HVAC
    (0x0908, 0x02E6),  # Schrack Technik GmbH
    # Weinzierl Engineering GmbH
    (0x0E77, 0x0111),  # Siemens
    (0x0E77, 0x0112),
    (0x0E77, 0x6910),  # Busch-Jaeger Elektro
    (0x0E77, 0x0104),  # GEWISS
    (0x0E77, 0x0104),  # Somfy
    (0x0E77, 0x0115),  # CONTROLtronic
    (0x0E77, 0x0102),  # Weinzierl Engineering GmbH
    (0x0E77, 0x0103),
    (0x0E77, 0x0104),
    (0x0E77, 0x2001),
    (0x0E77, 0x0121),  # Gustav Hensel GmbH & Co. KG
    (0x0E77, 0x0141),  # Schneider Electric (MG)
    # Insta
    (0x135E, 0x0023),  # Albrecht Jung
    (0x135E, 0x0123),
    (0x135E, 0x0323),
    (0x135E, 0x0021),  # Berker
    (0x135E, 0x0022),  # GIRA Giersiepen
    (0x135E, 0x0122),
    (0x135E, 0x0322),
    (0x135E, 0x0025),  # Hager Electro
    (0x135E, 0x0020),  # Insta GmbH
    (0x135E, 0x0320),
    (0x135E, 0x0024),  # Merten
    (0x135E, 0x0026),  # Feller
    (0x135E, 0x0326),
    (0x135E, 0x0028),  # Glamox AS
    (0x135E, 0x0027),  # Panasonic
    (0x135E, 0x0329),  # B.E.G.
    # Busch-Jaeger
    (0x145C, 0x1330),  # Busch-Jaeger Elektro
    (0x145C, 0x1490),
    # ABB STOTZ‐KONTAKT GmbH
    (0x147B, 0x2200),  # ABB
    (0x147B, 0x5120),
    # MCS Electronics ‐ OBSOLETE
    (0x16D0, 0x0490),  # TAPKO Technologies
    (0x16D0, 0x0491),  # MDT technologies
    (0x16D0, 0x0492),  # preussen automation
    # SATEL Ltd.
    (0x24D5, 0x0106),  # Satel sp. z o.o.
    # Tapko Technologies GmbH
    (0x28C2, 0x001A),  # VIMAR
    (0x28C2, 0x0002),  # Zennio
    (0x28C2, 0x0004),  # TAPKO Technologies
    (0x28C2, 0x0008),
    (0x28C2, 0x0006),  # HDL
    (0x28C2, 0x0007),  # Niko-Zublin
    (0x28C2, 0x000C),  # ESYLUX
    (0x28C2, 0x0010),  # Video-Star
    (0x28C2, 0x0015),  # Bes – Ingenium
    (0x28C2, 0x000E),  # APRICUM
    (0x28C2, 0x000F),
    (0x28C2, 0x0005),  # Philips Controls
    (0x28C2, 0x0003),  # Ekinex S.p.A.
    (0x28C2, 0x0011),  # Griesser AG
    (0x28C2, 0x0012),
    (0x28C2, 0x000B),  # VIVO
    (0x28C2, 0x000D),
    (0x28C2, 0x0017),  # Interra
    (0x28C2, 0x0013),  # MEAN WELL Enterprises Co. Ltd.
    (0x28C2, 0x0014),  # Ergo3 Sarl
    # ise GmbH
    (0x2A07, 0x0001),  # ise GmbH
    (0x2A07, 0x0002),  # Elsner Elektronik GmbH
    # DOGAWIST ‐ Investment GmbH
    (0x2D72, 0x0002),  # PEAKnx a DOGAWIST company
    (0x7660, 0x0002),  # KNX Association
]


class USBKNXInterfaceData:
    """ """

    def __init__(self, idVendor: int = 0x0000, idProduct: int = 0x0000, serial_number: str = ""):
        """ """
        self.idVendor = idVendor
        self.idProduct = idProduct
        self.serial_number = serial_number


class USBDevice:
    """Abstraction with basic information of usb devices"""

    def __init__(self):
        """"""
        self._device: Optional[usb.core.Device] = None
        self._manufacturer = ""
        self._product = ""
        self._serial_number = ""
        self._interface: Optional[usb.core.Interface] = None
        self._active_configuration = None
        self._ep_in: Optional[usb.core.Endpoint] = None
        self._ep_out: Optional[usb.core.Endpoint] = None

    @property
    def device(self) -> Optional[usb.core.Device]:
        """`usb.core.Device` object"""
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
        """returns `usb.core.Device` object"""
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
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN,
            )
            self._ep_out = usb.util.find_descriptor(
                self._interface,
                # match the first OUT endpoint
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT,
            )
            self._claim_interface()

    def release(self) -> None:
        """ """
        if self._device and self._interface:
            usb.util.release_interface(self._device, self._interface)
            # self._device.attach_kernel_driver(self._interface)

    def read(self) -> bytes:
        """ """
        response = bytes()
        if self._ep_in and self._device:
            try:
                response = self._ep_in.read(size_or_buffer=64, timeout=-1).tobytes()
                logger.debug(f"read {len(response)} bytes: {response.hex()}")
            except usb.core.USBTimeoutError:
                pass
            except usb.core.USBError as error:
                logger.warning(f"{str(error)}")
                time.sleep(1)
        else:
            logger.warning("no USB IN endpoint to read from")
        return response

    def write(self, data: bytes):
        """ """
        if self._device and self._ep_out:
            logger.debug(f"write {len(data)} bytes: {data.hex()}")
            write_count = self._ep_out.write(data)
            if write_count != len(data):
                logger.warning(f"{write_count} bytes instead of {len(data)} were written")
        else:
            logger.warning("no USB OUT endpoint to write to")

    def _claim_interface(self) -> None:
        """ """
        if self._device:  # if no device is connected, this will be None
            try:  # on Windows this doesn't work, but also does not seem necessary
                if self._device.is_kernel_driver_active(0):
                    try:
                        self._device.detach_kernel_driver(0)
                        usb.util.claim_interface(self._device, self._interface)
                    except usb.core.USBError as e:
                        usb_logger.error(f"Could not detach kernel driver: {str(e)}")
            except Exception as e:
                usb_logger.debug(str(e))


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
    matching_devices = [
        device
        for device in devices
        if (interface_data.serial_number and device.serial_number == str(interface_data.serial_number))
    ]
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
            usb.core.find(
                find_all=True,
                idVendor=interface_data.idVendor,
                idProduct=interface_data.idProduct,
                backend=_get_usb_backend(),
            )
        )
        device_list = _create_usb_device_list(usb_device_list)
    except usb.core.NoBackendError as e:
        usb_logger.error(str(e))
        raise
    return device_list


def get_all_known_knx_usb_devices() -> List[USBDevice]:
    """ """
    device_list = []
    try:
        usb_device_list = list(usb.core.find(find_all=True, backend=_get_usb_backend()))
        usb_device_list = list(
            filter(lambda device: bool((device.idVendor, device.idProduct) in KNOWN_DEVICES), usb_device_list)
        )
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
            interface = usb.util.find_descriptor(configuration, bInterfaceClass=self._class)
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
            usb.core.find(find_all=True, custom_match=FindHIDClass(hid_device_class), backend=_get_usb_backend())
        )
        device_list = _create_usb_device_list(usb_device_list)
    except usb.core.NoBackendError:
        usb_logger.error("No backend found")
        raise
    return device_list


def _get_usb_backend():
    """ """
    backend = None
    if platform.system() == "Windows":
        # TODO: here we loaded libusb dll and use it as backend
        #       libusb as backend on windows supports almost no function (install WinUSB with Zadig?)
        import os
        import usb.backend.libusb1

        dll_location = os.environ.get("XKNX_LIBUSB", "C:\\Windows\\System32\\libusb-1.0.dll")
        try:
            backend = usb.backend.libusb1.get_backend(find_library=lambda x: f"{dll_location}")
        except usb.core.NoBackendError as ex:
            logger.error(str(ex))
        if not backend:
            usb_logger.error(
                "No USB backend found. Set XKNX_LIBUSB environment variable pointing to libusb-1.0.dll or install it to C:\\Windows\\System32"
            )
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
                f"Exception reading information of idVendor: {device.idVendor}, idProduct: {device.idProduct}"
            )
            usb_logger.error(str(e))
    return device_list
