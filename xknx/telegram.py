from .address import Address
import binascii

class Telegram:
    """Abstraction for the business logic of KNX Telegrams

       This is a leightweight object for business logic,
       only containing group address and payload.
    """

    def __init__(self):
        self.group_address = Address()
        self.payload = bytearray()

    def __str__(self):
        return "<Telegram group_address={0}, payload={1}>".format(
            self.group_address,binascii.hexlify(self.payload))
