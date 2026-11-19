"""Tests for KNX RF through KNX USB RF interfaces."""

import asyncio
from collections.abc import Callable
import logging
from unittest.mock import Mock

import pytest

from xknx import XKNX
from xknx.exceptions import CommunicationError
from xknx.io.usb import (
    RFMediumInfo,
    RFSignalStrength,
    USBTunnel,
    rf_medium_info,
    tunnel as usb_tunnel,
)
from xknx.io.usb.const import DeviceFeature
from xknx.io.usb.rf import medium_of_mask_version, with_rf_medium_info
from xknx.knxip.knxip_enum import KNXMedium
from xknx.telegram import IndividualAddress

from .conftest import FakeHIDModule
from .tunnel_test import GROUP_WRITE

DOMAIN_ADDRESS = bytes.fromhex("00fa12345678")
# an L_Data.ind of a group write 1/2/3 from 1.1.5 without additional information
GROUP_WRITE_IND = bytes.fromhex("2900bce011050a0301 0081")
# the same with RF medium information: strong signal, battery ok, Domain Address, LFN 3
RF_GROUP_WRITE_IND = bytes.fromhex("290a 0208 32 00fa12345678 03 bce011050a0301 0081")
VOID_RF_INFO = bytes.fromhex("0208 02 000000000000 ff")


async def _until(condition: Callable[[], bool], timeout: float = 2.0) -> None:
    """Wait for something done by the reader thread - it can't set an asyncio.Event."""
    async with asyncio.timeout(timeout):
        while not condition():  # noqa: ASYNC110
            await asyncio.sleep(0.01)


