#!/usr/bin/python3

import socket
import time
from knx import Address,Telegram,Multicast,NameResolver

nameresolver = NameResolver()
own_address = Address("1.2.4")

def send(group,payload):
    if type(group) is str:
        send(nameresolver.group_id(group), payload)
        return

    multicast = Multicast(own_address)
    telegram = Telegram()
    telegram.sender.set(own_address)
    telegram.group=group
    telegram.payload.append(payload)
    multicast.send(telegram)

def callback(telegram):

    print( 'Message from: {0} / {1}',
        nameresolver.device_name( telegram.sender ), 
        nameresolver.group_name( telegram.group) )

    if (telegram.group == nameresolver.group_id("Livingroom/Switch 1") ):
        send("Livingroom/Light 1",telegram.payload[0])

    if (telegram.group == nameresolver.group_id("Livingroom/Switch 2") ):
        send("Livingroom/Light 2",telegram.payload[0])

Multicast(own_address).recv(callback)

