"""Test for CEMIHandler."""
import asyncio
from unittest.mock import AsyncMock

from xknx import XKNX
from xknx.dpt import DPTArray
from xknx.knxip import CEMIFrame, CEMIMessageCode
from xknx.telegram import GroupAddress, Telegram, apci


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
