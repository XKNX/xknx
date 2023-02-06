---
layout: default
title: Home Assistant Integration
has_children: true
nav_order: 13
---


Home Assistant KNX Integration
========================

XKNX is shipped within [Home Assistant (HA)](https://www.home-assistant.io/), the great solution for home automation, in the form of the included [KNX integration](https://www.home-assistant.io/integrations/knx/).


Running HA with local XKNX library
------------------------------------

When running HA with the KNX integrated component once, HA will automatically install a `xknx` library version within `[hass-dependency-directory]/lib/python[python-version]/site-packages` via pip. In order to test new features before a release you can run HA with a local xknx installation as follows:

Delete the automatically installed version of the library:

```bash
rm [hass-dependency-directory]/lib/python[python-version]/site-packages/xknx*
```

Note: `[hass-dependency-directory]` is platform dependent (e.g. `/usr/local` for Docker image, `~/.homeassistant/deps` for macOS or `/srv/homeassistant` for Debian).

Ideally start HA from command line. Export the environment variable PYTHONPATH to your local `xknx` checkout:

```bash
export PYTHONPATH=$HOME/xknx
hass
```

Starting via service is also possible, but you have to change the configuration to make sure PYTHONPATH [is set correctly](https://stackoverflow.com/questions/45374910/how-to-pass-environment-variables-to-a-service-started-by-systemd).

Help
----

If you have problems, join the [XKNX chat on Discord](https://discord.gg/EuAQDXU). We are happy to help :-)

