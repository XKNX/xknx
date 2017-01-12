from homeassistant.components.climate import ClimateDevice
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE

class XKNXClimate(ClimateDevice):
    def __init__(self, hass, device):
        # pylint: disable=unused-argument
        self._unit_of_measurement = TEMP_CELSIUS
        self._away = False  # not yet supported
        self._is_fan_on = False  # not yet supported

        self.device = device

        self.register_callbacks()


    def register_callbacks(self):
        def after_update_callback(device):
            # pylint: disable=unused-argument
            self.update()
        self.device.after_update_callback = after_update_callback


    @property
    def should_poll(self):
        """Polling not needed """
        return False


    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement


    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.device.temperature


    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.device.setpoint


    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        self.device.setpoint = temperature

        #TODO Sent to KNX bus

        self.update_ha_state()


    def set_operation_mode(self, operation_mode):
        """Set operation mode."""
        raise NotImplementedError()


    def update(self):
        self.update_ha_state()


    @property
    def name(self):
        return self.device.name
