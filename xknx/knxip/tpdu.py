'''
Created on 14.01.2021

@author: bonzius
'''

''' alternative class to CEMIFrame for non T_DATA requests '''
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, TelegramDirection
#from xknx.telegram.telegram import TPDUTelegram
from xknx.knxip.knxip_enum import TPDUType
from typing import Optional, Union
from xknx.telegram.apci import APCI


class TPDUTelegram (Telegram):
    ''' Subtype w/o spacial implementation '''
    def __init__(
        self,
        destination_address: Union[GroupAddress, IndividualAddress] = GroupAddress(0),
        direction: TelegramDirection = TelegramDirection.OUTGOING,
        payload: Optional[APCI] = None,
        source_address: IndividualAddress = IndividualAddress(0),
        tpdu_type: TPDUType = TPDUType.T_DATA
    ) -> None:
        """Initialize Telegram class."""
        self.destination_address = destination_address
        self.direction = direction
        self.payload = payload
        self.source_address = source_address
        self.tpdu_type = tpdu_type
 

class TPDU:
    
    def __init__(
        self,
        xknx,
        src_addr: IndividualAddress,
        tpdu_type:TPDUType
    ):
        self.xknx = xknx
        self.src_addr = src_addr
        self.tpdu_type = tpdu_type

    def init_from_telegram(
        xknx: "XKNX",
        telegram: TPDUTelegram,
        src_addr: IndividualAddress = IndividualAddress(None),
    ):
        """Return CEMIFrame from a Telegram."""
        tpdu = TPDU(xknx, src_addr, telegram.tpdu_type)
        # dst_addr, payload and cmd are set by telegram.setter - mpdu_len not needed for outgoing telegram
        tpdu.telegram = telegram
        return tpdu

    def calculated_length(self):
        return 11
    
    def to_knx(self):
        bytes = [0x11, 0x00, 0xb0, 0x60, 0x00, 0x00, 0x12, 0x03, 0x00, 0x80, 0x66]
        return bytes
    

       