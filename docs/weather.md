---
layout: default
title: Weather
parent: Devices
nav_order: 11
---

# [](#header-1)Weather device

## [](#header-2)Overview

The weather device is basically a set of sensors that you can obtain from your weather station.

## [](#header-2)Example

```python

    async with XKNX() as xknx:
        weather = Weather(
            xknx,
            'Home',
            group_address_temperature='7/0/1',
            group_address_brightness_south='7/0/5',
            group_address_brightness_east='7/0/4',
            group_address_brightness_west='7/0/3',
            group_address_wind_speed='7/0/2',
            group_address_wind_bearing='7/0/6',
            group_address_day_night='7/0/7',
            group_address_rain_alarm='7/0/0'
        )
        xknx.devices.async_add(weather)

        await weather.sync(wait_for_result=True)
        print(weather)

```

## [](#header-2)Interface

- **xknx** is the XKNX object.
- **name** is the name of the object.
- **group_address_temperature** KNX address of current outside temperature.
- **group_address_brightness_south** KNX address for the brightness to south **DPT 9.004**.
- **group_address_brightness_west** KNX address for the brightness to west **DPT 9.004**.
- **group_address_brightness_east** KNX address for the brightness to east **DPT 9.004**.
- **group_address_wind_speed** KNX address for current wind speed. **DPT 9.005**
- **group_address_wind_bearing** KNX address for current wind bearing. **DPT 5.003**
- **group_address_rain_alarm** KNX address for reading if rain alarm is on/off.
- **group_address_wind_alarm** KNX address for reading if wind alarm is on/off.
- **group_address_frost_alarm** KNX address for reading if frost alarm is on/off.
- **group_address_day_night** KNX address for reading a day/night object.
- **group_address_air_pressure** KNX address reading current air pressure. **DPT 9.006 or 14.058**
- **group_address_humidity** KNX address for reading current humidity. **DPT 9.007**
- **sync_state** Periodically sync the state.
- **device_updated_cb** Callback for each update.

```python

    async with XKNX() as xknx:
        weather = Weather(
            xknx,
            'Home',
            group_address_temperature='7/0/1',
            group_address_brightness_south='7/0/5',
            group_address_brightness_east='7/0/4',
            group_address_brightness_west='7/0/3',
            group_address_wind_speed='7/0/2',
            group_address_day_night='7/0/7',
            group_address_rain_alarm='7/0/0'
        )
        xknx.devices.async_add(weather)

        await weather.sync(wait_for_result=True)

        print(weather.humidity) # get humidity
        print(weather.ha_current_state()) # get the current state mapped as a WeatherCondition enum value. (for HA mainly)
        print(weather.wind_speed) # get the current wind speed in m/s

```
