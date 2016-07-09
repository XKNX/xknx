from .address import Address

class Globals():
    own_address_ = Address("15.15.250")

    own_ip = None

    @staticmethod
    def set_own_address(own_address):
        Globals.own_address_.set(own_address)

    @staticmethod
    def get_own_address():
        return Globals.own_address_

    @staticmethod
    def set_own_ip(own_ip):
        Globals.own_ip=own_ip

    @staticmethod
    def get_own_ip():
        return Globals.own_ip