@pytest.fixture(autouse=True)
def short_timeouts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Don't wait long for answers the fake interface doesn't give."""
    monkeypatch.setattr(usb_tunnel, "DEVICE_FEATURE_GET_TIMEOUT", 0.2)
    monkeypatch.setattr(usb_tunnel, "LOCAL_MANAGEMENT_TIMEOUT", 0.2)


class TestRFMediumInfo:
    """Test the RF medium information of cEMI frames."""

    def test_round_trip(self) -> None:
        """Test every field is kept."""
        info = RFMediumInfo(
            serial_number_or_domain_address=DOMAIN_ADDRESS,
            frame_number=5,
            route_last=True,
            signal_strength=RFSignalStrength.MEDIUM,
            retransmitter_signal_strength=RFSignalStrength.WEAK,
            battery_ok=False,
            unidirectional=True,
        )
        raw = info.to_knx()
        assert raw == bytes.fromhex("0208a5") + DOMAIN_ADDRESS + b"\x05"
        assert RFMediumInfo.from_knx(raw[2:]) == info

    def test_void(self) -> None:
        """Test the information the interface completes on sending."""
        assert RFMediumInfo().to_knx() == VOID_RF_INFO

    def test_wrong_length(self) -> None:
        """Test the information has 8 octets."""
        with pytest.raises(ValueError, match="8 octets"):
            RFMediumInfo.from_knx(bytes(7))

    def test_from_frame(self) -> None:
        """Test reading the information of a received frame."""
        assert rf_medium_info(RF_GROUP_WRITE_IND) == RFMediumInfo(
            serial_number_or_domain_address=DOMAIN_ADDRESS,
            frame_number=3,
            signal_strength=RFSignalStrength.STRONG,
        )
        assert rf_medium_info(GROUP_WRITE_IND) is None
        # other information before it
        assert rf_medium_info(
            bytes.fromhex("290d 030100 0208 32 00fa12345678 03 bce011050a0301 0081")
        ) == rf_medium_info(RF_GROUP_WRITE_IND)
        # no L_Data frame, too short, an information longer than its frame
        assert rf_medium_info(bytes.fromhex("fb000001391001 10")) is None
        assert rf_medium_info(b"\x29") is None
        assert rf_medium_info(bytes.fromhex("2905 0208 32")) is None
        assert rf_medium_info(bytes.fromhex("2903 0208 32")) is None

    def test_added_to_requests(self) -> None:
        """Test a void information is added to an L_Data.req without one."""
        request = GROUP_WRITE.to_knx()
        assert request[1] == 0
        assert with_rf_medium_info(request) == (
            bytes((0x11, len(VOID_RF_INFO))) + VOID_RF_INFO + request[2:]
        )
        # after the information it already has
        with_info = bytes.fromhex("1103 030100") + request[2:]
        assert with_rf_medium_info(with_info) == (
            bytes.fromhex("110d 030100") + VOID_RF_INFO + request[2:]
        )
        # a frame with RF medium information is kept as it is
        with_rf = with_rf_medium_info(request)
        assert with_rf_medium_info(with_rf) == with_rf
        # other frames are not changed
        assert with_rf_medium_info(RF_GROUP_WRITE_IND) == RF_GROUP_WRITE_IND
        assert with_rf_medium_info(b"") == b""
        assert with_rf_medium_info(bytes.fromhex("1105 0208")) == bytes.fromhex(
            "1105 0208"
        )

    @pytest.mark.parametrize(
        ("mask_version", "medium"),
        [
            (0x2311, KNXMedium.RF),
            (0x2705, KNXMedium.RF),
            (0x07B0, KNXMedium.TP1),
            (0x0310, KNXMedium.TP1),
            (0x1310, KNXMedium.PL110),
            (0x5705, KNXMedium.KNX_IP),
            (0x9999, KNXMedium.TP1),
            (None, KNXMedium.TP1),
        ],
    )
    def test_medium_of_mask_version(
        self, mask_version: int | None, medium: KNXMedium
    ) -> None:
        """Test the medium comes from the Medium Type digit of the mask version."""
        assert medium_of_mask_version(mask_version) is medium


class TestRFInterface:
    """Test USBTunnel with a simulated KNX USB RF interface (mask 2311h)."""

    def setup_method(self) -> None:
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.xknx = XKNX()
        self.cemi_received = Mock()

    def tunnel(self, rf_domain_address: bytes | None = None) -> USBTunnel:
        """Create a tunnel."""
        return USBTunnel(
            self.xknx,
            cemi_received_callback=self.cemi_received,
            auto_reconnect=False,
            rf_domain_address=rf_domain_address,
        )

    @staticmethod
    def rf_interface(fake_hid: FakeHIDModule) -> None:
        """Make the simulated interface an RF interface."""
        interface = fake_hid.interface
        interface.features[DeviceFeature.DEVICE_DESCRIPTOR_TYPE_0] = b"\x23\x11"
        interface.properties[(19, 56)] = DOMAIN_ADDRESS

    async def test_connect_send_and_receive(self, fake_hid: FakeHIDModule) -> None:
        """Test the Domain Address is read and frames are sent with RF medium information."""
        self.rf_interface(fake_hid)
        tunnel = self.tunnel()
        await tunnel.connect()
        interface = fake_hid.interface
        # PID_RF_DOMAIN_ADDRESS, then PID_RF_MULTI_TYPE of the RF Medium Object, after the
        # other properties
        assert interface.written_cemi()[-2:] == [
            bytes.fromhex("fc001301381001"),
            bytes.fromhex("fc001301331001"),
        ]
        info = tunnel.info
        assert info is not None
        assert info.medium is KNXMedium.RF
        assert info.rf_domain_address == DOMAIN_ADDRESS
        # a KNX RF Ready interface has no PID_RF_MULTI_TYPE
        assert not info.rf_multi

        await tunnel.send_cemi(GROUP_WRITE)
        request = GROUP_WRITE.to_knx()
        sent = interface.written_cemi()[-1]
        assert sent == bytes((0x11, len(VOID_RF_INFO))) + VOID_RF_INFO + request[2:]
        # the confirmation, with the information, is passed on
        await _until(lambda: self.cemi_received.call_count == 1)
        confirmation = self.cemi_received.call_args.args[0]
        assert rf_medium_info(confirmation) == RFMediumInfo()
        assert self.xknx.current_address == IndividualAddress("1.0.2")

        interface.send_cemi(RF_GROUP_WRITE_IND)
        await _until(lambda: self.cemi_received.call_count == 2)
        assert self.cemi_received.call_args.args[0] == RF_GROUP_WRITE_IND
        await tunnel.disconnect()

    async def test_domain_address_in_the_device_object(
        self, fake_hid: FakeHIDModule
    ) -> None:
        """Test the Device Object is read when the RF Medium Object gives none."""
        self.rf_interface(fake_hid)
        interface = fake_hid.interface
        interface.properties[(19, 56)] = bytes(5)
        interface.properties[(0, 82)] = DOMAIN_ADDRESS
        tunnel = self.tunnel()
        await tunnel.connect()
        assert interface.written_cemi()[-3:-1] == [
            bytes.fromhex("fc001301381001"),
            bytes.fromhex("fc000001521001"),
        ]
        assert tunnel.info is not None
        assert tunnel.info.rf_domain_address == DOMAIN_ADDRESS
        await tunnel.disconnect()

    @pytest.mark.parametrize(("value", "rf_multi"), [(b"\x01", True), (b"\x00", False)])
    async def test_rf_multi_type(
        self, fake_hid: FakeHIDModule, value: bytes, rf_multi: bool
    ) -> None:
        """Test whether an RF interface operates as a KNX RF Multi device."""
        self.rf_interface(fake_hid)
        fake_hid.interface.properties[(19, 51)] = value
        tunnel = self.tunnel()
        await tunnel.connect()
        assert tunnel.info is not None
        assert tunnel.info.rf_multi is rf_multi
        await tunnel.disconnect()

    async def test_domain_address_unknown(
        self, fake_hid: FakeHIDModule, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test an RF interface whose Domain Address can't be read still connects."""
        self.rf_interface(fake_hid)
        del fake_hid.interface.properties[(19, 56)]
        tunnel = self.tunnel()
        with caplog.at_level(logging.WARNING, logger="xknx.log"):
            await tunnel.connect()
        assert "Could not read the RF Domain Address" in caplog.text
        assert tunnel.info is not None
        assert tunnel.info.medium is KNXMedium.RF
        assert tunnel.info.rf_domain_address is None
        # frames are sent with the interface's own Domain Address
        await tunnel.send_cemi(GROUP_WRITE)
        assert fake_hid.interface.written_cemi()[-1][2:12] == VOID_RF_INFO
        await tunnel.disconnect()

    async def test_tp1_interface(self, fake_hid: FakeHIDModule) -> None:
        """Test a TP1 interface sends frames as they are and reads no Domain Address."""
        tunnel = self.tunnel()
        await tunnel.connect()
        assert tunnel.info is not None
        assert tunnel.info.medium is KNXMedium.TP1
        assert tunnel.info.rf_domain_address is None
        await tunnel.send_cemi(GROUP_WRITE)
        assert fake_hid.interface.written_cemi()[-1] == GROUP_WRITE.to_knx()
        assert not any(
            frame.startswith(bytes.fromhex("fc0013"))
            for frame in fake_hid.interface.written_cemi()
        )
        await tunnel.disconnect()


