---
layout: default
---


Home Assistant KNX Integration
========================

XKNX is shipped within [Home Assistant (HA)](https://www.home-assistant.io/), the great solution for home automation, in the form of the included [KNX integration](https://www.home-assistant.io/integrations/#search/KNX).

For development and debugging reasons - or to catch up with the newest features - you may still want to use the custom component version of the plugin.


Manual Installation:
--------------------

Checkout `xknx` ideally into your home folder:

```bash
cd ~
git clone https://github.com/XKNX/xknx.git
```

Create a symbolic link to your custom components directory:

```bash
mkdir -p ~/.homeassistant
ln -s ~/xknx/home-assistant-plugin/custom_components ~/.homeassistant/custom_components
```

Run HA as usual either via service or by directly typing in `hass`.

Running HA with local XKNX library
------------------------------------

Even when running HA with the XKNX custom component, HA will automatically install a `xknx` library version within `.homeassistant/deps/lib/python[python-version]/site-packages` via pip. This very often causes the problem, that the manually checked out `xknx` library is not in sync with the `xknx` library version HA already contains and uses by default. But getting both in sync is easy:

Delete the automatically installed version:

```bash
rm .homeassistant/deps/lib/python[python-version]/site-packages/xknx*
```

Ideally start HA from command line. Export the environment variable PYTHONPATH to your local `xknx` checkout:

```bash
export PYTHONPATH=$HOME/xknx
hass
```

Starting via service is also possible, but you have to change the configuration to make sure PYTHONPATH [is set correctly](https://stackoverflow.com/questions/45374910/how-to-pass-environment-variables-to-a-service-started-by-systemd).


Configuration:
--------------

The configuration for the manually checked out version works the same as described within [Home Assistant KNX documentation](https://home-assistant.io/integrations/#search/knx) with the difference that the integration and platform is called `xknx` instead of `knx` (which is the HA default KNX integration and platform name).

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


