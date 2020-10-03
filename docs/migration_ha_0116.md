---
layout: default
title: Migrating to HA 0.116.x
parent: Home Assistant Integration
nav_order: 2
---

# [](#header-1)Migrating to HA 0.116.x

We did some refactoring for binary sensors in order to comply with current Home Assistant standards. Please find them below.

## [](#header-2)Binary sensor tweaks

We've changed the default behavior of the `ignore_internal_state` attribute. It now defaults to `True` instead of `False`.

If you encounter issues with your current automations please set it to `False` again. We've analysed the current state
and it appears that most of the people using it have it set to `True`.

The binary sensor now has an additional `context_timeout` attribute which allows to define a time period
in which your clicks should be counted towards the current context (i.e. incrementing the counter variable that you can
use in your automations).

## [](#header-2)Migrating automations with binary sensors

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
  context_timeout: 1.0

```

and your new automation will look like this:

```yaml

automation:
  - alias: 'Binary sensor test counter=1 on'
    trigger:
      platform: numeric_state
      entity_id: binary_sensor.cover_abstell
      attribute: counter
      above: 0
      below: 2
    condition:
      - condition: state
        entity_id: binary_sensor.cover_abstell
        state: 'on'
    action:
      - service: cover.open_cover
        entity_id: cover.sonne_abstellkammer

  - alias: 'Binary sensor test counter=1 off'
    trigger:
      platform: numeric_state
      entity_id: binary_sensor.cover_abstell
      attribute: counter
      above: 0
      below: 2
    condition:
      - condition: state
        entity_id: binary_sensor.cover_abstell
        state: 'off'
    action:
      - service: cover.close_cover
        entity_id: cover.sonne_abstellkammer

```

If you intend to use the `counter` feature (counter > 1) make sure you also enable `ignore_internal_state`
for your binary_sensor and set the `context_timeout` attribute to the time in between you want it to react to your
sensor clicks (defaults to None - which disables this feature). Otherwise the counter will _not_ work correctly.