
from homeassistant.components.switch import SwitchDevice


class XKNXSwitch(SwitchDevice):
    """Representation of XKNX switches."""

    def __init__(self, device):
        self.device = device
        self.register_callbacks()

    def register_callbacks(self):
        def after_update_callback(device):
            # pylint: disable=unused-argument
            self.update()
        self.device.after_update_callback = after_update_callback

    def update(self):
        self.update_ha_state()

    @property
    def name(self):
        return self.device.name

    @property
    def is_on(self):
        """Return true if pin is high/on."""
        return self.device.state

    def turn_on(self):
        """Turn the pin to high/on."""
        self.device.set_on()

    def turn_off(self):
        """Turn the pin to low/off."""
        self.device.set_off()
