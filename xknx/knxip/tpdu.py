"""
Created on 14.01.2021.

@author: bonzius
"""
from xknx.telegram import IndividualAddress, GroupAddress, Telegram, TPDUType
from xknx.exceptions import UnsupportedCEMIMessage
from .knxip_enum import CEMIMessageCode

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from xknx.xknx import XKNX
    from typing import Union, List
    from Adress import InternalGroupAddress


class TPDU:
    """alternative class to CEMIFrame for non T_DATA requests."""

    def __init__(
        self,
        xknx: XKNX,
        src_addr: IndividualAddress = IndividualAddress(None),
    ):
        """Initialize TPDU."""
        self.xknx = xknx
        self.src_addr = src_addr
        self.destination_address: Union[GroupAddress, IndividualAddress, InternalGroupAddress] = IndividualAddress(None)
        self.tpdu_type: TPDUType | None = None

    @staticmethod
    def init_from_telegram(
        xknx: XKNX,
        telegram: Telegram,
        src_addr: IndividualAddress = IndividualAddress(None),
    ) -> TPDU:
        """Return TPDU from a Telegram."""
        tpdu = TPDU(xknx, src_addr)
        tpdu.telegram = telegram
        return tpdu

    @property
    def telegram(self) -> Telegram:
        """Return telegram."""
        return Telegram(destination_address=self.destination_address,
                        )

    @telegram.setter
    def telegram(self, telegram: Telegram) -> None:
        """Set telegram."""
        self.destination_address = telegram.destination_address
        self.tpdu_type = telegram.tpdu_type

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        '''
        if raw[0] != 0x11:
            raise UnsupportedCEMIMessage(
                "Invalid TPDU message code: {} in TPDU: {}".format(
                    raw[0], raw.hex()
                ))
        '''
        try:
            self.code = CEMIMessageCode(raw[0])
        except ValueError:
            raise UnsupportedCEMIMessage(
                "CEMIMessageCode not implemented: {} in CEMI: {}".format(
                    raw[0], raw.hex()
                )
            )
        self.destination_address = IndividualAddress((raw[6], raw[7]))
        self.data = raw
        return 10

    def calculated_length(self) -> int:
        """Length of PDU."""
        return 10

    def to_knx(self) -> List[int]:
        """Convert PDU to KNX."""
        data = [0x11, 0x00, 0xb0, 0x60, 0x00, 0x00]
        data += self.destination_address.to_knx()
        if self.tpdu_type == TPDUType.T_CONNECT:
            data += [0x00, 0x80]
        elif self.tpdu_type == TPDUType.T_DISCONNECT:
            data += [0x00, 0x81]
        elif self.tpdu_type == TPDUType.T_ACK:
            data += [0x00, 0xc2]
        elif self.tpdu_type == TPDUType.T_ACK_NUMBERED:
            data += [0x00, 0xc6]
        else:
            raise RuntimeError("Invalid TPDUType" + str(self.tpdu_type))
        return data

    def __str__(self) -> str:
        """Return object as readable string."""
        res = '<TPDUFrame DestinationAddress="{}" '.format(
            self.destination_address.__repr__())
        '''
        data = self.to_knx()
        for i in data:
            res += hex(i) + " "
        '''
        return res
