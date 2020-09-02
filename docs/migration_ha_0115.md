---
layout: default
title: Migrating to HA 0.115.x
parent: Home Assistant Integration
nav_order: 1
---

# [](#header-1)Migrating to HA 0.115.x

Due to architecture decision [ADR-0007](https://github.com/home-assistant/architecture/blob/master/adr/0007-integration-config-yaml-structure.md) from Home Assistant we had to completely refactor
the way we handle YAML configuration in the KNX integration.

This was a great opportunity to also refactor other parts of the integration making it future proof for new features.

You will find all the necessary things here that you need in order to migrate your configuration to HA 0.155.x and above.

## [](#header-2)Configuration structure

If you've previously used the following config:

```yaml
knx:
  tunneling:
    host: '192.168.0.1'

switch:
  - platform: knx
    name: Switch
    address: '2/0/1'
    state_address: '2/0/2'
```

you will now need to configure the KNX integration like so:

```yaml
knx:
  tunneling:
    host: '192.168.0.1'
  switch:
    - name: Switch
      address: '2/0/1'
      state_address: '2/0/2'
```

Please be aware that this is true for all examples, not only switches but all other platforms that are supported in KNX.

You can still use the `!include` block in order to [split your configuration](https://www.home-assistant.io/docs/configuration/splitting_configuration/) and make it nice and tidy.



## [](#header-2)Automations with binary sensors

For a long time now it was possible to use the automation schema together with binary sensors. Due to the way this is integrated and in order
to be able to move to config flows (https://github.com/XKNX/xknx/issues/238) in the future we had to refactor this approach.

Instead of directly configuring the automation while defining the binary sensor you will now need to trigger your automation within
the standard automation definition from Home Assistant. This is much cleaner and easier to maintain in the future.

If you've previously defined your config like this:

```yaml
-  name: cover_abstell
   state_address: "2/0/33"
   automation:
     - counter: 1
       hook: 'on'
       action:
         - entity_id: cover.sonne_abstellkammer
           service: cover.open_cover
     - counter: 1
       hook: 'off'
       action:
         - entity_id: cover.sonne_abstellkammer
           service: cover.close_cover
```

you will need to _completely remove_ the `automation` section.

Your new binary sensor will now look like:

```yaml

- name: cover_abstell
  state_address: "2/0/33"

```

and your new automation will look like this:

```yaml

automation:
  - trigger:
      - platform: event
        event_type: knx_binary_sensor
        event_data:
            entity_id: "binary_sensor.cover_abstell"
            counter: 1
            state: "on"
    action:
      - service: cover.open_cover
        entity_id: cover.sonne_abstellkammer

  - trigger:
     - platform: event
       event_type: knx_binary_sensor
       event_data:
            entity_id: "binary_sensor.cover_abstell"
            counter: 1
            state: "off"
    action:
      - service: cover.close_cover
        entity_id: cover.sonne_abstellkammer

```
