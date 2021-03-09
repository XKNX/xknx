'use strict';

let source, result, wrap_knx, sort_keys;

window.onload = function () {
  source = CodeMirror.fromTextArea(document.getElementById('source'), {
    mode: 'yaml',
    lineNumbers: true
  });
  result = CodeMirror.fromTextArea(document.getElementById('result'), {
    mode: 'yaml',
    lineNumbers: true
  });
  wrap_knx = document.getElementById('wrap_knx');
  sort_keys = document.getElementById('sort_keys');

  var timer;

  source.on('change', function () {
    clearTimeout(timer);
    timer = setTimeout(parse, 500);
  });

  wrap_knx.addEventListener('change', (event) => {
    clearTimeout(timer);
    timer = setTimeout(parse, 500);
  })

  sort_keys.addEventListener('change', (event) => {
    clearTimeout(timer);
    timer = setTimeout(parse, 500);
  })
}

function parse() {
  var newObj;
  let oldStr, oldObj, newYaml;
  let wrap_knx_checked = document.getElementById('wrap_knx').checked;
  let sort_keys_checked = document.getElementById('sort_keys').checked;

  try {
    oldStr = source.getValue();
    oldObj = jsyaml.load(oldStr);

    newObj = parseOldConfig(oldObj);
    if (Object.keys(newObj).length === 0) {
      result.setOption('mode', 'yaml');
      result.setValue("");
      return;
    }

    if (wrap_knx_checked) {
      newObj = { knx: newObj };
    }

    newYaml = jsyaml.dump(newObj, {
      'styles': {
        '!!null': 'canonical' // dump null as ~
      },
      'sortKeys': sort_keys_checked // sort object keys
    });

    result.setOption('mode', 'yaml');
    result.setValue(newYaml);
  } catch (err) {
    result.setOption('mode', 'text/plain');
    result.setValue(err.message || String(err));
  }

}

function parseOldConfig(oldConfig) {
  var newConfig = {}
  var invalid = []
  let info_text = document.getElementById('info_text')

  if (typeof oldConfig === 'string') {
    info_text.value = "No key found in source.";
    return {};
  }

  for (let key in oldConfig) {
    switch (key) {
      case "general":
        parseGeneral(oldConfig.general, newConfig, invalid);
        break;
      case "connection":
        parseConnection(oldConfig.connection, newConfig, invalid);
        break;
      case "groups":
        parseGroups(oldConfig.groups, newConfig, invalid);
        break;
      default:
        invalid.push(key);
    }
  }
  console.log(newConfig);
  console.log(invalid);
  if (invalid.length) {
    invalid.unshift("Invalid keys found. They are removed form converted config.\nInvalid config keys have been ignored by xknx so your new config should work just like before.")
    for (let item of invalid) {
      if (item.endsWith("actions")) {
        invalid[0] += "\nNOTE: Actions in BinarySensors are not supported anymore. Use a HomeAssistant Automation instead.";
        break;
      }
    }
    info_text.value = invalid.join("\n  - ");
  } else {
    info_text.value = "Conversion succeded.";
  }

  return newConfig;
}

function parseGeneral(generalConfig, newConfig, invalid) {
  for (let general_key in generalConfig) {
    switch (general_key) {
      case "own_address":
        newConfig.individual_address = generalConfig.own_address;
        break;
      case "rate_limit":
        newConfig.rate_limit = generalConfig.rate_limit;
        break;
      case "multicast_group":
        newConfig.multicast_group = generalConfig.multicast_group;
        break;
      case "multicast_port":
        newConfig.multicast_port = generalConfig.multicast_port;
        break;
      default:
        invalid.push("general: " + general_key);
    }
  }
}

function parseConnection(connectionConfig, newConfig, invalid) {
  for (var connection_key in connectionConfig) {
    switch (connection_key) {
      case "tunneling":
        newConfig.tunneling = {};
        for (let tunneling_key in connectionConfig.tunneling) {
          switch (tunneling_key) {
            case "gateway_ip":
              newConfig.tunneling.host = connectionConfig.tunneling.gateway_ip;
              break;
            case "gateway_port":
              newConfig.tunneling.port = connectionConfig.tunneling.gateway_port;
              break;
            case "local_ip":
              newConfig.tunneling.local_ip = connectionConfig.tunneling.local_ip;
              break;
            default:
              invalid.push("connection: tunneling: " + tunneling_key);
          }
        }
        break;
      case "routing":
        newConfig.routing = null;
        for (let routing_key in connectionConfig.routing) {
          switch (routing_key) {
            case "local_ip":
              newConfig.routing = {};
              newConfig.routing.local_ip = connectionConfig.routing.local_ip;
              break;
            default:
              invalid.push("connection: routing: " + routing_key)
          }
        }
        break;
      case "auto":
        // ignore auto
        break;
      default:
        invalid.push("connection: " + connection_key);
    }
  }
}

