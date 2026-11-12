"""Tests for KNX USB interfaces with EMI1 or EMI2 instead of cEMI."""

import asyncio
from collections.abc import Callable
import logging
from pathlib import Path
from unittest.mock import Mock

import pytest

from xknx import XKNX
from xknx.cemi import CEMIFrame, CEMILData, CEMIMessageCode
from xknx.dpt import DPTBinary
from xknx.exceptions import CommunicationError, ConversionError
from xknx.io.usb import USBTunnel, emi, tunnel as usb_tunnel
from xknx.io.usb.const import EMIID, DeviceFeature
from xknx.io.usb.emi import EMILayer
from xknx.secure.keyring import sync_load_keyring
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import GroupValueWrite

from .conftest import FakeHIDModule, FakeInterface, make_emi_interface

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
USB_KEYRING = (
    Path(__file__).parents[2] / "secure_tests" / "resources" / "DataSecure_usb.knxkeys"
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


def _tunnel(
    cemi_received: Mock, xknx: XKNX | None = None, **kwargs: object
) -> USBTunnel:
    return USBTunnel(
        xknx or XKNX(),
        cemi_received_callback=cemi_received,
        auto_reconnect=False,
        **kwargs,  # type: ignore[arg-type]
    )


def _tunnelled(interface: FakeInterface) -> list[str]:
    """Return the EMI messages the host sent, in hex."""
    return [raw.hex() for raw in interface.written_cemi()]


class TestEMI2:
    """An interface with EMI2 only (BCU 2)."""

    async def test_connect_send_receive_disconnect(
        self, fake_hid: FakeHIDModule
    ) -> None:
        """Test the data link layer of an EMI2 interface, in cEMI."""
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI2, 0x0020)
        received = Mock()
        tunnel = _tunnel(received)
        await tunnel.connect()
        assert interface.features[DeviceFeature.ACTIVE_EMI_TYPE] == b"\x02"
        # Figure 2's data link layer, then the individual address of a BCU 2
        assert _tunnelled(interface) == ["a900183456780a", "ac020117"]
        assert tunnel.info is not None
        assert tunnel.info.emi_type is EMIID.EMI2
        assert tunnel.info.mask_version == 0x0020
        assert tunnel.info.individual_address == IndividualAddress("1.1.5")
        assert tunnel.info.max_apdu_length == 15
        assert tunnel.xknx.current_address == IndividualAddress("1.1.5")

        await tunnel.send_cemi(GROUP_WRITE)
        # priority low, source left to the interface, AT group, hop count 6, length 1
        assert interface.written_cemi()[-1] == bytes.fromhex("110c00000c00e10081")
        await _until(lambda: received.call_count == 1)
        # the "x" bits of the control field dropped, the interface's own address
        # as source of the confirmation
        assert received.call_args.args[0] == bytes.fromhex("2e009ce011050c00010081")

        # a message that isn't converted, then an indication from the bus
        interface.send_emi(EMIID.EMI2, bytes.fromhex("5500"))
        interface.send_emi(EMIID.EMI2, bytes.fromhex("29bc102f0012e1008034"))
        await _until(lambda: received.call_count == 2)
        assert received.call_args.args[0] == bytes.fromhex("2900bce0102f001201008034")

        await tunnel.disconnect()
        # Figure 2's normal mode, the "system status" unchanged
        assert interface.pei_switch == bytes.fromhex("00123456789a")

    async def test_busmonitor(self, fake_hid: FakeHIDModule) -> None:
        """Test the bus monitor mode of an EMI2 interface, in cEMI."""
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI2, 0x0020)
        received = Mock()
        tunnel = _tunnel(received, busmonitor=True)
        await tunnel.connect()
        # the "system status" is read before the bus monitor mode changes it
        assert _tunnelled(interface)[:2] == ["ac010060", "a990183456780a"]
        assert interface.pei_switch == bytes.fromhex("90183456780a")
        interface.send_emi(EMIID.EMI2, bytes.fromhex("2b03d70abc102f0016e300800d4347"))
        await _until(lambda: received.call_count == 1)
        assert received.call_args.args[0] == bytes.fromhex(
            "2b070301030402d70abc102f0016e300800d4347"
        )
        with pytest.raises(CommunicationError, match="bus monitor mode"):
            await tunnel.send_cemi(GROUP_WRITE)
        await tunnel.disconnect()
        # the "system status" of before
        assert interface.pei_switch == bytes.fromhex("1e123456789a")

    async def test_busmonitor_left_by_another_client(
        self, fake_hid: FakeHIDModule
    ) -> None:
        """Test leaving the bus monitor mode an interface was already in."""
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI2, 0x0020)
        interface.memory[0x0060] = b"\x90"
        tunnel = _tunnel(Mock(), busmonitor=True)
        await tunnel.connect()
        await tunnel.disconnect()
        # every layer, the PEI and the user program
        assert interface.pei_switch == bytes.fromhex("be123456789a")

    async def test_only_standard_frames(self, fake_hid: FakeHIDModule) -> None:
        """Test what EMI can't carry is refused."""
        make_emi_interface(fake_hid.interface, EMIID.EMI2, 0x0020)
        tunnel = _tunnel(Mock())
        await tunnel.connect()
        with pytest.raises(CommunicationError, match="EMI2 interface"):
            await tunnel.send_cemi(
                CEMIFrame(code=CEMIMessageCode.M_RESET_REQ, data=None)
            )
        await tunnel.disconnect()

    async def test_data_secure_warning(
        self, fake_hid: FakeHIDModule, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test Data Secure with an EMI2 interface is warned about."""
        make_emi_interface(fake_hid.interface, EMIID.EMI2, 0x0020)
        keyring = sync_load_keyring(USB_KEYRING, "test")
        xknx = XKNX()
        xknx.cemi_handler.data_secure_init(keyring)
        assert xknx.cemi_handler.data_secure is not None
        tunnel = _tunnel(Mock(), xknx=xknx, keyring=keyring)
        with caplog.at_level(logging.WARNING, logger="xknx.log"):
            await tunnel.connect()
        assert "supports EMI2 only: it can't send or receive extended frames" in (
            caplog.text
        )
        # 1.1.5 is not the keyring's USB interface 1.0.12
        assert "1.1.5, which is no interface of the keyring" in caplog.text
        assert "USB interfaces of the keyring: 1.0.12" in caplog.text
        await tunnel.disconnect()


class TestEMI1:
    """An interface with EMI1 only (BCU 1)."""

    async def test_connect_send_receive_disconnect(
        self, fake_hid: FakeHIDModule
    ) -> None:
        """Test the data link layer of an EMI1 interface, in cEMI."""
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI1, 0x0012)
        received = Mock()
        tunnel = _tunnel(received)
        await tunnel.connect()
        assert interface.features[DeviceFeature.ACTIVE_EMI_TYPE] == b"\x01"
        # system status read, set to "data link layer", read back; individual address
        assert _tunnelled(interface) == [
            "4c010060",
            "4601006012",
            "4c010060",
            "4c020117",
        ]
        assert interface.memory[0x0060] == b"\x12"
        assert tunnel.info is not None
        assert tunnel.info.emi_type is EMIID.EMI1
        assert tunnel.info.individual_address == IndividualAddress("1.1.5")

        await tunnel.send_cemi(GROUP_WRITE)
        await _until(lambda: received.call_count == 1)
        assert received.call_args.args[0] == bytes.fromhex("2e009ce011050c00010081")
        interface.send_emi(EMIID.EMI1, bytes.fromhex("49bc102f0012e1008034"))
        await _until(lambda: received.call_count == 2)
        assert received.call_args.args[0][0] == 0x29

        await tunnel.disconnect()
        # the system status of before
        assert interface.memory[0x0060] == b"\x1e"

    async def test_busmonitor(self, fake_hid: FakeHIDModule) -> None:
        """Test EMI1's L_Busmon.ind, which has the message code of L_Data.ind."""
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI1, 0x0012)
        received = Mock()
        tunnel = _tunnel(received, busmonitor=True)
        await tunnel.connect()
        assert interface.memory[0x0060] == b"\x90"
        interface.send_emi(EMIID.EMI1, bytes.fromhex("4903d70acc"))
        await _until(lambda: received.call_count == 1)
        assert received.call_args.args[0] == bytes.fromhex("2b070301030402d70acc")
        await tunnel.disconnect()
        assert interface.memory[0x0060] == b"\x1e"

    @pytest.mark.parametrize(
        ("before", "after"),
        [
            # left in the data link layer by another client
            (b"\x12", b"\xbe"),
            # a user program that doesn't run
            (b"\x1e", b"\x1e"),
            # every layer and the user program
            (b"\xbe", b"\xbe"),
        ],
    )
    async def test_normal_mode(
        self, fake_hid: FakeHIDModule, before: bytes, after: bytes
    ) -> None:
        """Test the system status the interface is switched back to."""
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI1, 0x0012)
        interface.memory[0x0060] = before
        tunnel = _tunnel(Mock())
        await tunnel.connect()
        await tunnel.disconnect()
        assert interface.memory[0x0060] == after

    async def test_system_status_unreadable(self, fake_hid: FakeHIDModule) -> None:
        """Test switching back without the system status of before."""
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI1, 0x0012)
        handle = interface._handle_emi
        reads: list[bytes] = []

        def first_read_lost(emi_id: EMIID, raw: bytes) -> None:
            if raw.hex() == "4c010060" and not reads:
                reads.append(raw)
                return
            handle(emi_id, raw)

        interface._handle_emi = first_read_lost  # type: ignore[method-assign]
        tunnel = _tunnel(Mock())
        await tunnel.connect()
        await tunnel.disconnect()
        assert interface.memory[0x0060] == b"\xbe"

    async def test_layer_not_switched(self, fake_hid: FakeHIDModule) -> None:
        """Test an interface that doesn't take the system status."""
        make_emi_interface(fake_hid.interface, EMIID.EMI1, 0x0012)
        fake_hid.interface.accepts_memory_writes = False
        with pytest.raises(
            CommunicationError, match="did not switch to data_link_layer"
        ):
            await _tunnel(Mock()).connect()

    async def test_individual_address_unreadable(self, fake_hid: FakeHIDModule) -> None:
        """Test an interface that doesn't answer the read of its individual address."""
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI1, 0x0012)
        del interface.memory[0x0117]
        tunnel = _tunnel(Mock())
        await tunnel.connect()
        assert tunnel.info is not None
        assert tunnel.info.individual_address is None
        assert tunnel.xknx.current_address == IndividualAddress(0)
        # a failing switch back to normal mode doesn't stop the disconnect
        interface.write_result = -1
        await tunnel.disconnect()
        assert fake_hid.closed == 1

    async def test_individual_address_too_short(self, fake_hid: FakeHIDModule) -> None:
        """Test an interface answering the read of its individual address with one octet."""
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI1, 0x0012)
        interface.memory[0x0117] = b"\x11"
        tunnel = _tunnel(Mock())
        await tunnel.connect()
        assert tunnel.info is not None
        assert tunnel.info.individual_address is None
        await tunnel.disconnect()

    async def test_individual_address_unknown_with_data_secure(
        self, fake_hid: FakeHIDModule
    ) -> None:
        """Test Data Secure needs the individual address of the interface."""
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI1, 0x0012)
        del interface.memory[0x0117]
        xknx = XKNX()
        xknx.cemi_handler.data_secure_init(sync_load_keyring(USB_KEYRING, "test"))
        with pytest.raises(CommunicationError, match="Data Secure needs it"):
            await _tunnel(Mock(), xknx=xknx).connect()
        assert fake_hid.closed == 1


