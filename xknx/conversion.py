from datetime import time, date, datetime, timedelta
from .colors import Colors
from enum import Enum

class CouldNotConvert(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "CouldNotConvert"

class DPT():
    def __init__(self, dptype = "", name = "", valuerange= (0,1), unit="", bitlength = 1):	
	    self._dptype = dptype
	    self._name = name
	    self._valuerange = valuerange
	    self._unit  = unit
	    self._bitlength = bitlength
	    self._value = 0
	    self._raw = [0]
    @property
    def dptype(self):
	    """Return the type"""
	    return _dptype		
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
    def value(self):
	    """Return the value"""
	    return _value	
    @property
    def raw(self):
	    """Return the rawknxdata"""
	    return _raw	
    @property
    def bitlength(self):
	    """Return the bitlength"""
	    return _bitlength		
		
    def convert2knx(self, value):
        pass
    def convert2value(self, knxdata):
        pass

	
class DPT_9_FLOAT(DPT):
    def __init__(self,  value = None,  data = None):
        DPT.__init__( "9.000", "Float", (-671088.64, 670760.96), "",  16)	   
        self._value = value
        self._raw = data
		
    def convert2knxdata(value):
        """Convert a float to a 2 byte KNX float value"""
        if value < -671088.64 or value > 670760.96:
            raise CouldNotConvert("DPT_9 {} out of valid range".format(value))
			
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

    def convert2value(knxdata):
        """Convert a KNX 2 byte float object to a float"""
        if knxdata == None:
          raise CouldNotConvert("Can not convert a object of Type None")
        if len(knxdata) != 2:
          raise CouldNotConvert("Can only convert a 2 Byte object to float")
	       
        data = knxdata[0] * 256 + knxdata[1]
        sign = data >> 15
        exponent = (data >> 11) & 0x0f
        mantisse = float(data & 0x7ff)
        if sign == 1:
            mantisse = -2048 + mantisse

        return mantisse * pow(2, exponent) / 100