function parseGroups(groups, newConfig, invalid) {
  var platforms = {
    expose: [],
    binary_sensor: [],
    climate: [],
    cover: [],
    fan: [],
    light: [],
    notify: [],
    scene: [],
    sensor: [],
    switch: [],
    weather: [],
  }

  for (let group in groups) {
    if (group.startsWith("binary_sensor")) {
      for (let device in groups[group]) {
        platforms.binary_sensor.push(parseBinarySensor(device, groups[group][device], invalid, group))
      }
    } else if (group.startsWith("climate")) {
      for (let device in groups[group]) {
        platforms.climate.push(parseClimate(device, groups[group][device], invalid, group))
      }
    } else if (group.startsWith("cover")) {
      for (let device in groups[group]) {
        platforms.cover.push(parseCover(device, groups[group][device], invalid, group))
      }
    } else if (group.startsWith("datetime")) {
      for (let device in groups[group]) {
        platforms.expose.push(parseDateTime(device, groups[group][device], invalid, group))
      }
    } else if (group.startsWith("fan")) {
      for (let device in groups[group]) {
        platforms.fan.push(parseFan(device, groups[group][device], invalid, group))
      }
    } else if (group.startsWith("light")) {
      for (let device in groups[group]) {
        platforms.light.push(parseLight(device, groups[group][device], invalid, group))
      }
    } else if (group.startsWith("notification")) {
      for (let device in groups[group]) {
        platforms.notify.push(parseNotify(device, groups[group][device], invalid, group))
      }
    } else if (group.startsWith("scene")) {
      for (let device in groups[group]) {
        platforms.scene.push(parseScene(device, groups[group][device], invalid, group))
      }
    } else if (group.startsWith("sensor")) {
      for (let device in groups[group]) {
        platforms.sensor.push(parseSensor(device, groups[group][device], invalid, group))
      }
    } else if (group.startsWith("switch")) {
      for (let device in groups[group]) {
        platforms.switch.push(parseSwitch(device, groups[group][device], invalid, group))
      }
    } else if (group.startsWith("weather")) {
      for (let device in groups[group]) {
        platforms.weather.push(parseWeather(device, groups[group][device], invalid, group))
      }
    } else {
      invalid.push("groups: " + group);
    }
  }

  for (let platform in platforms) {
    if (platforms[platform].length) {
      newConfig[platform] = platforms[platform];
    }
  }
}

/////////////
// PLATFORMS
////////////

function parseBinarySensor(name, device, invalid, groupname) {
  let entity = { name: name }

  for (let conf in device) {
    switch (conf) {
      case "group_address_state":
        entity.state_address = device[conf]
        break;
      case "sync_state":
        entity[conf] = device[conf]
        break;
      case "invert":
        entity[conf] = device[conf]
        break;
      case "ignore_internal_state":
        entity[conf] = device[conf]
        break;
      case "context_timeout":
        entity[conf] = device[conf]
        break;
      case "reset_after":
        entity[conf] = device[conf]
        break;
      case "device_class":
        entity[conf] = device[conf]
        break;
      default:
        invalid.push("groups: " + groupname + ": " + name + ": " + conf);
    }
  }
  return entity
}

