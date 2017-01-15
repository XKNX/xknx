
""" Implementation of Basic KNX datatypes """

class ConversionError(Exception):
    def __init__(self, i):
        super(ConversionError, self).__init__("Conversion Error")
        self.i = i
    def __str__(self):
        return "<ConversionError input='{0}'>".format(self.i)


class DPTBase:
    # pylint: disable=too-few-public-methods
    @staticmethod
    def test_bytesarray(raw, length):
        if not isinstance(raw, tuple) \
                or len(raw) != length \
                or any(not isinstance(byte, int) for byte in raw) \
                or any(byte < 0 for byte in raw) \
                or any(byte > 255 for byte in raw):
            raise ConversionError(raw)


class DPTBinary(DPTBase):
    # pylint: disable=too-few-public-methods
    """ The DPTBinary is a base class for all datatypes encoded
    directly into the first Byte of the payload """

    # APCI (application layer control information)
    APCI_BITMASK = 0x3F
    APCI_MAX_VALUE = APCI_BITMASK

    def __init__(self, value):
        if not isinstance(value, int):
            raise TypeError()
        if value > DPTBinary.APCI_BITMASK:
            raise ConversionError(value)

        self.value = value

    def __eq__(self, other):
        return DPTComparator.compare(self, other)

    def __str__(self):
        return "<DPTBinary value={0}>".format(self.value)



class DPTArray(DPTBase):
    # pylint: disable=too-few-public-methods
    """ The DPTArray is a base class for all datatypes appended
    to the KNX telegram """

    def __init__(self, value):
        if isinstance(value, int):
            self.value = (value,)
        elif isinstance(value, (list, bytes)):
            self.value = tuple(value,)
        elif isinstance(value, tuple):
            self.value = value
        else:
            raise TypeError()

    def __eq__(self, other):
        return DPTComparator.compare(self, other)

    def __str__(self):
        return "<DPTArray value=[{0}]>".format(
            ','.join(hex(b) for b in self.value))


class DPTComparator():
    # pylint: disable=too-few-public-methods
    """ Helper class to compare different types of DPT objects"""

    @staticmethod
    def compare(a, b):
        # pylint: disable=invalid-name,too-many-return-statements
        if a is None and b is None:
            return True

        elif a is None:
            if isinstance(b, DPTBinary):
                return b.value == 0
            elif isinstance(b, DPTArray):
                return len(b.value) == 0

        elif b is None:
            if isinstance(a, DPTBinary):
                return a.value == 0
            elif isinstance(a, DPTArray):
                return len(a.value) == 0

        elif isinstance(a, DPTArray) and isinstance(b, DPTArray):
            return a.value == b.value

        elif isinstance(a, DPTBinary) and isinstance(b, DPTBinary):
            return a.value == b.value

        elif isinstance(a, DPTBinary) and isinstance(b, DPTArray):
            return a.value == 0 and len(b.value) == 0

        elif isinstance(a, DPTArray) and isinstance(b, DPTBinary):
            return len(a.value) == 0 and b.value == 0

        raise TypeError()
