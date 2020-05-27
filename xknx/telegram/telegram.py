"""
Module for KNX Telegrams.

The telegram class is the leightweight interaction object between

* business logic (Lights, Covers, etc) and
* underlaying KNX/IP abstraction (KNX-Routing/KNX-Tunneling).

It contains

* the telegram type (e.g. GROUP_WRITE)
* the direction (incoming or outgoing)
* the group address (e.g. 1/2/3)
* and the payload (e.g. "12%" or "23.23 C".

"""
from enum import Enum

from .address import GroupAddress


class TelegramDirection(Enum):
    """Enum class for the communication direction of a telegram (from KNX bus or to KNX bus)."""

    INCOMING = 1
    OUTGOING = 2


class TelegramType(Enum):
    """Enum class for type of telegram."""

    GROUP_READ = 1
    GROUP_WRITE = 2
    GROUP_RESPONSE = 3


class Telegram:
    """Class for KNX telegrams."""

    # pylint: disable=too-few-public-methods

    def __init__(self, group_address=GroupAddress(None),
                 telegramtype=TelegramType.GROUP_WRITE,
                 direction=TelegramDirection.OUTGOING,
                 payload=None):
        """Initialize Telegram class."""
        self.direction = direction
        self.telegramtype = telegramtype
        self.group_address = group_address
        self.payload = payload

    def __str__(self):
        """Return object as readable string."""
        return '<Telegram group_address="{0}", payload="{1}" ' \
            'telegramtype="{2}" direction="{3}" />'.format(
                self.group_address.__repr__(),
                self.payload,
                self.telegramtype,
                self.direction)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
