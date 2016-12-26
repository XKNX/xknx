from datetime import time, date, datetime, timedelta
from .colors import Colors
from enum import Enum

class xKNXCouldNotConvert(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "CouldNotConvert"

class DPT():
    def __init__(self, type = "", name = "", valuerange= (0,100), unit="", bitlength = 1):	
	    self._type = type
	    self._name = name
	    self._valuerange = valuerange
	    self._unit  = unit
	    self._bitlength = bitlength
    @property
    def type(self):
	    """Return the type"""
	    return _type		
    @property
    def name(self):
	    """Return the name"""
	    return _name	
    @property
    def valuerange(self):
	    """Return the valuerange"""
	    return _valuerange	
    @property
    def unit(self):
	    """Return the unit"""
	    return _unit	
    @property
    def bitlength(self):
	    """Return the unit"""
	    return _bitlength			
		
class DPTTypes(Enum):
    DPT_1_Switch  = DPT("1.001", "Switch", (0, 1), "", 1)
    DPT_3_Dimming  = DPT("3.000", "Dimming", ([0,0], [1,7]), "", 8)
    DPT_4_ASCII_CHAR  = DPT("4.000", "ASCII_CHAR", (0, 1), "", 8)
    DPT_5_Scaling = DPT("5.001", "Scaling", (0, 100), "%")
    DPT_5_Angle = DPT("5.003", "Angle", (0, 360), "s")
    DPT_5_Percent_U8 = DPT("5.004", "Percent (8 bit)", (0, 255), "%")
    DPT_5_DecimalFactor = DPT("5.005", "Decimal factor", (0, 1), "ratio")
    DPT_7_INT_Unsigned  = DPT("7.000", "Int unigned", (0, 65535), "", 16)
    DPT_8_INT_Signed  = DPT("8.000", "Int signed", (-32768, 32767), "", 16)
    DPT_9_FLOAT  = DPT("9.000", "Foat", (-671088.64, 670760.96), "", 16)
	
class xKNXconvert():
    def float2knx(value):
        """Convert a float to a 2 byte KNX float value"""
        if value < -671088.64 or value > 670760.96:
            raise xKNXCouldNotConvert("float {} out of valid range".format(value))
			
        value = value * 100
        i = 0
        for i in range(0, 15):
            exp = pow(2, i)
            if ((value / exp) >= -2048) and ((value / exp) < 2047):
                break
        if value < 0:
            sign = 1
            mantisse = int(2048 + (value / exp))
        else:
            sign = 0
            mantisse = int(value / exp)

        return [(sign << 7) + (i << 3) + (mantisse >> 8),
            mantisse & 0xff]
			
    def knx2float(knxdata):
        """Convert a KNX 2 byte float object to a float"""
        if knxdata == None:
          raise xKNXCouldNotConvert("Can not convert a object of Type None")
        if len(knxdata) != 2:
          raise xKNXCouldNotConvert("Can only convert a 2 Byte object to float")
	  
      
        data = knxdata[0] * 256 + knxdata[1]
        sign = data >> 15
        exponent = (data >> 11) & 0x0f
        mantisse = float(data & 0x7ff)
        if sign == 1:
            mantisse = -2048 + mantisse

        return mantisse * pow(2, exponent) / 100