class TestMaskVersion:
    """The individual address is only read for a BCU 1 or BCU 2 mask."""

    @pytest.mark.parametrize("emi_id", [EMIID.EMI1, EMIID.EMI2])
    async def test_other_mask(
        self,
        fake_hid: FakeHIDModule,
        emi_id: EMIID,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test no local device management for a mask without the address at 0117h."""
        interface = fake_hid.interface
        make_emi_interface(interface, emi_id, 0x0701)
        tunnel = _tunnel(Mock())
        with caplog.at_level(logging.WARNING, logger="xknx.log"):
            await tunnel.connect()
        assert not [raw for raw in _tunnelled(interface) if raw.endswith("0117")]
        assert tunnel.info is not None
        assert tunnel.info.mask_version == 0x0701
        assert tunnel.info.individual_address is None
        assert "mask version 0701h: its individual address is not read" in caplog.text
        await tunnel.disconnect()

    @pytest.mark.parametrize("emi_id", [EMIID.EMI1, EMIID.EMI2])
    async def test_mask_from_memory(
        self, fake_hid: FakeHIDModule, emi_id: EMIID
    ) -> None:
        """Test the memory mapped mask version of an interface without the device feature."""
        interface = fake_hid.interface
        make_emi_interface(interface, emi_id, None)
        mask_version = 0x0012 if emi_id is EMIID.EMI1 else 0x0021
        interface.memory[0x004E] = mask_version.to_bytes(2, "big")
        tunnel = _tunnel(Mock())
        await tunnel.connect()
        assert tunnel.info is not None
        assert tunnel.info.mask_version == mask_version
        assert tunnel.info.individual_address == IndividualAddress("1.1.5")
        await tunnel.disconnect()

    @pytest.mark.parametrize("emi_id", [EMIID.EMI1, EMIID.EMI2])
    async def test_mask_absent(
        self,
        fake_hid: FakeHIDModule,
        emi_id: EMIID,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test an interface that tells no mask version at all."""
        interface = fake_hid.interface
        make_emi_interface(interface, emi_id, None)
        tunnel = _tunnel(Mock())
        with caplog.at_level(logging.WARNING, logger="xknx.log"):
            await tunnel.connect()
        assert tunnel.info is not None
        assert tunnel.info.mask_version is None
        assert tunnel.info.individual_address is None
        assert "mask version unknown" in caplog.text
        await tunnel.disconnect()


class TestPreferredEMIType:
    """The EMI type chosen from several."""

    async def test_emi2_over_emi1(self, fake_hid: FakeHIDModule) -> None:
        """Test EMI2 is preferred to EMI1 and verified as the active one."""
        interface = fake_hid.interface
        make_emi_interface(interface, EMIID.EMI2, 0x0020)
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
            emi.l_data_req_from_cemi(EMIID.EMI2, b"\xf1")
        with pytest.raises(ConversionError, match="Invalid"):
            emi.l_data_req_from_cemi(EMIID.EMI2, bytes.fromhex("110000"))
        # extended frame
        with pytest.raises(ConversionError, match="Data Secure"):
            emi.l_data_req_from_cemi(
                EMIID.EMI1, bytes.fromhex("11003ce011050c00010081")
            )
        # with additional information
        assert emi.l_data_req_from_cemi(
            EMIID.EMI1, bytes.fromhex("1103030100bce011050c00010081")
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
        # no L_Data.ind in the bus monitor mode
        assert (
            emi.to_cemi(
                EMIID.EMI2, bytes.fromhex("29bc102f0012e1008034"), busmonitor=True
            )
            is None
        )

    def test_control_field(self) -> None:
        """Test only the defined bits of the EMI control field are taken over."""
        # L_Data.con: repeat, priority, confirm; standard frame, broadcast
        assert emi.to_cemi(
            EMIID.EMI2,
            bytes.fromhex("2efdffff0c00e10081"),
            busmonitor=False,
            own_address=0x1105,
        ) == bytes.fromhex("2e00bde011050c00010081")
        # L_Data.ind: priority only; standard frame, not repeated, broadcast
        assert emi.to_cemi(
            EMIID.EMI2, bytes.fromhex("29c3102f0012e1008034"), busmonitor=False
        ) == bytes.fromhex("2900b0e0102f001201008034")

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
        assert emi.pei_switch(EMILayer.BUSMONITOR) == bytes.fromhex("a990183456780a")
        assert emi.pei_switch(EMILayer.NORMAL) == bytes.fromhex("a900123456789a")
        assert emi.pei_switch(EMILayer.NORMAL, 0x1E) == bytes.fromhex("a91e123456789a")
        assert emi.pc_set_value(EMIID.EMI1, 0x0060, b"\x90") == bytes.fromhex(
            "4601006090"
        )
        assert emi.pc_get_value(EMIID.EMI2, 0x0117, 2) == bytes.fromhex("ac020117")

    def test_system_status(self) -> None:
        """Test the system status values of Figure 1 and the normal mode."""
        # the examples of Figure 1 have an even parity
        for status in (0x90, 0x12, 0x96, 0x1E):
            assert emi._with_parity(status) == status
        assert emi.SYSTEM_STATUS_NORMAL == 0xBE
        assert emi.normal_system_status(None) == 0xBE
        # busmonitor, data link layer, transport layer: an external client's
        for status in (0x90, 0x12, 0x96):
            assert emi.normal_system_status(status) == 0xBE
        # the application layer with or without the user program
        assert emi.normal_system_status(0x1E) == 0x1E
        assert emi.normal_system_status(0xBE) == 0xBE
