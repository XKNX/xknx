
""" Implementation of Basic KNX datatypes """

""" See: http://www.knx.org/fileadmin/template/documents/downloads_support_menu/KNX_tutor_seminar_page/Advanced_documentation/05_Interworking_E1209.pdf as reference """

from enum import Enum
import time

class ConversionError(Exception):
    def __init__(self, i):
        self.i = i
    def __str__(self):
        return "<ConversionError input='{0}'>".format(self.i)


class DPT_Base:

    @staticmethod
    def test_bytesarray( raw,length ):
        if type(raw) is not tuple \
                or len(raw) != length \
                or any(not isinstance(byte,int) for byte in raw) \
                or any(byte < 0 for byte in raw) \
                or any(byte > 255 for byte in raw):
            raise ConversionError(raw)


class DPT_Binary(DPT_Base):
    """ The DPT_Binary is a base class for all datatypes encoded
    directly into the first Byte of the payload """

    # APCI (application layer control information)  
    APCI_BITMASK = 0x3F
    APCI_MAX_VALUE = APCI_BITMASK 

    def __init__( self, value ):
        if not isinstance(value,int):
            raise TypeError()
        if value > DPT_Binary.APCI_BITMASK:
            raise ConversionError(value)

        self.value = value

    def __eq__(self, other):
        return DPT_Comparator.compare(self,other)

    def __str__(self):
        return "<DPT_Binary value={0}>".format(self.value)



class DPT_Array(DPT_Base):
    """ The DPT_Array is a base class for all datatypes appended
    to the KNX telegram """

    def __init__(self, value ):
        if isinstance(value, int):
            self.value = (value,)
        elif isinstance(value, (list,bytes)):
            self.value = tuple(value,)
        elif isinstance(value, tuple):
            self.value = value
        else:
            print(value,type(value))
            raise TypeError()

    def __eq__(self, other):
        return DPT_Comparator.compare(self,other)

    def __str__(self):
        return "<DPT_Array value=[{0}]>".format( ','.join(hex(b) for b in self.value))



class DPT_Comparator():
    """ Helper class to compare different types of DPT objects"""

    @staticmethod
    def compare(a,b):
        if a is None and b is None:
            return True

        elif a is None:
            if isinstance(b,DPT_Binary):
                return b.value == 0
            elif isinstance(b,DPT_Array):
                return len(b.value) == 0

        elif b is None:
            if isinstance(a,DPT_Binary):
                return a.value == 0
            elif isinstance(a,DPT_Array):
                return len(a.value) == 0

        elif isinstance(a,DPT_Array) and isinstance(b,DPT_Array):
            return a.value == b.value

        elif isinstance(a,DPT_Binary) and isinstance(b,DPT_Binary):
            return a.value == b.value

        elif isinstance(a,DPT_Binary) and isinstance(b,DPT_Array):
            return a.value == 0 and len(b.value) == 0

        elif isinstance(a,DPT_Array) and isinstance(b,DPT_Binary):
            return len(a.value) == 0 and b.value == 0

        raise TypeError()

