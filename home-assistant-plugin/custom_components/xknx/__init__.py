"""
"
" Connects to xknx plattform
"
"""
import logging
from homeassistant.helpers import discovery
from .xknx_wrapper import XKNX_Wrapper

DOMAIN = "xknx"

#SUPPORTED_DOMAINS = ['binary_sensor', 'cover', 'fan', 'light', 'lock', 'sensor', 'switch']

SUPPORTED_DOMAINS = ['switch','climate']

_LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    """Setup device tracker."""

    conf = config.get(DOMAIN, {})

    # Config can be an empty list. In that case, substitute a dict
    if isinstance(conf, list):
        conf = conf[0] if len(conf) > 0 else {}

    config_file = conf["config_file"]

    global xknx_wrapper
    xknx_wrapper = XKNX_Wrapper(hass, config_file)
    xknx_wrapper.start()

    # Load platforms for the devices in the ISY controller that we support.
    for component in SUPPORTED_DOMAINS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    return True
