"""Tests for KNX USB interfaces with EMI1 or EMI2 instead of cEMI."""

import asyncio
from collections.abc import Callable
from unittest.mock import Mock

import pytest

from xknx import XKNX
from xknx.cemi import CEMIFrame, CEMILData, CEMIMessageCode
from xknx.dpt import DPTBinary
from xknx.exceptions import CommunicationError, ConversionError
from xknx.io.usb import USBTunnel, emi, tunnel as usb_tunnel
from xknx.io.usb.const import EMIID, DeviceFeature
from xknx.io.usb.emi import EMILayer
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import GroupValueWrite

from .conftest import FakeHIDModule

GROUP_WRITE = CEMIFrame(
    code=CEMIMessageCode.L_DATA_REQ,
    data=CEMILData.init_from_telegram(
        Telegram(
            destination_address=GroupAddress("1/4/0"),
            payload=GroupValueWrite(DPTBinary(1)),
        ),
        src_addr=IndividualAddress("1.1.5"),
    ),
)


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


def _tunnel(cemi_received: Mock, **kwargs: object) -> USBTunnel:
    return USBTunnel(
        XKNX(),
        cemi_received_callback=cemi_received,
        auto_reconnect=False,
        **kwargs,  # type: ignore[arg-type]
    )


class TestEMI2:
    """An interface with EMI2 only (BCU 2)."""

    async def test_connect_send_receive_disconnect(
        self, fake_hid: FakeHIDModule
    ) -> None:
        """Test the data link layer of an EMI2 interface, in cEMI."""
        interface = fake_hid.interface
        interface.features[DeviceFeature.SUPPORTED_EMI_TYPE] = b"\x00\x02"
        received = Mock()
        tunnel = _tunnel(received)
        await tunnel.connect()
        assert interface.features[DeviceFeature.ACTIVE_EMI_TYPE] == b"\x02"
        assert interface.pei_switch == bytes.fromhex("00183456780a")
        assert tunnel.info is not None
        assert tunnel.info.emi_type is EMIID.EMI2
        assert tunnel.info.individual_address == IndividualAddress("1.1.5")
        assert tunnel.info.max_apdu_length == 15
        assert tunnel.xknx.current_address == IndividualAddress("1.1.5")

        await tunnel.send_cemi(GROUP_WRITE)
        # priority low, source left to the interface, AT group, hop count 6, length 1
        assert interface.written_cemi()[-1] == bytes.fromhex("110c00000c00e10081")
        await _until(lambda: received.call_count == 1)
        assert received.call_args.args[0] == bytes.fromhex("2e00bce011050c00010081")

        # an indication from the bus
        interface.send_emi(EMIID.EMI2, bytes.fromhex("29bc102f0012e1008034"))
        await _until(lambda: received.call_count == 2)
        assert received.call_args.args[0] == bytes.fromhex("2900bce0102f001201008034")

        await tunnel.disconnect()
        assert interface.pei_switch == bytes.fromhex("1e123456789a")

    async def test_busmonitor(self, fake_hid: FakeHIDModule) -> None:
        """Test the bus monitor mode of an EMI2 interface, in cEMI."""
        interface = fake_hid.interface
        interface.features[DeviceFeature.SUPPORTED_EMI_TYPE] = b"\x00\x02"
        received = Mock()
        tunnel = _tunnel(received, busmonitor=True)
        await tunnel.connect()
        assert interface.pei_switch == bytes.fromhex("90183456780a")
        interface.send_emi(EMIID.EMI2, bytes.fromhex("2b03d70abc102f0016e300800d4347"))
        await _until(lambda: received.call_count == 1)
        assert received.call_args.args[0] == bytes.fromhex(
            "2b070301030402d70abc102f0016e300800d4347"
        )
        with pytest.raises(CommunicationError, match="bus monitor mode"):
            await tunnel.send_cemi(GROUP_WRITE)
        await tunnel.disconnect()

    async def test_only_standard_frames(self, fake_hid: FakeHIDModule) -> None:
        """Test what EMI can't carry is refused."""
        fake_hid.interface.features[DeviceFeature.SUPPORTED_EMI_TYPE] = b"\x00\x02"
        tunnel = _tunnel(Mock())
        await tunnel.connect()
        with pytest.raises(CommunicationError, match="EMI2 interface"):
            await tunnel.send_cemi(
                CEMIFrame(code=CEMIMessageCode.M_RESET_REQ, data=None)
            )
        await tunnel.disconnect()


