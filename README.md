XKNX - A KNX library written in Python
================================================

[![Build Status](https://travis-ci.org/XKNX/xknx.svg?branch=master)](https://travis-ci.org/XKNX/xknx)

A Wrapper around KNX/UDP protocol written in python.

The wrapper is also intended to be used as a KNX logic module, which means to connect different KNX devices and make them interact.

At the moment the wrapper works with KNX/IP routers.

See documentation at: [http://xknx.io/](http://xknx.io/)


Help
----

We need your help for testing and improving XKNX. For questions, feature requests, bugreports wither join the [XKNX chat on Gitter](https://gitter.im/XKNX/Lobby) or write an [email](mailto:xknx@xknx.io).


Home-Assistant Plugin
---------------------

XKNX contains a [Plugin](http://xknx.io/home_assistant) for the [Home-Assistant](https://home-assistant.io/) automation plattform

Supported / Tested Devices
--------------------------

The software was tested with the following devices:

- [GIRA KNX/IP-Routers 216700](http://www.gira.com/en/gebaeudetechnik/systeme/knx-eib_system/knx-produkte/systemgeraete/knx-ip-router.html)
- [GIRA KNX/Switching Actor  104000](http://katalog.gira.de/de_DE/deeplinking.html?artikelnr=104000&m=compare)
- [GIRA KNX/Shutter Binary Actor 103800](https://katalog.gira.de/en/datenblatt.html?id=635678)
- [GIRA KNX/Binary Input 111900 ](https://www.gira.de/gebaeudetechnik/systeme/knx-eib_system/knx-produkte/tasterschnittstellen/knxeib-universal-tasterschnittstelle.html)
- [GIRA Tastsensor 3 Plus 2-fach 514200 ](https://katalog.gira.de/de_DE/datenblatt.html?id=635019)
	(This sensor is also used as Thermostat)
- [KNX Dimmaktor 4fach](https://katalog.gira.de/de_DE/datenblatt.html?id=658701)


Basic Operations
----------------

```python

# Outlet

xknx.devices.device_by_name("Livingroom.Outlet_1").set_on()
time.sleep(5)
xknx.devices.device_by_name("Livingroom.Outlet_2").set_off()

# Shutter
xknx.devices.device_by_name("Livingroom.Shutter_1").set_down()
time.sleep(2)
xknx.devices.device_by_name("Livingroom.Shutter_1").set_up()
time.sleep(5)
xknx.devices.device_by_name("Livingroom.Shutter_1").set_short_down()
time.sleep(5)
xknx.devices.device_by_name("Livingroom.Shutter_1").set_short_up()

```


