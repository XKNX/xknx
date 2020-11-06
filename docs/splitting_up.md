---
layout: default
title: Splitting up your configuration
nav_order: 1
parent: Configuration
---

# Splitting up your configuration

## Basic usage

XKNX is controlled via a configuration file. Per default the configuration file is named `xknx.yaml`. You can change this by providing the `config` option like so: `XKNX(config='xknx.yaml')`.

Throughout the time this configuration has grown a lot meaning that it can be really hard to maintain for bigger installations.

There are several ways to improve the readability of your configuration:

* `lights: !include lights.yaml` will load all lights from a dedicated `lights.yaml`.
* `host: !env_var XKNX_HOST 192.168.0.200` will load the host variable from an environment variable `XKNX_HOST` and if `XKNX_HOST` does not exist falls back to `192.168.0.200`.

## Advanced usage

There is one advanced method to load a whole directory of YAML files at once. Your files must have the `.yaml` file extension.

* `!include_dir_list` will return the complete content of a directory as a list with each file content being and entry in the list. The list entries are unordered.