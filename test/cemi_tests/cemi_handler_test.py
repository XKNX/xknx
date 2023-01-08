"""Test for CEMIHandler."""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from xknx import XKNX
from xknx.cemi import CEMIFrame, CEMIMessageCode
from xknx.dpt import DPTArray
from xknx.exceptions import ConfirmationError
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, apci, tpci


async def test_wait_for_l2_confirmation(time_travel):
    """Test waiting for L_DATA.con before sending another L_DATA.req."""
    xknx = XKNX()
    xknx.knxip_interface = AsyncMock()

    test_telegram = Telegram(
        destination_address=GroupAddress(1),
        payload=apci.GroupValueWrite(DPTArray((1,))),
    )
    test_cemi = CEMIFrame.init_from_telegram(
        test_telegram,
        code=CEMIMessageCode.L_DATA_REQ,
    )
    test_cemi_confirmation = CEMIFrame.init_from_telegram(
        test_telegram,
        code=CEMIMessageCode.L_DATA_CON,
    )
    task = asyncio.create_task(xknx.cemi_handler.send_telegram(test_telegram))
    await time_travel(0)
    xknx.knxip_interface.send_cemi.assert_called_once_with(test_cemi)
    assert not task.done()
    xknx.cemi_handler.handle_cemi_frame(test_cemi_confirmation)
    await time_travel(0)
    assert task.done()
    await task

    # no L_DATA.con received -> raise ConfirmationError
    xknx.knxip_interface.send_cemi.reset_mock()
    task = asyncio.create_task(xknx.cemi_handler.send_telegram(test_telegram))
    await time_travel(0)
    xknx.knxip_interface.send_cemi.assert_called_once_with(test_cemi)
    with pytest.raises(ConfirmationError):
        await time_travel(3)
        assert task.done()
        await task


def test_incoming_cemi():
    """Test incoming CEMI."""
    xknx = XKNX()
    xknx.current_address = IndividualAddress("1.1.1")

    # TDataGroup Telegram
    test_telegram = Telegram(
        destination_address=GroupAddress(1),
        payload=apci.GroupValueWrite(DPTArray((1,))),
    )
    test_group_cemi = CEMIFrame.init_from_telegram(
        test_telegram,
        code=CEMIMessageCode.L_DATA_IND,
    )
    xknx.cemi_handler.handle_cemi_frame(test_group_cemi)
    assert xknx.telegrams.qsize() == 1

    # L_DATA_CON and L_DATA_REQ should not be forwarded to the telegram queue or management
    with patch.object(xknx.cemi_handler, "telegram_received") as mock_telegram_received:
        test_incoming_l_data_con = CEMIFrame.init_from_telegram(
            test_telegram,
            code=CEMIMessageCode.L_DATA_CON,
        )
        xknx.cemi_handler.handle_cemi_frame(test_incoming_l_data_con)
        mock_telegram_received.assert_not_called()

        test_incoming_l_data_req = CEMIFrame.init_from_telegram(
            test_telegram,
            code=CEMIMessageCode.L_DATA_REQ,
        )
        xknx.cemi_handler.handle_cemi_frame(test_incoming_l_data_req)
        mock_telegram_received.assert_not_called()


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
def test_incoming_management_telegram(telegram):
    """Test incoming management CEMI."""
    xknx = XKNX()
    xknx.current_address = IndividualAddress("1.1.1")

    with patch.object(xknx.management, "process") as mock_management_process:
        test_cemi = CEMIFrame.init_from_telegram(
            telegram, code=CEMIMessageCode.L_DATA_IND
        )
        xknx.cemi_handler.handle_cemi_frame(test_cemi)
        mock_management_process.assert_called_once()
        assert xknx.telegrams.qsize() == 0
