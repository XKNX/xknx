"""Module for handling devices like Lights, Switches or Covers."""
# flake8: noqa
from .action import Action, ActionBase, ActionCallback
from .binary_sensor import BinarySensor, BinarySensorState
from .climate import Climate
from .climate_mode import ClimateMode
from .cover import Cover
from .datetime import DateTime, DateTimeBroadcastType
from .device import Device
from .devices import Devices
from .expose_sensor import ExposeSensor
from .fan import Fan
from .light import Light
from .notification import Notification
from .scene import Scene
from .sensor import Sensor
from .switch import Switch
from .travelcalculator import TravelCalculator, TravelStatus

device_types = dict(
		binary_sensor = BinarySensor,
		climate = Climate,
		cover = Cover,
		datetime = DateTime,
		expose_sensor = ExposeSensor,
		fan = Fan,
		light = Light,
		notification = Notification,
		scene = Scene,
		sensor = Sensor,
		switch = Switch,
)
