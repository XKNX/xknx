---
layout: default
---


Home Assistant Component
========================

XKNX ships with [Home Assistant](https://home-assistant.io/components/#search/knx), the great platform for home automation!

For development and debugging reasons - or to catch up with the newest features - you may still use the custom component version of the plugin.


Manual Installation:
--------------------

Checkout xknx ideally into your home folder:

```bash
cd ~
git clone https://github.com/XKNX/xknx.git
```

Create a symbolic link to your custom components directory:

```bash
mkdir -p ~/.homeassistant
ln -s ~/xknx/home-assistant-plugin/custom_components ~/.homeassistant/custom_components
```

Run HASS as usual either via service or by directly typing in `hass`.

Running HASS with local XKNX library
------------------------------------

Even when running hass with the XKNX component, hass will automatically install a xknx library within `.homeassistant/deps/lib/python3.5/site-packages` via pip. This very often causes the problem, that the checked out xknx library is not in sync with the xknx library hass uses. But getting both in sync is easy:

Delete automatically installed version:

```bash
rm .homeassistant/deps/lib/python3.5/site-packages/xknx*
```

Ideally start hass from command line. Export the environment variable PYTHONPATH to your local xknx checkout:

```bash
export PYTHONPATH=$HOME/xknx
hass
```

Starting via service is also possible, but you have to change the configuration to make sure PYTHONPATH [is set correctly](https://stackoverflow.com/questions/45374910/how-to-pass-environment-variables-to-a-service-started-by-systemd).


Configuration:
--------------

The configuration works as described within [Home Assistant documentation](https://home-assistant.io/components/#search/knx) with the difference that the component is called `xknx` instead of `knx`.

### Platform:

```yaml 
xknx:
  tunneling:
    host: '192.168.2.23'
    port: 3671
    local_ip: '192.168.2.109'

light:
  - platform: xknx
    name: Kitchen-Light-1
    address: '1/0/9'
    brightness_address: '1/0/11'

switch:
  - platform: xknx
    name: Kitchen.Coffee
    address: '1/1/6'
```


Help
----

If you have problems, join the [XKNX chat on Discord](https://discord.gg/EuAQDXU). We are happy to help :-)


