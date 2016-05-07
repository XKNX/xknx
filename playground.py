#!/usr/bin/python3

from knx import Telegram,Multicast,BinaryInput,BinaryOutput 
from knx import NameResolver,nameresolver_

def callback(telegram):

    if (telegram.group == nameresolver_.group_id("Livingroom/Switch 1") ):
        binaryinput = BinaryInput(telegram)

        if binaryinput.is_on():
            BinaryOutput("Livingroom/Outlet 1").set_on()

        elif binaryinput.is_off():
            BinaryOutput("Livingroom/Outlet 1").set_off()

    if (telegram.group == nameresolver_.group_id("Livingroom/Switch 2") ):
        binaryinput = BinaryInput(telegram)

        if binaryinput.is_on():
            BinaryOutput("Livingroom/Outlet 2").set_on()

        elif binaryinput.is_off():
            BinaryOutput("Livingroom/Outlet 2").set_off()


nameresolver_.init()
Multicast().recv(callback)