class TestRFDomainAddressWrite:
    """Test setting the Domain Address of a KNX USB RF interface on connect."""

    NEW_DOMAIN_ADDRESS = bytes.fromhex("00fa00000042")

    def tunnel(self, xknx: XKNX) -> USBTunnel:
        """Create a tunnel that sets the Domain Address."""
        return USBTunnel(
            xknx,
            cemi_received_callback=Mock(),
            auto_reconnect=False,
            rf_domain_address=self.NEW_DOMAIN_ADDRESS,
        )

    async def test_set(
        self, fake_hid: FakeHIDModule, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test another Domain Address is written to the RF Medium Object."""
        TestRFInterface.rf_interface(fake_hid)
        interface = fake_hid.interface
        tunnel = self.tunnel(XKNX())
        with caplog.at_level(logging.INFO, logger="xknx.log"):
            await tunnel.connect()
        assert interface.written_cemi()[-1] == (
            bytes.fromhex("f6001301381001") + self.NEW_DOMAIN_ADDRESS
        )
        assert interface.properties[(19, 56)] == self.NEW_DOMAIN_ADDRESS
        assert tunnel.info is not None
        assert tunnel.info.rf_domain_address == self.NEW_DOMAIN_ADDRESS
        assert "from 00fa12345678 to 00fa00000042" in caplog.text
        await tunnel.disconnect()

    async def test_same_one_not_written(self, fake_hid: FakeHIDModule) -> None:
        """Test the Domain Address the interface has already is not written again."""
        TestRFInterface.rf_interface(fake_hid)
        interface = fake_hid.interface
        interface.properties[(19, 56)] = self.NEW_DOMAIN_ADDRESS
        tunnel = self.tunnel(XKNX())
        await tunnel.connect()
        assert not any(
            frame[0] == 0xF6 and frame[2] == 0x13 for frame in interface.written_cemi()
        )
        await tunnel.disconnect()

    async def test_unknown_one_written(
        self, fake_hid: FakeHIDModule, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test a Domain Address is written when the interface's own can't be read."""
        TestRFInterface.rf_interface(fake_hid)
        del fake_hid.interface.properties[(19, 56)]
        tunnel = self.tunnel(XKNX())
        with caplog.at_level(logging.INFO, logger="xknx.log"):
            await tunnel.connect()
        assert fake_hid.interface.properties[(19, 56)] == self.NEW_DOMAIN_ADDRESS
        assert "from unknown to 00fa00000042" in caplog.text
        await tunnel.disconnect()

    async def test_refused(self, fake_hid: FakeHIDModule) -> None:
        """Test the connect fails when the interface refuses the Domain Address."""
        TestRFInterface.rf_interface(fake_hid)
        fake_hid.interface.refused_writes[(19, 56)] = 0x0B
        tunnel = self.tunnel(XKNX())
        with pytest.raises(
            CommunicationError, match="Could not set the RF Domain Address"
        ):
            await tunnel.connect()
        assert fake_hid.interface.properties[(19, 56)] == DOMAIN_ADDRESS

    async def test_ignored_for_tp1(self, fake_hid: FakeHIDModule) -> None:
        """Test a TP1 interface gets no Domain Address."""
        tunnel = self.tunnel(XKNX())
        await tunnel.connect()
        assert (19, 56) not in fake_hid.interface.properties
        assert tunnel.info is not None
        assert tunnel.info.rf_domain_address is None
        await tunnel.disconnect()
