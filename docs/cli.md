---
layout: default
title: Command Line Interface
nav_order: 12
---

# [](#header-1)Command Line Interface

Installing xknx puts an `xknx` command on the path (also available via
`python -m xknx`). Run `xknx --help` or `xknx <command> --help` for all
options.

## [](#header-2)Discover gateways

Searches all network interfaces for KNX/IP gateways and prints their
addresses and capabilities. Exits non-zero when nothing was found.

```shell
xknx scan
xknx scan --local-ip 10.0.100.49 --timeout 5
```

## [](#header-2)Group communication

The `group` commands connect to the KNX installation - by gateway discovery,
or through a specific gateway with `--gateway` (UDP tunneling).

Read a group address value once and print it:

```shell
xknx group read 1/2/3
xknx group read 1/2/3 --type temperature
```

Write a value to a group address and wait for the bus confirmation.
Without `--type`, `on`/`off` and raw integers 0-63 are sent as 1-bit or
6-bit payloads; with `--type`, the value is encoded by that datapoint type.
Structured datapoint types take a JSON object:

```shell
xknx group write 1/2/3 on
xknx group write 1/2/3 21.5 --type temperature --gateway 10.0.0.10
xknx group write 1/2/3 '{"red": 255, "green": 0, "blue": 0}' --type 232.600
```

Print group telegrams from the bus until interrupted with Ctrl+C:

```shell
xknx group monitor
xknx group monitor --filter '1/2/*' --filter '1/4/5-6,8'
```

## [](#header-2)Environment variables

`--gateway` and `--local-ip` default to the `XKNX_GATEWAY` and
`XKNX_LOCAL_IP` environment variables; explicit options take precedence.

```shell
export XKNX_GATEWAY=10.0.0.10
xknx group read 1/2/3
```

## [](#header-2)Exit codes

- `0` on success
- `1` when the command failed (no response, no confirmation, no gateways
  found, connection errors)
- `2` for invalid command line arguments
- `130` when interrupted with Ctrl+C
