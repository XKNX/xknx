"""
"
" Connects to XKNX plattforms
"
"""
import logging
from homeassistant.helpers import discovery

from .xknx_module import XKNXModule
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

XKNX_MODULE = None

def setup(hass, config):
    """Setup device tracker."""

    # pylint: disable=global-statement, import-error
    global XKNX_MODULE

    if XKNX_MODULE is None:
        XKNX_MODULE = XKNXModule(hass, config)
        XKNX_MODULE.start()

    for component in SUPPORTED_DOMAINS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    return True
