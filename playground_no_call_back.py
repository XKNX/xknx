#!/usr/bin/python3
from xknx import Multicast,Devices,devices_,Config

Config.read()

Multicast().recv()

