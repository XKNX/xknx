"""
"
" Connects to XKNX plattform
"
"""
import logging
from homeassistant.helpers import discovery
from .xknx_wrapper import XKNX_Wrapper
from .xknx_config import XKNX_Config

DOMAIN = "xknx"

#SUPPORTED_DOMAINS = ['binary_sensor', 'cover', 'fan', 'light', 'lock', 'sensor', 'switch']
SUPPORTED_DOMAINS = ['switch', 'climate', 'cover', 'light']


_LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    """Setup device tracker."""

    xknx_config = XKNX_Config(hass, config)

    global xknx_wrapper
    xknx_wrapper = XKNX_Wrapper(hass, xknx_config)
    xknx_wrapper.start()

    # Load platforms for the devices in the ISY controller that we support.
    for component in SUPPORTED_DOMAINS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    return True
