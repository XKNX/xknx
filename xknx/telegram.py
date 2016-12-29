from .address import Address
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
        self.payload = []

    def __str__(self):
        return "<Telegram group_address={0}, payload=[{1}] type={2}>".format(
            self.group_address,
            ','.join(hex(b) for b in self.payload),
            self.type)