function parseClimate(name, device, invalid, groupname) {
  let entity = { name: name }

  for (let conf in device) {
    switch (conf) {
      case "group_address_temperature":
        entity.temperature_address = device[conf];
        break;
      case "group_address_target_temperature":
        entity.target_temperature_address = device[conf];
        break;
      case "group_address_target_temperature_state":
        entity.target_temperature_state_address = device[conf];
        break;
      case "group_address_setpoint_shift":
        entity.setpoint_shift_address = device[conf];
        break;
      case "group_address_setpoint_shift_state":
        entity.setpoint_shift_state_address = device[conf];
        break;
      case "setpoint_shift_mode":
        entity[conf] = device[conf];
        break;
      case "setpoint_shift_max":
        entity[conf] = device[conf];
        break;
      case "setpoint_shift_min":
        entity[conf] = device[conf];
        break;
      case "temperature_step":
        entity[conf] = device[conf];
        break;
      case "group_address_on_off":
        entity.on_off_address = device[conf];
        break;
      case "group_address_on_off_state":
        entity.on_off_state_address = device[conf];
        break;
      case "on_off_invert":
        entity[conf] = device[conf];
        break;
      case "min_temp":
        entity[conf] = device[conf];
        break;
      case "max_temp":
        entity[conf] = device[conf];
        break;
      case "mode":
        for (let mode_conf in device.mode) {
          switch (mode_conf) {
            case "group_address_operation_mode":
              entity.operation_mode_address = device.mode[mode_conf];
              break;
            case "group_address_operation_mode_state":
              entity.operation_mode_state_address = device.mode[mode_conf];
              break;
            case "group_address_operation_mode_protection":
              entity.operation_mode_frost_protection_address = device.mode[mode_conf];
              break;
            case "group_address_operation_mode_night":
              entity.operation_mode_night_address = device.mode[mode_conf];
              break;
            case "group_address_operation_mode_comfort":
              entity.operation_mode_comfort_address = device.mode[mode_conf];
              break;
            case "group_address_operation_mode_standby":
              entity.operation_mode_standby_address = device.mode[mode_conf];
              break;
            case "group_address_controller_status":
              entity.controller_status_address = device.mode[mode_conf];
              break;
            case "group_address_controller_status_state":
              entity.controller_status_state_address = device.mode[mode_conf];
              break;
            case "group_address_controller_mode":
              entity.controller_mode_address = device.mode[mode_conf];
              break;
            case "group_address_controller_mode_state":
              entity.controller_mode_state_address = device.mode[mode_conf];
              break;
            case "group_address_heat_cool":
              entity.heat_cool_address = device.mode[mode_conf];
              break;
            case "group_address_heat_cool_state":
              entity.heat_cool_state_address = device.mode[mode_conf];
              break;
            default:
              invalid.push("groups: " + groupname + ": " + name + ": mode: " + mode_conf);
          }
        }
        break;
      default:
        invalid.push("groups: " + groupname + ": " + name + ": " + conf);
    }
  }
  return entity
}

function parseCover(name, device, invalid, groupname) {
  let entity = { name: name }

  for (let conf in device) {
    switch (conf) {
      case "group_address_long":
        entity.move_long_address = device[conf]
        break;
      case "group_address_short":
        entity.move_short_address = device[conf]
        break;
      case "group_address_stop":
        entity.stop_address = device[conf]
        break;
      case "group_address_position":
        entity.position_address = device[conf]
        break;
      case "group_address_position_state":
        entity.position_state_address = device[conf]
        break;
      case "group_address_angle":
        entity.angle_address = device[conf]
        break;
      case "group_address_angle_state":
        entity.angle_state_address = device[conf]
        break;
      case "travel_time_down":
        entity.travelling_time_down = device[conf]
        break;
      case "travel_time_up":
        entity.travelling_time_up = device[conf]
        break;
      case "invert_position":
        entity[conf] = device[conf]
        break;
      case "invert_angle":
        entity[conf] = device[conf]
        break;
      case "device_class":
        entity[conf] = device[conf]
        break;
      default:
        invalid.push("groups: " + groupname + ": " + name + ": " + conf);
    }
  }
  return entity
}

function parseDateTime(name, device, invalid, groupname) {
  let entity = { type: "time" }

  for (let conf in device) {
    switch (conf) {
      case "group_address":
        entity.address = device[conf]
        break;
      case "broadcast_type":
        entity.type = device[conf]
        break;
      default:
        invalid.push("groups: " + groupname + ": " + name + ": " + conf);
    }
  }
  return entity
}

function parseFan(name, device, invalid, groupname) {
  let entity = { name: name }

  for (let conf in device) {
    switch (conf) {
      case "group_address_speed":
        entity.address = device[conf]
        break;
      case "group_address_speed_state":
        entity.state_address = device[conf]
        break;
      case "group_address_oscillation":
        entity.oscillation_address = device[conf]
        break;
      case "group_address_oscillation_state":
        entity.oscillation_state_address = device[conf]
        break;
      case "max_step":
        entity[conf] = device[conf]
        break;
      default:
        invalid.push("groups: " + groupname + ": " + name + ": " + conf);
    }
  }
  return entity
}

