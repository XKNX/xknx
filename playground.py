#!/usr/bin/python3

import socket
import time
from knx import Address,Telegram,Multicast,NameResolver

nameresolver = NameResolver()
my_address = Address("1.2.4")

def send(group,payload):
    multicast = Multicast(my_address)
    telegram = Telegram()
    telegram.group=group
    telegram.payload.append(payload)
    multicast.send(telegram)

def callback(telegram):

    print( 'Message from: {0}', nameresolver.device_name( telegram.sender ) )

    if (telegram.group == 1):
        send(65,telegram.payload[0])

    if (telegram.group == 2):
        send(65,telegram.payload[0])

Multicast(my_address).recv(callback)

