#!/usr/bin/env python
"""
Example of a daemon listening for values from my main power-meter and resend them on a MQTT bus.

This example will not be able to run as it is - but it will hopefully give you some
ideas to how you can define DPT, and get their converted values, and even send them to MQTT
in a tested topic-format.

I have a Mosquitto MQTT Server - and running the Paho Python client.
I use some external MQTT libraries as well to handle the MQTT Topic-creation.

The data published on the MQTT bus can be fetched and stored in InfluxDB for graphing,
or monitored by other listeners - that triggers different events.

Please join XKNX on Discord (https://discord.gg/EuAQDXU) and chat with JohanElmis for
specific questions.
"""

from __future__ import print_function

# Disabling some Pylint checks as it assumes that the global variables are all constants.
# pylint: disable=invalid-name
# pylint: disable=global-statement

try:
    import asyncio

    from xknx import XKNX
    from xknx.devices import Sensor
    import sys
    import re
    # import time
    import paho.mqtt.client as mqtt
    # The following library is not included.
    from myhouse_sensors_mqtt import SensorClientMqtt
    from myhouse_sensors_mqtt import MetricType
    # import pprint
except ImportError as import_err:
    err_list = str(import_err).split(' ')
    print('Unable to import module: ' + err_list[3])
    print('Please install the ' + err_list[3] + ' module for Python.')
    sys.exit()

BROKER_ADDRESS = '127.0.0.1'
# Give this client a name on the MQTT bus.
mqttc = mqtt.Client('main_power_central')

# Library to deal with verification of values.
# It also triggers and send values to the MQTT bus if the values has changed.
# With no changes it can go up to max_interval_seconds before it's sent.
# This allows me to fetch fast changes without storing all data at a 15s interval.
mh_sensor = SensorClientMqtt(change_trigger_percent=5,
                             max_interval_seconds=600,
                             metric_class='sensor',
                             debug=True)

# Pre-compile some regexp filters that will be used to catch the different types.
RE_METER_READING = re.compile('MeterReading_')
RE_ACTIVE_POWER = re.compile('ActivePower')
RE_REACTIVE_POWER = re.compile('ReactivePower')
RE_APPARENT_POWER = re.compile('ApparentPower')
RE_VOLTAGE = re.compile('Voltage_')
RE_CURRENT = re.compile('Current_')
RE_FREQUENCY = re.compile('Frequency_')


@asyncio.coroutine
def device_updated_cb(device):
    """Do something with the updated device."""
    global mqttc

    # print(device.name + ' ' + str(device.resolve_state()) + ' ' + device.unit_of_measurement())
    topic = None
    value = None
    if re.search('^EL-T-O_', device.name):
        metric = str(device.name)[7:]
        value = device.resolve_state()
        if RE_ACTIVE_POWER.search(metric):
            topic = mh_sensor.get_mqtt_sensor_metric(MetricType.WATT, 'main_power_central', metric)
        elif RE_REACTIVE_POWER.search(metric):
            topic = mh_sensor.get_mqtt_sensor_metric(MetricType.VAR, 'main_power_central', metric)
        elif RE_APPARENT_POWER.search(metric):
            topic = mh_sensor.get_mqtt_sensor_metric(MetricType.VA, 'main_power_central', metric)
        elif RE_VOLTAGE.search(metric):
            topic = mh_sensor.get_mqtt_sensor_metric(MetricType.VOLTAGE, 'main_power_central', metric)
        elif RE_CURRENT.search(metric):
            topic = mh_sensor.get_mqtt_sensor_metric(MetricType.CURRENT, 'main_power_central', metric)
        elif RE_METER_READING.search(metric):
            topic = mh_sensor.get_mqtt_sensor_metric(MetricType.KWH, 'main_power_central', metric)
        elif RE_FREQUENCY:
            topic = mh_sensor.get_mqtt_sensor_metric(MetricType.CUSTOM, 'main_power_central', metric)
    else:
        print("Uncatched metric: " + device.name + ' ' + str(device.resolve_state()) +
              ' ' + device.unit_of_measurement())

    if topic and value:
        # This will create a topic like:
        # myhouse/sensor/KWH/main_power_central/MeterReading_ActiveEnergy 103150280
        # myhouse/sensor/WATT/main_power_central/ActivePower_L2 1028.1099853515625
        # myhouse/sensor/VAR/main_power_central/ReactivePower_L3 136.3699951171875
        # myhouse/sensor/VA/main_power_central/ApparentPower_L3 1449.919921875
        # myhouse/sensor/CURRENT/main_power_central/Current_L3 6.239999294281006

        # When storing it to InfluxDB I have a DB named 'myhouse' where all these values will be stored.
        # Then I use the next two fields as metric name (lowercase):  sensor/current
        # break out main_power_central as a tag 'location', and the last field is tagged as the
        # 'sensor': ApparentPower_L3

        # This makes it really easy to graph in for example Grafana.
        # My latest version of the library doesn't send the value after the MQTT Topic, but a JSON structure
        # that also contains time.

        print(topic + ' ' + str(value))
        # ts = int(time.time() * 1000)
        mqttc.publish(topic, value)


