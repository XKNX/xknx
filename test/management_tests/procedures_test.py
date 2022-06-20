"""Test management procedures."""
import asyncio
from unittest.mock import call, patch

from xknx import XKNX
from xknx.management import procedures
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


@patch("xknx.io.knxip_interface.KNXIPInterface", autospec=True)
async def test_nm_individual_address_check_success(_if_mock):
    """Test nm_individual_address_check."""
    xknx = XKNX()
    individual_address = IndividualAddress("4.0.10")

    connect = Telegram(destination_address=individual_address, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    ack = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    device_desc_resp = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorResponse(),
    )
    task = asyncio.create_task(
        procedures.nm_individual_address_check(xknx, individual_address)
    )
    await asyncio.sleep(0)
    assert xknx.knxip_interface.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]
    # receive response
    xknx.management.process(ack)
    xknx.management.process(device_desc_resp)
    assert await task


@patch("xknx.io.knxip_interface.KNXIPInterface", autospec=True)
async def test_nm_individual_address_check_refused(_if_mock):
    """Test nm_individual_address_check."""
    xknx = XKNX()
    individual_address = IndividualAddress("4.0.10")

    connect = Telegram(destination_address=individual_address, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    ack = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    disconnect = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDisconnect(),
    )
    task = asyncio.create_task(
        procedures.nm_individual_address_check(xknx, individual_address)
    )
    await asyncio.sleep(0)
    assert xknx.knxip_interface.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]
    xknx.management.process(disconnect)
    xknx.management.process(ack)
    assert await task
