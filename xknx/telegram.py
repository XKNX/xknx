from .address import Address
import binascii
from enum import Enum

class TelegramType(Enum):
    INCOMING = 1
    OUTGOING = 2

class Telegram:
    """ Abstraction for the business logic of KNX Telegrams

        This is a leightweight object for business logic,
        only containing group address and payload.

        The telegram type marks if a telegram originates from
        XKNX abstraction or was sent from outside for internal
        processing.
    """

    def __init__(self,type = TelegramType.OUTGOING):
        self.type = type
        self.group_address = Address()
        self.payload = bytearray()

    def __str__(self):
        return "<Telegram group_address={0}, payload={1} type={2}>".format(
            self.group_address,binascii.hexlify(self.payload),
            self.type)