function parseLight(name, device, invalid, groupname) {
  let entity = { name: name }

  for (let conf in device) {
    switch (conf) {
      case "group_address_switch":
        entity.address = device[conf]
        break;
      case "group_address_switch_state":
        entity.state_address = device[conf]
        break;
      case "group_address_brightness":
        entity.brightness_address = device[conf]
        break;
      case "group_address_brightness_state":
        entity.brightness_state_address = device[conf]
        break;
      case "group_address_color":
        entity.color_address = device[conf]
        break;
      case "group_address_color_state":
        entity.color_state_address = device[conf]
        break;
      case "group_address_rgbw":
        entity.rgbw_address = device[conf]
        break;
      case "group_address_rgbw_state":
        entity.rgbw_state_address = device[conf]
        break;
      case "group_address_tunable_white":
        entity.color_temperature_address = device[conf]
        entity.color_temperature_mode = "relative"
        break;
      case "group_address_tunable_white_state":
        entity.color_temperature_state_address = device[conf]
        break;
      case "group_address_color_temperature":
        entity.color_temperature_address = device[conf]
        entity.color_temperature_mode = "absolute"
        break;
      case "group_address_color_temperature_state":
        entity.color_temperature_state_address = device[conf]
        break;
      case "min_kelvin":
        entity[conf] = device[conf]
        break;
      case "max_kelvin":
        entity[conf] = device[conf]
        break;
      case "individual_colors":
        entity.individual_colors = {}
        for (let color in device.individual_colors) {
          entity.individual_colors[color] = {}
          for (let color_config in device.individual_colors[color]) {
            switch (color_config) {
              case "group_address_switch":
                entity.individual_colors[color]["address"] = device.individual_colors[color][color_config]
                break;
              case "group_address_switch_state":
                entity.individual_colors[color]["state_address"] = device.individual_colors[color][color_config]
                break;
              case "group_address_brightness":
                entity.individual_colors[color]["brightness_address"] = device.individual_colors[color][color_config]
                break;
              case "group_address_brightness_state":
                entity.individual_colors[color]["brightness_state_address"] = device.individual_colors[color][color_config]
                break;
            }
          }
        }
        break;
      default:
        invalid.push("groups: " + groupname + ": " + name + ": " + conf);
    }
  }
  return entity
}

function parseNotify(name, device, invalid, groupname) {
  let entity = { name: name }

  for (let conf in device) {
    switch (conf) {
      case "group_address":
        entity.address = device[conf]
        break;
      default:
        invalid.push("groups: " + groupname + ": " + name + ": " + conf);
    }
  }
  return entity
}

function parseScene(name, device, invalid, groupname) {
  let entity = { name: name }

  for (let conf in device) {
    switch (conf) {
      case "group_address":
        entity.address = device[conf]
        break;
      case "scene_number":
        entity[conf] = device[conf]
        break;
      default:
        invalid.push("groups: " + groupname + ": " + name + ": " + conf);
    }
  }
  return entity
}

function parseSensor(name, device, invalid, groupname) {
  let entity = { name: name }

  for (let conf in device) {
    switch (conf) {
      case "group_address_state":
        entity.state_address = device[conf]
        break;
      case "value_type":
        entity.type = device[conf]
        break;
      case "sync_state":
        entity[conf] = device[conf]
        break;
      case "always_callback":
        entity[conf] = device[conf]
        break;
      default:
        invalid.push("groups: " + groupname + ": " + name + ": " + conf);
    }
  }
  return entity
}

function parseSwitch(name, device, invalid, groupname) {
  let entity = { name: name }

  for (let conf in device) {
    switch (conf) {
      case "group_address":
        entity.address = device[conf]
        break;
      case "group_address_state":
        entity.state_address = device[conf]
        break;
      case "invert":
        entity[conf] = device[conf]
        break;
      default:
        invalid.push("groups: " + groupname + ": " + name + ": " + conf);
    }
  }
  return entity
}

function parseWeather(name, device, invalid, groupname) {
  let entity = { name: name }

  for (let conf in device) {
    switch (conf) {
      case "group_address_temperature":
        entity.address_temperature = device[conf]
        break;
      case "group_address_brightness_south":
        entity.address_brightness_south = device[conf]
        break;
      case "group_address_brightness_north":
        entity.address_brightness_north = device[conf]
        break;
      case "group_address_brightness_west":
        entity.address_brightness_west = device[conf]
        break;
      case "group_address_brightness_east":
        entity.address_brightness_east = device[conf]
        break;
      case "group_address_wind_speed":
        entity.address_wind_speed = device[conf]
        break;
      case "group_address_wind_bearing":
        entity.address_wind_bearing = device[conf]
        break;
      case "group_address_rain_alarm":
        entity.address_rain_alarm = device[conf]
        break;
      case "group_address_frost_alarm":
        entity.address_frost_alarm = device[conf]
        break;
      case "group_address_wind_alarm":
        entity.address_wind_alarm = device[conf]
        break;
      case "group_address_day_night":
        entity.address_day_night = device[conf]
        break;
      case "group_address_air_pressure":
        entity.address_air_pressure = device[conf]
        break;
      case "group_address_humidity":
        entity.address_humidity = device[conf]
        break;
      case "expose_sensors":
        entity.create_sensors = device[conf]
        break;
      case "sync_state":
        entity[conf] = device[conf]
        break;
      default:
        invalid.push("groups: " + groupname + ": " + name + ": " + conf);
    }
  }
  return entity
}

