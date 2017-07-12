#!/usr/bin/python3

from xknx import XKNX,Config,Multicast,Address,Telegram,TelegramType,TelegramDirection,DPTBinary, DPTArray
import time

xknx = XKNX()
Config(xknx).read(file="/home/julius/.homeassistant/xknx.yaml")

xknx.globals.own_address = Address("6.6.6") 

def read(address):
    telegram = Telegram(address, direction = TelegramDirection.OUTGOING, telegramtype=TelegramType.GROUP_READ)
    multicast = Multicast(xknx)
    multicast.send(telegram)


def write(address):
    telegram = Telegram(address, direction = TelegramDirection.OUTGOING, payload =  DPTArray((0x60,) ))
    multicast = Multicast(xknx)
    multicast.send(telegram)

def handle(address):
    write(address)
    #read(address)
    #print(address.raw)
    pass

while True:
    print("WAITING 5 seconds")
    time.sleep(5)
    handle(Address("2/0/0"))
    handle(Address("2/0/1"))
    handle(Address("2/0/2"))
    handle(Address("2/0/3"))
    handle(Address("2/0/4"))
    handle(Address("2/0/5"))
    time.sleep(1)
    handle(Address("2/0/6"))
    handle(Address("2/0/7"))
    handle(Address("2/0/8"))
    handle(Address("2/0/9"))
    handle(Address("2/0/10"))
    handle(Address("2/0/11"))
    time.sleep(1)
    #read(Address("2/1/0"))
    #read(Address("2/1/1"))
    #read(Address("2/1/2"))
    #read(Address("2/1/3"))
    #read(Address("2/1/4"))
    #read(Address("2/1/5"))
    #time.sleep(1)
    #read(Address("2/1/6"))
    #read(Address("2/1/7"))
    #read(Address("2/1/8"))
    #read(Address("2/1/9"))
    #read(Address("2/1/10"))
    #read(Address("2/1/11"))
    #print("sleeping for 1 minute")
    time.sleep(60)
