from enum import Enum
from .address import Address

class TelegramDirection(Enum):
    INCOMING = 1
    OUTGOING = 2


class TelegramType(Enum):
    GROUP_READ = 1
    GROUP_WRITE = 2
    GROUP_RESPONSE = 3


class Telegram:
    # pylint: disable=too-few-public-methods

    """ Abstraction for the business logic of KNX Telegrams

        This is a leightweight object for business logic,
        only containing group address and payload.

        The telegram direction marks if a telegram originates from
        XKNX abstraction or was sent from outside for internal
        processing.
    """

    def __init__(self, group_address=Address(),
                 telegramtype=TelegramType.GROUP_WRITE,
                 direction=TelegramDirection.OUTGOING,
                 payload=None):
        self.direction = direction
        self.telegramtype = telegramtype
        self.group_address = group_address
        self.payload = payload


    def __str__(self):
        return "<Telegram group_address={0}, payload={1} " \
                "telegramtype={2} direction={3}>".format(
                    self.group_address,
                    self.payload,
                    self.telegramtype,
                    self.direction)


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
