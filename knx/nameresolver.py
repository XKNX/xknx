import yaml
from .address import Address

class NameResolver:

    def __init__(self, file='xknx.yaml'):

        with open(file, 'r') as f:
            self.doc = yaml.load(f)

    def device_name( self, address ):
        if type(address) is Address: 
            return self.device_name( address.str() )

        if address not in self.doc["devices"].keys():
            return 'unknown device ({0})'.format(address)

        return self.doc["devices"][address]

