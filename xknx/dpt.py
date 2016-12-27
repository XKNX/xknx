
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

