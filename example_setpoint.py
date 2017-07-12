#!/usr/bin/python3

from xknx import XKNX,Config,Multicast,Address,Telegram,TelegramType,TelegramDirection,DPTBinary, DPTArray, DPTTemperature

xknx = XKNX()
Config(xknx).read(file="/home/julius/.homeassistant/xknx.yaml")

xknx.globals.own_address = Address("6.6.6") 

def read(address):
    telegram = Telegram(address, direction = TelegramDirection.OUTGOING, telegramtype=TelegramType.GROUP_READ)
    multicast = Multicast(xknx)
    multicast.send(telegram)


def write(address):
    telegram = Telegram(address, direction = TelegramDirection.OUTGOING, payload =  DPTArray(DPTTemperature().to_knx(17.10)) )
    multicast = Multicast(xknx)
    multicast.send(telegram)

def handle(address):
    write(address)
    read(address)
    #print(address.raw)

handle(Address("5/1/1"))
