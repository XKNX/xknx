from .address import Address
from .dpt import DPT_Binary
from enum import Enum

class TelegramDirection(Enum):
    INCOMING = 1
    OUTGOING = 2

class TelegramType(Enum):
    GROUP_READ = 1
    GROUP_WRITE = 2
    GROUP_RESPONSE = 3

class Telegram:
    """ Abstraction for the business logic of KNX Telegrams

        This is a leightweight object for business logic,
        only containing group address and payload.

        The telegram direction marks if a telegram originates from
        XKNX abstraction or was sent from outside for internal
        processing.
    """

    def __init__(self, group_address = Address(),
            type = TelegramType.GROUP_WRITE,
            direction = TelegramDirection.OUTGOING, payload = None ):
        self.direction = direction
        self.type = type
        self.group_address = group_address
        self.payload = payload

    def __str__(self):
        return "<Telegram group_address={0}, payload={1} type={2} direction={3}>".format(
            self.group_address,
            self.payload,
            self.type,
            self.direction)

    # TODO: Add unit test
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