async def main():
    """
    KNX device objects are created and the MQTT server connection is established.

    Then the XKNX Daemon will be started.
    Then everything else happens in the device_updated-function above as it is triggered when we receive data.
    """
    global mqttc

    # Connect to KNX/IP device and listen if a switch was updated via KNX bus.
    xknx = XKNX(device_updated_cb=device_updated_cb)

    # The KNX addresses to monitor are defined below, but is normally placed in an external
    #  file that is loaded in on start.

    # Generic Types not specifically supported by XKNX
    el_meter_reading_active_energy = Sensor(
        xknx, 'EL-T-O_MeterReading_ActiveEnergy', group_address_state='5/6/11', value_type="DPT-13")
    xknx.devices.add(el_meter_reading_active_energy)
    el_meter_reading_reactive_energy = Sensor(
        xknx, 'EL-T-O_MeterReading_ReactiveEnergy', group_address_state='5/6/16', value_type="DPT-13")
    xknx.devices.add(el_meter_reading_reactive_energy)

    # Active Power
    el_total_active_power = Sensor(
        xknx, 'EL-T-O_TotalActivePower', group_address_state='5/6/24', value_type="power")
    xknx.devices.add(el_total_active_power)
    el_active_power_l1 = Sensor(
        xknx, 'EL-T-O_ActivePower_L1', group_address_state='5/6/25', value_type="power")
    xknx.devices.add(el_active_power_l1)
    # ...

    # Reactive Power
    el_total_reactive_power = Sensor(
        xknx, 'EL-T-O_TotalReactivePower', group_address_state='5/6/28', value_type="power")
    xknx.devices.add(el_total_reactive_power)
    el_reactive_power_l1 = Sensor(
        xknx, 'EL-T-O_ReactivePower_L1', group_address_state='5/6/29', value_type="power")
    xknx.devices.add(el_reactive_power_l1)
    # ...

    # Apparent Power
    el_total_apparent_power = Sensor(
        xknx, 'EL-T-O_TotalReactivePower', group_address_state='5/6/32', value_type="power")
    xknx.devices.add(el_total_apparent_power)
    el_apparent_power_l1 = Sensor(
        xknx, 'EL-T-O_ApparentPower_L1', group_address_state='5/6/33', value_type="power")
    xknx.devices.add(el_apparent_power_l1)
    # ...

    # Current
    el_current_l1 = Sensor(
        xknx, 'EL-T-O_Current_L1', group_address_state='5/6/45', value_type="electric_current")
    xknx.devices.add(el_current_l1)
    # ...

    # Voltage
    el_voltage_l1 = Sensor(
        xknx, 'EL-T-O_Voltage_L1-N', group_address_state='5/6/48', value_type="electric_potential")
    xknx.devices.add(el_voltage_l1)
    # ...

    # Frequency
    el_frequency = Sensor(
        xknx, 'EL-T-O_Frequency', group_address_state='5/6/53', value_type="frequency")
    xknx.devices.add(el_frequency)

    mqttc.connect(BROKER_ADDRESS, 8883, 60)
    mqttc.loop_start()

    # Wait until Ctrl-C was pressed
    await xknx.start(daemon_mode=True)

    await xknx.stop()
    await mqttc.loop_stop()
    await mqttc.disconnect()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
