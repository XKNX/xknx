"""
"
" Connects to XKNX plattform
"
"""
import logging
from homeassistant.helpers import discovery

from .xknx_wrapper import XKNXWrapper
from .xknx_config import XKNXConfig
from .xknx_binary_sensor import XKNXBinarySensor
from .xknx_sensor import XKNXSensor
from .xknx_switch import XKNXSwitch
from .xknx_climate import XKNXClimate
from .xknx_cover import XKNXCover
from .xknx_light import XKNXLight

DOMAIN = "xknx"

SUPPORTED_DOMAINS = [
    'switch',
    'climate',
    'cover',
    'light',
    'sensor',
    'binary_sensor']


_LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    """Setup device tracker."""

    xknx_config = XKNXConfig(hass, config)

    global xknx_wrapper
    xknx_wrapper = XKNXWrapper(hass, xknx_config)
    xknx_wrapper.start()

    # Load platforms for the devices in the ISY controller that we support.
    for component in SUPPORTED_DOMAINS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    return True
