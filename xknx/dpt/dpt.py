"""Implementation of Basic KNX datatypes."""
from xknx.exceptions import ConversionError


class DPTBase:
    """
    Base class for KNX data point type transcoder.

    KNX communicates using Group-addresses, and every Group Object represents a data point of some type.
    To have a standardized interpretation of the data there are a number of Data Point types (DPT).
    The DPT's is written like: xx.yyy, for example 14.056 for a 4-octet float, with Power info in Watts.
    The Major number (xx) describes the data type (format and encoding) - while the the minor (YYY) number
    describes the measurement with value range and unit.

    More DTP's are added as new needs come up, but this a list of some of the commonly used ones:
    1.yyy  boolean, like switching, on/off, open/close, move up/down, step
    2.yyy  2 x boolean, e.g. switching + priority control
    3.yyy  boolean + 3-bit unsigned value, e.g. dimming up/down
    4.yyy  character (8-bit)
    5.yyy  8-bit unsigned value, like dim value (0..100%), blinds position (0..100%)
    6.yyy  8-bit signed (2's complement), e.g. +/- %
    7.yyy  2-byte unsigned value, i.e. pulse counter
    8.yyy  2-byte signed (2's complement), e.g. +/- %
    9.yyy  2-byte float, e.g. temperature
    10.yyy time (3 bytes)
    11.yyy date (3 bytes)
    12.yyy 4-byte unsigned value, i.e. pulse counter
    13.yyy 4-byte signed (2's complement), i.e. flow, energy
    14.yyy 4-byte float, IEEE 754, i.e. Electrical measurements: current, power
    15.yyy access control
    16.yyy string -> 14 characters (14 x 8-bit)
    17.yyy scene number
    18.yyy scene control
    19.yyy date / time
    20.yyy 8-bit enumeration, e.g. HVAC mode ('auto', 'comfort', 'standby', 'economy', 'protection')
    28.yyy UTF-8
    29.yyy V64, 64-bit signed value
    232.yyy RGB [0,0,0]...[255,255,255]

    """

    payload_length = None

    @classmethod
    def test_bytesarray(cls, raw):
        """Test if array of raw bytes has the correct length and values of correct type."""
        if cls.payload_length is None:
            raise NotImplementedError("payload_length has to be defined for: %s" % cls)
        if (
            not isinstance(raw, (tuple, list))
            or len(raw) != cls.payload_length
            or any(not isinstance(byte, int) for byte in raw)
            or any(byte < 0 for byte in raw)
            or any(byte > 255 for byte in raw)
        ):
            raise ConversionError("Invalid raw bytes", raw=raw)

    @classmethod
    def __recursive_subclasses__(cls):
        """Yield all subclasses and their subclasses."""
        for subclass in cls.__subclasses__():
            yield from subclass.__recursive_subclasses__()
            yield subclass

    @classmethod
    def has_distinct_dpt_numbers(cls):
        """Return True if dpt numbers are defined (not inherited)."""
        return "dpt_main_number" in cls.__dict__ and "dpt_sub_number" in cls.__dict__

    @classmethod
    def has_distinct_value_type(cls):
        """Return True if value_type is defined (not inherited)."""
        return "value_type" in cls.__dict__

    @staticmethod
    def transcoder_by_dpt(dpt_main, dpt_sub=None):
        """Return Class reference of DPTBase subclass with matching DPT number."""
        for dpt in DPTBase.__recursive_subclasses__():
            if dpt.has_distinct_dpt_numbers():
                if dpt_main == dpt.dpt_main_number and dpt_sub == dpt.dpt_sub_number:
                    return dpt
        return None

    @staticmethod
    def transcoder_by_value_type(value_type):
        """Return Class reference of DPTBase subclass with matching value_type."""
        for dpt in DPTBase.__recursive_subclasses__():
            if dpt.has_distinct_value_type():
                if value_type == dpt.value_type:
                    return dpt
        return None

    @staticmethod
    def parse_transcoder(value_type):
        """Return Class reference of DPTBase subclass from value_type or DPT number."""
        if isinstance(value_type, int):
            return DPTBase.transcoder_by_dpt(value_type)
        if isinstance(value_type, float):
            # avoid modulo for floating point rounding errors
            main, sub = map(int, str(value_type).split("."))
            return DPTBase.transcoder_by_dpt(main, sub)
        if isinstance(value_type, str):
            _string_type = value_type.strip()
            transcoder = DPTBase.transcoder_by_value_type(_string_type)
            if transcoder is None:
                # Try to parse the value_type if it is a string but not found by DPTBase.transcoder_by_value_type()
                # for backwards compatibility (eg. "DPT-5") and strings representing numbers (eg. "7", "9.001")
                _string_type = _string_type.upper().strip(" DPT-")
                if _string_type.isdigit():
                    transcoder = DPTBase.parse_transcoder(int(_string_type))
                else:
                    try:
                        transcoder = DPTBase.parse_transcoder(float(_string_type))
                    except ValueError:
                        pass
            return transcoder
        return None


class DPTBinary:
    """The DPTBinary is a base class for all datatypes encoded directly into the last 6 bit of the APCI (mostly integer)."""

    # pylint: disable=too-few-public-methods

    # APCI (application layer control information)
    APCI_BITMASK = 0x3F
    APCI_MAX_VALUE = APCI_BITMASK

    def __init__(self, value):
        """Initialize DPTBinary class."""
        if not isinstance(value, int):
            raise TypeError()
        if value > DPTBinary.APCI_BITMASK:
            raise ConversionError("Could not init DPTBinary", value=value)

        self.value = value

    def __eq__(self, other):
        """Equal operator."""
        return DPTComparator.compare(self, other)

    def __str__(self):
        """Return object as readable string."""
        return f'<DPTBinary value="{self.value}" />'


class DPTArray:
    """The DPTArray is a base class for all datatypes appended to the KNX telegram."""

    # pylint: disable=too-few-public-methods
    def __init__(self, value):
        """Initialize DPTArray class."""
        if isinstance(value, int):
            self.value = (value,)
        elif isinstance(value, (list, bytes)):
            self.value = tuple(
                value,
            )
        elif isinstance(value, tuple):
            self.value = value
        else:
            raise TypeError()

    def __eq__(self, other):
        """Equal operator."""
        return DPTComparator.compare(self, other)

    def __str__(self):
        """Return object as readable string."""
        return '<DPTArray value="[{}]" />'.format(",".join(hex(b) for b in self.value))


class DPTComparator:
    """Helper class to compare different types of DPT objects."""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def compare(a, b):
        """Test if 'a' and 'b' are the same."""
        # pylint: disable=invalid-name,too-many-return-statements,len-as-condition
        if a is None and b is None:
            return True

        if a is None:
            if isinstance(b, DPTBinary):
                return b.value == 0
            if isinstance(b, DPTArray):
                return len(b.value) == 0

        if b is None:
            if isinstance(a, DPTBinary):
                return a.value == 0
            if isinstance(a, DPTArray):
                return len(a.value) == 0

        if isinstance(a, DPTArray) and isinstance(b, DPTArray):
            return a.value == b.value

        if isinstance(a, DPTBinary) and isinstance(b, DPTBinary):
            return a.value == b.value

        if isinstance(a, DPTBinary) and isinstance(b, DPTArray):
            return a.value == 0 and len(b.value) == 0

        if isinstance(a, DPTArray) and isinstance(b, DPTBinary):
            return len(a.value) == 0 and b.value == 0

        raise TypeError()
