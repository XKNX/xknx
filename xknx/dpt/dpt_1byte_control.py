"""Implementation of Basic KNX DPT_1_Control Values."""
from xknx.exceptions import ConversionError

from .dpt import DPTBase, DPTComparator


class DPTControl(DPTBase):
    """
    Abstraction for KNX 1 Nibble "control and step-code".

    DPT 3.00*
    """

    # pylint: disable=too-few-public-methods

    # APCI (application layer control information)
    APCI_CONTROLMASK = 0x08
    APCI_STEPCODEMASK = 0x07
    APCI_MAX_VALUE = (APCI_CONTROLMASK | APCI_STEPCODEMASK)

    unit = ""
    resolution = 1
    payload_length = 1

    def __init__(self, control, step_code=None):
        """Initialize DPTControl class."""
        if step_code is None:
            if isinstance(control, int):
                value = control
            elif isinstance(control, (list, tuple, bytes)):
                value = control[0]
            else:
                raise TypeError()
        else:
            if not self._test_values(control, step_code):
                raise ConversionError("Cant init DPTControl", control=control, step_code=step_code)
            value = self.__encode__(control, step_code)

        if value > self.APCI_MAX_VALUE or value < 0:
            raise ConversionError("Cant init DPTControl", value=value)

        self.value = value

    def __eq__(self, other):
        """Equal operator."""
        """Test if 'a' and 'b' are the same."""
        # pylint: disable=invalid-name,too-many-return-statements,len-as-condition
        if other is None:
            return self.value == 0

        if not isinstance(other, DPTControl):
            raise TypeError()

        return self.value == other.value

    @classmethod
    def __encode__(cls, control, step_code):
        """Encodes control-bit with step-code"""
        value = 1 if control > 0 else 0
        value = (value << 3) | (step_code & cls.APCI_STEPCODEMASK)
        return value

    @classmethod
    def __decode__(cls, value):
        """Decodes value into control-bit and step-code"""
        control = 1 if (value & cls.APCI_CONTROLMASK) != 0 else 0
        step_code = (value & cls.APCI_STEPCODEMASK)
        return control, step_code

    def __str__(self):
        """Return object as readable string."""
        control, step_code = self.__decode__(self.value)
        step_code_str = 'break' if step_code == 0 else 2**(step_code-1)
        return '<DPTControl value="{0}|{1}" />'.format(control, step_code_str)
        # stepcode: 001b…111b: -> Number of intervals = 2^(stepcode-1)
        #           000b: Break

    @classmethod
    def to_knx(cls, values, invert=False):
        """Serialize to KNX/IP raw data."""
        # from values to array/tuple
        try:
            if not isinstance(values, dict):
                raise ValueError

            control = values.get('control', 0)
            step_code = values.get('step_code', 1)

            if not cls._test_values(control, step_code):
                raise ValueError

            if invert:
                control = 1 if control == 0 else 0

            knx_value = cls.__encode__(control, step_code)

            if not cls._test_boundaries(knx_value):
                raise ValueError

            return (knx_value, )
        except ValueError:
            raise ConversionError("Cant serialize %s" % cls.__name__, values=values)

    @classmethod
    def from_knx(cls, raw, invert=False):
        """Parse/deserialize from KNX/IP raw data."""
        # from int/array/tuple to values
        if isinstance(raw, (list, tuple)):
            cls.test_bytesarray(raw, cls.payload_length)
            value = raw[0]
        else:
            value = raw

        if not cls._test_boundaries(value):
            raise ConversionError("Cant parse %s" % cls.__name__, raw=raw)

        control, step_code = cls.__decode__(value)

        if invert:
            control = 1 if control == 0 else 0

        return {
            'control': control,
            'step_code': step_code
        }

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        if isinstance(value, int):
            return 0 <= value <= cls.APCI_MAX_VALUE
        else:
            return False

    @classmethod
    def _test_values(cls, control, step_code):
        """Test if input values are valid."""
        try:
            if 0 > control or control > 1:
                return 0
            if 0 > step_code or step_code > cls.APCI_CONTROLMASK:
                return 0
        except:
            return 0
        return 1

    @classmethod
    def invert_control_bit(cls, value):
        if value & cls.APCI_CONTROLMASK:
            value = value & ~cls.APCI_CONTROLMASK  # clear bit
        else:
            value = value | cls.APCI_CONTROLMASK   # set bit
        return value


class DPTControlDimming(DPTControl):
    """
    Abstraction for KNX 1 Octet Dimming.

    DPT 3.007
    """
    pass


class DPTControlBlinds(DPTControl):
    """
    Abstraction for KNX 1 Octet Blinds.

    DPT 3.008
    """
    pass

