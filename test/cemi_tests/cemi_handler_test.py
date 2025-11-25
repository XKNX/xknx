"""Test for CEMIHandler."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from xknx import XKNX
from xknx.cemi import CEMIFrame, CEMILData, CEMIMessageCode
from xknx.dpt import DPTArray
from xknx.exceptions import ConfirmationError
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, apci, tpci

from ..conftest import EventLoopClockAdvancer


async def test_wait_for_l2_confirmation(time_travel: EventLoopClockAdvancer) -> None:
    """Test waiting for L_DATA.con before sending another L_DATA.req."""
    xknx = XKNX()
    xknx.knxip_interface = AsyncMock()

    test_telegram = Telegram(
        destination_address=GroupAddress(1),
        payload=apci.GroupValueWrite(DPTArray((1,))),
    )
    test_cemi = CEMIFrame(
        code=CEMIMessageCode.L_DATA_REQ,
        data=CEMILData.init_from_telegram(test_telegram),
    )
    test_cemi_confirmation = CEMIFrame(
        code=CEMIMessageCode.L_DATA_CON,
        data=CEMILData.init_from_telegram(
            test_telegram,
        ),
    )
    task = asyncio.create_task(xknx.cemi_handler.send_telegram(test_telegram))
    await time_travel(0)
    xknx.knxip_interface.send_cemi.assert_called_once_with(test_cemi)
    assert xknx.connection_manager.cemi_count_outgoing == 0

    assert not task.done()
    xknx.cemi_handler.handle_cemi_frame(test_cemi_confirmation)
    await time_travel(0)
    assert task.done()
    await task
    assert xknx.connection_manager.cemi_count_outgoing == 1
    assert xknx.connection_manager.cemi_count_outgoing_error == 0

    # no L_DATA.con received -> raise ConfirmationError
    xknx.knxip_interface.send_cemi.reset_mock()
    task = asyncio.create_task(xknx.cemi_handler.send_telegram(test_telegram))
    await time_travel(0)
    xknx.knxip_interface.send_cemi.assert_called_once_with(test_cemi)
    with pytest.raises(ConfirmationError):
        await time_travel(3)
        assert task.done()
        await task
        assert xknx.connection_manager.cemi_count_outgoing == 1
        assert xknx.connection_manager.cemi_count_outgoing_error == 1


def test_incoming_cemi() -> None:
    """Test incoming CEMI."""
    xknx = XKNX()
    xknx.current_address = IndividualAddress("1.1.1")

    # TDataGroup Telegram
    test_telegram = Telegram(
        destination_address=GroupAddress(1),
        payload=apci.GroupValueWrite(DPTArray((1,))),
    )
    test_group_cemi = CEMIFrame(
        code=CEMIMessageCode.L_DATA_IND,
        data=CEMILData.init_from_telegram(test_telegram),
    )
    xknx.cemi_handler.handle_cemi_frame(test_group_cemi)
    assert xknx.telegrams.qsize() == 1

    # L_DATA_CON and L_DATA_REQ should not be forwarded to the telegram queue or management
    with patch.object(xknx.cemi_handler, "telegram_received") as mock_telegram_received:
        test_incoming_l_data_con = CEMIFrame(
            code=CEMIMessageCode.L_DATA_CON,
            data=CEMILData.init_from_telegram(test_telegram),
        )
        xknx.cemi_handler.handle_cemi_frame(test_incoming_l_data_con)
        mock_telegram_received.assert_not_called()

        test_incoming_l_data_req = CEMIFrame(
            code=CEMIMessageCode.L_DATA_REQ,
            data=CEMILData.init_from_telegram(test_telegram),
        )
        xknx.cemi_handler.handle_cemi_frame(test_incoming_l_data_req)
        mock_telegram_received.assert_not_called()
        assert xknx.connection_manager.cemi_count_incoming == 1


@pytest.mark.parametrize(
    "telegram",
    [
        Telegram(
            destination_address=GroupAddress(0),
            tpci=tpci.TDataBroadcast(),
        ),
        Telegram(
            destination_address=IndividualAddress("1.1.1"),
            tpci=tpci.TConnect(),
        ),
        Telegram(
            destination_address=IndividualAddress("1.1.1"),
            tpci=tpci.TDataIndividual(),
        ),
    ],
)
def test_incoming_management_telegram(telegram: Telegram) -> None:
    """Test incoming management CEMI."""
    xknx = XKNX()
    xknx.current_address = IndividualAddress("1.1.1")

    with patch.object(xknx.management, "process") as mock_management_process:
        test_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(telegram),
        )
        xknx.cemi_handler.handle_cemi_frame(test_cemi)
        mock_management_process.assert_called_once()
        assert xknx.telegrams.qsize() == 0
        assert xknx.connection_manager.cemi_count_incoming == 1


@pytest.mark.parametrize(
    "raw",
    [
        # <CouldNotParseCEMI description="CEMI too small. Length: 9; CEMI: 2900b06010fa10ff00" />
        # communication_channel_id: 0x02   sequence_counter: 0x81
        bytes.fromhex("2900b06010fa10ff00"),
    ],
)
def test_invalid_cemi(raw: bytes) -> None:
    """Test incoming invalid CEMI Frames."""
    xknx = XKNX()

    with (
        patch("logging.Logger.warning") as mock_info,
        patch.object(xknx.cemi_handler, "handle_cemi_frame") as mock_handle_cemi_frame,
    ):
        xknx.cemi_handler.handle_raw_cemi(raw)
        mock_info.assert_called_once()
        mock_handle_cemi_frame.assert_not_called()
        assert xknx.connection_manager.cemi_count_incoming_error == 1


@pytest.mark.parametrize(
    "raw",
    [
        # LDataInd Unsupported Extended APCI from 0.0.1 to 0/0/0 broadcast
        # <UnsupportedCEMIMessage description="APCI not supported: 0b1111111000 in CEMI: 2900b0d0000100000103f8" />
        bytes.fromhex("2900b0d0000100000103f8"),
    ],
)
def test_unsupported_cemi(raw: bytes) -> None:
    """Test incoming unsupported CEMI Frames."""
    xknx = XKNX()

    with (
        patch("logging.Logger.info") as mock_info,
        patch.object(xknx.cemi_handler, "handle_cemi_frame") as mock_handle_cemi_frame,
    ):
        xknx.cemi_handler.handle_raw_cemi(raw)
        mock_info.assert_called_once()
        mock_handle_cemi_frame.assert_not_called()
        assert xknx.connection_manager.cemi_count_incoming_error == 1


def test_incoming_from_own_ia() -> None:
    """Test incoming CEMI from own IA."""
    xknx = XKNX()
    xknx.current_address = IndividualAddress("1.1.22")
    # L_Data.ind GroupValueWrite from 1.1.22 to to 5/1/22 with DPT9 payload 0C 3F
    raw = bytes.fromhex("2900bcd011162916030080 0c 3f")

    with (
        patch("logging.Logger.debug") as mock_debug,
        patch.object(xknx.cemi_handler, "telegram_received") as mock_telegram_received,
    ):
        xknx.cemi_handler.handle_raw_cemi(raw)
        mock_debug.assert_called_once()
        mock_telegram_received.assert_called_once()
        assert xknx.connection_manager.cemi_count_incoming == 1
        assert xknx.connection_manager.cemi_count_incoming_error == 0


@pytest.mark.parametrize(
    "raw_cemi_data_secure",
    [
        # src = 4.0.9; dst = 0/4/0; GroupValueResponse; value=(116, 41, 41)
        # A+C; seq_num=155806854986
        bytes.fromhex("29003ce0400904001103f110002446cfef4ac085e7092ab062b44d"),
        # Property Value Write PID_GRP_KEY_TABLE connectionless
        # Object Idx = 5, PropId = 35h, Element Count = 1, Index = 1
        # Data = 20 21 22 23 24 25 26 27 28 29 2A 2B 2C 2D 2E 2F
        # A+C
        # from AN158 v07 KNX Data Security AS - Annex A example
        bytes.fromhex(
            "29 00 b0 60 ff 67 ff 00 22 03 f1 90 00 00 00 00"
            "00 04 67 67 24 2a 23 08 ca 76 a1 17 74 21 4e e4"
            "cf 5d 94 90 9f 74 3d 05 0d 8f c1 68"
        ),
    ],
)
def test_incoming_cemi_no_data_secure_keys(raw_cemi_data_secure: bytes) -> None:
    """Test incoming DataSecure CEMI when no DataSecure keys are initialized."""
    xknx = XKNX()
    xknx.current_address = IndividualAddress("5.0.1")

    with (
        patch("logging.Logger.debug") as mock_debug,
        patch.object(xknx.cemi_handler, "telegram_received") as mock_telegram_received,
    ):
        xknx.cemi_handler.handle_raw_cemi(raw_cemi_data_secure)
        assert mock_debug.call_count == 2  # one for reception, one for DataSecure debug
        mock_telegram_received.assert_not_called()
        assert xknx.connection_manager.cemi_count_incoming == 0
        assert xknx.connection_manager.cemi_count_incoming_error == 0
