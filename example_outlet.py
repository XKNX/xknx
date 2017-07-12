#!/usr/bin/python3

from xknx import XKNX

xknx = XKNX(config="xknx.yaml")

xknx.devices["Livingroom.Outlet_1"].set_on()
xknx.join()

