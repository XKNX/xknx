#!/usr/bin/python3

from xknx import XKNX,Config,Multicast,Address,Telegram,TelegramDirection,DPT_Binary

xknx = XKNX()
Config(xknx).read()

xknx.globals.own_address = Address("1.1.4") 
telegram = Telegram(Address("1/2/7"), direction = TelegramDirection.OUTGOING, payload = DPT_Binary(1) )

multicast = Multicast(xknx)
multicast.send(telegram)
