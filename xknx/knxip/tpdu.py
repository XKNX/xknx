'''
Created on 14.01.2021

@author: bonzius
'''
#from enum import Enum
''' alternative class to CEMIFrame for non T_DATA requests '''
from xknx.telegram import IndividualAddress, Telegram, TPDUType
#from xknx.telegram.telegram import TPDUTelegram
#from typing import Optional, Union


class TPDU:
    
    def __init__(
        self,
        xknx,
        src_addr: IndividualAddress,
    ):
        self.xknx = xknx
        self.src_addr = src_addr
        
    @staticmethod
    def init_from_telegram(
        xknx: "XKNX",
        telegram: Telegram,
        src_addr: IndividualAddress = IndividualAddress(None),
    ):
        """Return CEMIFrame from a Telegram."""
        tpdu = TPDU(xknx, src_addr)
        tpdu.telegram = telegram
        return tpdu

    def calculated_length(self):
        return 11
    
    def to_knx(self):
        data = [0x11, 0x00, 0xb0, 0x60, 0x00, 0x00]
        data += self.telegram.destination_address.to_knx()
        data += [ 0x00, 0x80, 0x66]
        return data
    

       