from examples.usb.knx_hid_frame import KNXHIDFrame

import usb_util
from knx_hid_datatypes import PacketType


def get_knx_frame() -> bytes:
    """ """
    data = (
        b"\x01\x13\x09\x00\x08" \
        b"\x00\x01\x0f\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    return bytes(data)


def pyusb():
    """ """
    usb_devices = usb_util.get_all_hid_devices()  # searches for potential KNX interfaces
    usb_device = usb_util.get_first_matching_usb_device(  # search device by providing vendor and product id
        usb_util.USBKNXInterfaceData(usb_util.USBVendorId.SIEMENS_OCI702, usb_util.USBProductId.SIEMENS_OCI702))
    usb_device.use()  # claims the interface and sets up the endpoints for read/write
    usb_device.write(get_knx_frame())
    print(str(usb_device.active_configuration))


if __name__ == "__main__":
    pyusb()
    frame = get_knx_frame()
    parsed_frame = KNXHIDFrame.from_bytes(frame)
    constructed_bytes = parsed_frame.to_knx()
    assert constructed_bytes == frame
    if parsed_frame.is_valid:
        while parsed_frame.report_header.packet_info.packet_type not in [PacketType.START_AND_END, PacketType.PARTIAL_AND_END, PacketType.END]:
            # continue receiving partial packets
            frame = get_knx_frame()
            parsed_frame = KNXHIDFrame.from_bytes(frame, partial=True)
