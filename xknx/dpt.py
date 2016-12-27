from enum import Enum

class ConversionError(Exception):
    def __init__(self, i):
        self.i = i
    def __str__(self):
        return "<ConversionError input='{0}'>".format(self.i)


class DPT_BASE:

    @staticmethod
    def test_bytesarray( raw,length ):
        if type(raw) is not tuple \
                or len(raw) != length \
                or any(not isinstance(byte,int) for byte in raw) \
                or any(byte < 0 for byte in raw) \
                or any(byte > 255 for byte in raw):
            raise ConversionError(raw)

class DPT_Float(DPT_BASE):
    """ Abstraction for KNX 2 Octet Floating Point Numbers """
    """ DPT 9.xxx """

    value_min = -671088.64 
    value_max = 670760.96

    @staticmethod
    def from_knx(raw):
        """Convert a 2 byte KNX float to a flaot value"""
        DPT_BASE.test_bytesarray(raw,2)

        data = (raw[0] * 256 ) + raw[1]
        exponent = (data >> 11) & 0x0f
        significand = data & 0x7ff
        sign = data >> 15

        if sign == 1:
            significand = significand - 2048

        return float(significand << exponent) / 100


    @staticmethod
    def to_knx(value):
        """Convert a float to a 2 byte KNX float value"""

        if not isinstance(value, (int, float)):
            raise ConversionError(value)

        if value < DPT_Float.value_min or \
                value > DPT_Float.value_max:
            raise ConversionError(value)

        sign = 1 if value < 0 else 0

        def calc_exponent(value, sign):
            exponent = 0
            significand = abs ( int (value * 100) )

            while significand < -2048 or significand > 2048:
                exponent += 1
                significand >>= 1

            if sign:
                significand ^= 0x7ff # invert
                significand += 1     # and add 1

            return exponent,significand

        exponent,significand = calc_exponent(value, sign)

        return (sign << 7) | (exponent << 3) | (significand >> 8), significand & 0xff

class DPT_Weekday(Enum):
    MONDAY    = 1
    TUESDAY   = 2
    WEDNESDAY = 3
    THURSDAY  = 4
    FRIDAY    = 5
    SATURDAY  = 6
    SUNDAY    = 7
    NONE      = 0

class DPT_Time(DPT_BASE):
    """ Abstraction for KNX 3 Octet Time """
    """ DPT 10.001 """

    @staticmethod
    def from_knx(raw):
        """Convert a 3 byte KNX date to a time dict"""

        DPT_BASE.test_bytesarray(raw,3)

        day     = ( raw[0] & 0xE0 ) >> 5
        hours   = raw[0] & 0x1F
        minutes = raw[1] & 0x3F
        seconds = raw[2] & 0x3F

        if not DPT_Time.test_range(day,hours,minutes,seconds):
            raise ConversionError(raw)

        return {'day':DPT_Weekday(day),'hours':hours,
            'minutes':minutes,'seconds':seconds}

    @staticmethod
    def to_knx(values):
        """Convert time tuple to KNX time
        @param value: dict with following elements: (day,hours,minutes,seconds)
        """

        if not isinstance(values, dict):
            raise ConversionError(values)

        day     = values.get('day',DPT_Weekday.NONE).value
        hours   = values.get('hours',0)
        minutes = values.get('minutes',0)
        seconds = values.get('seconds',0)

        if not DPT_Time.test_range(day,hours,minutes,seconds):
            raise ConversionError(value)

        return day << 5 | hours, minutes, seconds

    @staticmethod
    def current_time():
        t = time.localtime()

        day     = t.tm_wday + 1
        hours   = t.tm_hour
        minutes = t.tm_min
        seconds = t.tm_sec

        return {'day':DPT_Weekday(day),'hours':hours,
            'minutes':minutes,'seconds':seconds}

    @classmethod
    def current_time_as_knx(cls):
        return cls.to_knx( cls.current_time() )

    @staticmethod
    def test_range(day,hours,minutes,seconds):
        if day < 0 or day > 7:
            return False
        if hours < 0 or hours > 23:
            return False
        if minutes  < 0 or minutes > 59:
            return False
        if seconds  < 0 or seconds > 59:
            return False
        return True