class TestEMI1:
    """An interface with EMI1 only (BCU 1)."""

    async def test_connect_send_receive_disconnect(
        self, fake_hid: FakeHIDModule
    ) -> None:
        """Test the data link layer of an EMI1 interface, in cEMI."""
        interface = fake_hid.interface
        interface.features[DeviceFeature.SUPPORTED_EMI_TYPE] = b"\x00\x01"
        received = Mock()
        tunnel = _tunnel(received)
        await tunnel.connect()
        assert interface.features[DeviceFeature.ACTIVE_EMI_TYPE] == b"\x01"
        # system status "data link layer", read back
        assert interface.written_cemi()[:2] == [
            bytes.fromhex("4601006012"),
            bytes.fromhex("4c010060"),
        ]
        assert interface.memory[0x0060] == b"\x12"
        assert tunnel.info is not None
        assert tunnel.info.emi_type is EMIID.EMI1
        assert tunnel.info.individual_address == IndividualAddress("1.1.5")

        await tunnel.send_cemi(GROUP_WRITE)
        await _until(lambda: received.call_count == 1)
        assert received.call_args.args[0] == bytes.fromhex("2e00bce011050c00010081")
        interface.send_emi(EMIID.EMI1, bytes.fromhex("49bc102f0012e1008034"))
        await _until(lambda: received.call_count == 2)
        assert received.call_args.args[0][0] == 0x29

        await tunnel.disconnect()
        # the default system status again
        assert interface.memory[0x0060] == b"\x1e"

    async def test_busmonitor(self, fake_hid: FakeHIDModule) -> None:
        """Test EMI1's L_Busmon.ind, which has the message code of L_Data.ind."""
        interface = fake_hid.interface
        interface.features[DeviceFeature.SUPPORTED_EMI_TYPE] = b"\x00\x01"
        received = Mock()
        tunnel = _tunnel(received, busmonitor=True)
        await tunnel.connect()
        assert interface.memory[0x0060] == b"\x90"
        interface.send_emi(EMIID.EMI1, bytes.fromhex("4903d70acc"))
        await _until(lambda: received.call_count == 1)
        assert received.call_args.args[0] == bytes.fromhex("2b070301030402d70acc")
        await tunnel.disconnect()

    async def test_layer_not_switched(self, fake_hid: FakeHIDModule) -> None:
        """Test an interface that doesn't take the system status."""
        interface = fake_hid.interface
        interface.features[DeviceFeature.SUPPORTED_EMI_TYPE] = b"\x00\x01"
        interface.accepts_memory_writes = False
        with pytest.raises(
            CommunicationError, match="did not switch to data_link_layer"
        ):
            await _tunnel(Mock()).connect()

    async def test_individual_address_unreadable(self, fake_hid: FakeHIDModule) -> None:
        """Test an interface that doesn't answer the read of its individual address."""
        interface = fake_hid.interface
        interface.features[DeviceFeature.SUPPORTED_EMI_TYPE] = b"\x00\x01"
        handle = interface._handle_emi

        def no_address(emi_id: EMIID, raw: bytes) -> None:
            if raw[:1] == b"\x4c" and raw[2:4] == b"\x01\x17":
                return
            handle(emi_id, raw)

        interface._handle_emi = no_address  # type: ignore[method-assign]
        tunnel = _tunnel(Mock())
        await tunnel.connect()
        assert tunnel.info is not None
        assert tunnel.info.individual_address == IndividualAddress(0)
        # a failing switch back to normal mode doesn't stop the disconnect
        interface.write_result = -1
        await tunnel.disconnect()
        assert fake_hid.closed == 1


class TestPreferredEMIType:
    """The EMI type chosen from several."""

    async def test_emi2_over_emi1(self, fake_hid: FakeHIDModule) -> None:
        """Test EMI2 is preferred to EMI1 and verified as the active one."""
        interface = fake_hid.interface
        interface.features[DeviceFeature.SUPPORTED_EMI_TYPE] = b"\x00\x03"
        tunnel = _tunnel(Mock())
        await tunnel.connect()
        assert tunnel.info is not None and tunnel.info.emi_type is EMIID.EMI2
        await tunnel.disconnect()
        interface.accepts_emi_set = False
        interface.features[DeviceFeature.ACTIVE_EMI_TYPE] = b"\x01"
        with pytest.raises(CommunicationError, match="did not activate EMI2"):
            await _tunnel(Mock()).connect()


class TestConversion:
    """Converting between cEMI and EMI1/EMI2."""

    def test_l_data_req(self) -> None:
        """Test cEMI L_Data.req that EMI can't carry."""
        with pytest.raises(ConversionError, match=r"Only L_Data\.req"):
            emi.l_data_req_from_cemi(b"\xf1")
        with pytest.raises(ConversionError, match="Invalid"):
            emi.l_data_req_from_cemi(bytes.fromhex("110000"))
        # extended frame
        with pytest.raises(ConversionError, match="standard frames"):
            emi.l_data_req_from_cemi(bytes.fromhex("11003ce011050c00010081"))
        # with additional information
        assert emi.l_data_req_from_cemi(
            bytes.fromhex("1103030100bce011050c00010081")
        ) == bytes.fromhex("110c00000c00e10081")

    def test_to_cemi(self) -> None:
        """Test EMI messages that aren't converted."""
        assert emi.to_cemi(EMIID.EMI2, b"", busmonitor=False) is None
        assert emi.to_cemi(EMIID.EMI2, b"\x29\xbc", busmonitor=False) is None
        assert emi.to_cemi(EMIID.EMI2, b"\x2b\x00", busmonitor=True) is None
        assert (
            emi.to_cemi(EMIID.EMI2, b"\x2b\x00\x00\x00\xcc", busmonitor=False) is None
        )
        assert emi.to_cemi(EMIID.EMI1, b"\x55", busmonitor=False) is None

    def test_pc_get_value_con(self) -> None:
        """Test reading PC_Get_Value.con."""
        assert emi.parse_pc_get_value_con(
            EMIID.EMI2, bytes.fromhex("ab0201171105")
        ) == (
            0x0117,
            b"\x11\x05",
        )
        assert (
            emi.parse_pc_get_value_con(EMIID.EMI1, bytes.fromhex("ab0201171105"))
            is None
        )
        assert emi.parse_pc_get_value_con(EMIID.EMI2, b"\xab\x01") is None

    def test_switch_messages(self) -> None:
        """Test the layer switching messages of the specification's examples."""
        assert emi.pei_switch(EMILayer.DATA_LINK_LAYER) == bytes.fromhex(
            "a900183456780a"
        )
        assert emi.pc_set_value(EMIID.EMI1, 0x0060, b"\x90") == bytes.fromhex(
            "4601006090"
        )
        assert emi.pc_get_value(EMIID.EMI2, 0x0117, 2) == bytes.fromhex("ac020117")
