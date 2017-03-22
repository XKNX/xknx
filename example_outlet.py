#!/usr/bin/python3

from xknx import XKNX,Config

xknx = XKNX()

Config(xknx).read()

xknx.devices["Livingroom.Outlet_1"].set_on()
xknx.join()

