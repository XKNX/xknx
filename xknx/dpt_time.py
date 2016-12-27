
""" Implementation of Basic KNX Time """

""" See: http://www.knx.org/fileadmin/template/documents/downloads_support_menu/KNX_tutor_seminar_page/Advanced_documentation/05_Interworking_E1209.pdf as reference """

from enum import Enum
import time

from .dpt import DPT_Base,ConversionError

class DPT_Weekday(Enum):
    MONDAY    = 1
    TUESDAY   = 2
    WEDNESDAY = 3
    THURSDAY  = 4
    FRIDAY    = 5
    SATURDAY  = 6
    SUNDAY    = 7
    NONE      = 0

class DPT_Time(DPT_Base):
    """ Abstraction for KNX 3 Octet Time """
    """ DPT 10.001 """

    @classmethod
    def from_knx(cls,raw):
        """Convert a 3 byte KNX date to a time dict"""

        cls.test_bytesarray(raw,3)

        day     = ( raw[0] & 0xE0 ) >> 5
        hours   = raw[0] & 0x1F
        minutes = raw[1] & 0x3F
        seconds = raw[2] & 0x3F

        if not DPT_Time.test_range(day,hours,minutes,seconds):
            raise ConversionError(raw)

        return {'day':DPT_Weekday(day),'hours':hours,
            'minutes':minutes,'seconds':seconds}

    @classmethod
    def to_knx(cls,values):
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

    @classmethod
    def current_time(cls):
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
