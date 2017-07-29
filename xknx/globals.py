"""Module for handling some global settings of XKNX."""
from xknx.knx import Address, AddressType

class Globals():
    """Class for handling some global settings of XKNX."""
    # pylint: disable=too-few-public-methods

    def __init__(self):
        """Initialize Globals class."""

        # own_address is the own group address of the XKNX daemon
        self.own_address = Address("15.15.250", AddressType.PHYSICAL)

        #own_ip is the own ip address of the daemon. Needed if multiple
        #network interfaces are available to detect on which the multicast
        #daemon should listen
        self.own_ip = None
