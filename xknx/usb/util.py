from __future__ import annotations

import logging
import platform
import time

import hid
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

    def __init__(
        self, idVendor: int = 0x0000, idProduct: int = 0x0000, serial_number: str = ""
    ):
        """ """
        self.idVendor = idVendor
        self.idProduct = idProduct
        self.serial_number = serial_number


class USBDevice:
    """Abstraction with basic information of usb devices"""

    def __init__(self):
        """"""
        self._device: dict | None = None
        self._vendor_id: int = 0
        self._product_id: int = 0
        self._manufacturer = ""
        self._product = ""
        self._serial_number = ""
        self._hid_device: hid.device | None = None
        self._is_open: bool = False

    @property
    def device(self) -> dict | None:
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
    def vendor_id(self):
        return self._vendor_id

    @property
    def product_id(self):
        return self._product_id

    @device.setter
    def device(self, device: dict):
        """returns raw dict returned by hidapi"""
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

    @vendor_id.setter
    def vendor_id(self, vendor_id: int):
        self._vendor_id = vendor_id

    @product_id.setter
    def product_id(self, product_id: int):
        self._product_id = product_id

    def use(self) -> None:
        """ """
        if self._device:
            self._hid_device = hid.device()
            try:
                self._hid_device.open(self._vendor_id, self._product_id)
                #self._hid_device.set_nonblocking(1)
                self._is_open = True
            except OSError as ex:
                usb_logger.error(str(ex))
                self._is_open = False
            usb_logger.info(f"Using device: \n{self._device}")

    def release(self) -> None:
        """ """
        if self._hid_device:
            self._hid_device.close()

    def read(self) -> bytes:
        """ """
        response = b""
        if self._hid_device:
            response = bytes(self._hid_device.read(64))
            usb_logger.debug(f"read {len(response)} bytes: {response.hex()}")
        return response

    def write(self, data: bytes):
        """ """
        if self._hid_device:
            logger.debug(f"write {len(data)} bytes: {data.hex()}")
            write_count = self._hid_device.write(data)
            if write_count != len(data):
                usb_logger.warning(
                    f"{write_count} bytes instead of {len(data)} were written"
                )

def get_all_known_knx_usb_devices(vendor_id: int, product_id: int) -> list[USBDevice]:
    """ """
    device_list = []
    hid_device_list = hid.enumerate()
    specific_interface = vendor_id != 0 and product_id != 0
    if specific_interface:
        KNOWN_DEVICES.append((vendor_id, product_id))
    hid_device_list = list(
        filter(
            lambda device: bool(
                (device.get("vendor_id", 0), device.get("product_id", 0)) in KNOWN_DEVICES
            ),
            hid_device_list,
        )
    )
    if specific_interface:
        hid_device_list = list(
            filter(
                lambda device: bool(
                    (device.get("vendor_id", 0), device.get("product_id", 0)) in [(vendor_id, product_id)]
                ),
                hid_device_list,
            )
        )
    device_list = _create_usb_device_list(hid_device_list)
    return device_list


def _get_usb_backend():
    """ """
    backend = None
    if platform.system() == "Windows":
        # TODO: here we loaded libusb dll and use it as backend
        #       libusb as backend on windows supports almost no function (install WinUSB with Zadig?)
        import os

        import usb.backend.libusb1

        dll_location = os.environ.get(
            "XKNX_LIBUSB", "C:\\Windows\\System32\\libusb-1.0.dll"
        )
        try:
            backend = usb.backend.libusb1.get_backend(
                find_library=lambda x: f"{dll_location}"
            )
        except usb.core.NoBackendError as ex:
            logger.error(str(ex))
        if not backend:
            usb_logger.error(
                "No USB backend found. Set XKNX_LIBUSB environment variable pointing to libusb-1.0.dll or install it to C:\\Windows\\System32"
            )
    return backend


def _log_usb_device(index: int, device: dict):
    """ """
    usb_logger.info(f"device {index}")
    usb_logger.info(
        f"    manufacturer  : {device.get('manufacturer_string', '')} (idVendor: {device.get('vendor_id', 0):#0{6}x})"
    )
    usb_logger.info(
        f"    product       : {device.get('product_string', '')} (idProduct: {device.get('product_id'):#0{6}x})"
    )
    usb_logger.info(f"    serial_number : {device.get('serial_number', '')}")


def _create_usb_device(device: dict) -> USBDevice:
    """ """
    usb_device = USBDevice()
    usb_device.device = device
    usb_device.manufacturer = device.get("manufacturer_string", "")
    usb_device.product = device.get("product_string", "")
    usb_device.serial_number = device.get("serial_number", "")
    usb_device.vendor_id = device.get("vendor_id", 0)
    usb_device.product_id = device.get("product_id", 0)
    return usb_device


def _create_usb_device_list(usb_device_list: dict) -> list[USBDevice]:
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
