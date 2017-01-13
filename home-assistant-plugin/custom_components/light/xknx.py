import logging
import xknx

#import homeassistant.components.xknx as xknx_component
import custom_components.xknx as xknx_component

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    # pylint: disable=unused-argument
    """Setup the demo light platform."""

    if xknx_component.XKNX_MODULE is None \
            or not xknx_component.XKNX_MODULE.initialized:
        _LOGGER.error('A connection has not been made to the XKNX controller.')
        return False

    entities = []

    for device in xknx_component.XKNX_MODULE.xknx.devices.devices:
        if isinstance(device, xknx.Light):
            entities.append(xknx_component.XKNXLight(hass, device))

    add_devices_callback(entities)

    return True
