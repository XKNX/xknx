
DOMAIN = "xknx"

class XKNXConfig(object):
    """Representation of XKNX Configuration."""

    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self.xknx_config = config.get(DOMAIN, {})
        self.ensure_config()

    def ensure_config(self):
        # Config can be an empty list. In that case, substitute a dict
        if isinstance(self.xknx_config, list):
            self.xknx_config = \
                self.xknx_config[0] \
                if len(self.xknx_config) > 0 else \
                {}

    def get_config_value(self, key, default_value):
        if not key in self.xknx_config:
            return default_value
        return self.xknx_config[key]

    def config_file(self):
        config_file = self.get_config_value("config_file", "xknx.yml")
        if not config_file.startswith("/"):
            return  self.hass.config.path(config_file)
        return config_file
