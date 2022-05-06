"""Unit test for code sniplets regarding programming device support."""
import pytest

from xknx.knxip.tunnelling_request import TunnellingRequest

# from xknx import XKNX
# from xknx.knxip.tpdu import TPDU
# from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, TPDUType


@pytest.mark.asyncio
class TestSniplet:
    """Test class for code sniplets regarding programming device support."""

    async def test_tunnelling_request(self):
        tr = TunnellingRequest()
        tr.from_knx(bytes.fromhex("0403020100010203040506070809"))
