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