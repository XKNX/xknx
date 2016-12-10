
Installation:
-------------
* checkout xknx library e.g. within ~/xknx

* `make install -C ~/xknx/home-assistant-plugin` will copy plugin files to `~/.homeassistant/custom_components`

* Add Configuration to `~/.homeassistant/configuration.yaml` ( config_file should define the absolute path of your `xknx.yaml` ) 

```
xknx:
    config_file: /home/julius/xknx/xknx.yaml
```


Running:
--------

* add the location of the xknx library to `PYTHONPATH` when starting hass:

```
PYTHONPATH="${PYTHONPATH}:${HOME}/xknx" hass
```

