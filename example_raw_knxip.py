#!/usr/bin/python3

from xknx import XKNX,Config,Multicast,Address,Telegram,TelegramDirection,DPTBinary

xknx = XKNX()
Config(xknx).read()

xknx.globals.own_address = Address("1.1.4") 
telegram = Telegram(Address("1/2/7"), direction = TelegramDirection.OUTGOING, payload = DPTBinary(1) )

multicast = Multicast(xknx)
multicast.send(telegram)
