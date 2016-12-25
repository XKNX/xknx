from enum import Enum

class CouldNotParseAddress(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "CouldNotParseAddress"

class AddressType(Enum):
    PHYSICAL = 1
    GROUP = 2

class AddressFormat(Enum):
    LEVEL2 = 1
    LEVEL3 = 2
    FREE = 3 

class Address:

    def __init__(self, address = 0, address_type = AddressType.GROUP):
        self._set(address, address_type)

    def __eq__(self, other):
        if type(other) is not Address:
            raise TypeError()
        return self.raw == other.raw

    def __str__(self):
        return self._to_str()

    def _set(self, address, address_type):

        if address is None:
            self.raw=0
            self.address_format = AddressFormat.LEVEL3
            self.address_type = address_type

        elif type(address) is Address:
            self.raw = address.raw
            self.address_format = address.address_format
            self.address_type = address.address_type

        elif type(address) is str:
            self.address_type = address_type
            if address_type == AddressType.PHYSICAL:
                self._set_str(address,".")
            else:
                self._set_str(address,"/")
    
        elif type(address) is int:
            self._set_int(address)
            self.address_format = AddressFormat.FREE
            self.address_type = address_type

        else:
            raise TypeError()

    def byte1(self):
        return ( self.raw >> 8 ) & 255

    def byte2(self):
        return self.raw & 255

    def is_set(self):
        return self.raw != 0

    ##################################################

    def _set_str( self, address, delimiter ):
        parts = address.split(delimiter)
            
        if any(not part.isdigit() for part in parts):
            raise CouldNotParseAddress()
        if len(parts) == 1:
            self._set_int( int ( parts[0] ) ) 
        elif len(parts) == 2:
            self._set_str_level2( parts )
        elif len(parts) == 3:
            self._set_str_level3( parts )
        else:
            raise CouldNotParseAddress()

    def _set_str_level2( self, parts ):
        main = int(parts[0])
        sub = int(parts[1])   
        if main > 15:
            raise CouldNotParseAddress()
        if sub > 4095:
            raise CouldNotParseAddress()
        self.raw = (main<<12) + sub
        self.address_format = AddressFormat.LEVEL2

    def _set_str_level3( self, parts ):
        main = int(parts[0])
        middle = int(parts[1])
        sub = int(parts[2]) 
        if main > 15:
            raise CouldNotParseAddress()
        if middle > 15:
            raise CouldNotParseAddress()
        if sub > 255:
            raise CouldNotParseAddress()
        self.raw = (main<<12) +  (middle<<8) + sub
        self.address_format = AddressFormat.LEVEL3

    def _set_int(self, raw):
        if type(raw) is not int:
            raise CouldNotParseAddress()
        if ( raw > 65535 ):
            raise CouldNotParseAddress()
        self.raw = raw
        self.address_format = AddressFormat.FREE

    def _to_str(self):
        if self.address_type == AddressType.PHYSICAL:
            return self._to_str_physical()
        elif self.address_format == AddressFormat.FREE:
            return self._to_str_free()
        elif self.address_format == AddressFormat.LEVEL2:
            return self._to_str_level2()
        elif self.address_format == AddressFormat.LEVEL3:
            return self._to_str_level3()
        else:
            raise TypeError() 

    def _to_str_free(self):
        return '{0}'.format(
            (self.raw & 65535) )

    def _to_str_level2(self):
        return '{0}/{1}'.format(
            ((self.raw >> 12 ) & 15),
            (self.raw & 4095) )

    def _to_str_level3(self):
        return '{0}/{1}/{2}'.format(
            ((self.raw >> 12 ) & 15),
            ((self.raw >> 8) & 15),
            (self.raw & 255) )

    def _to_str_physical(self):
        return '{0}.{1}.{2}'.format(
            ((self.raw >> 12 ) & 15),
            ((self.raw >> 8) & 15),
            (self.raw & 255) )
