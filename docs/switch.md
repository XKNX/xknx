---
layout: default
---

# [](#header-1)Switches

## [](#header-2)Overview

Switches are simple representations of binary actors. They mainly support switching on and off.

## [](#header-2)Example

```python
switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
xknx.devices.add(switch)

# Accessing switch
await xknx.devices['TestOutlet'].set_on()
``` 

## [](#header-2)Configuration via **xknx.yaml**

Switches are usually configured via [`xknx.yaml`](/configuration):

```yaml
groups:
    switch:
        Livingroom.Outlet_1: {group_address: '1/3/1'}
        Livingroom.Outlet_2: {group_address: '1/3/2'} 
```

## [](#header-2)Interface


```python
switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')

# Switching switch on
await switch.set_on()

# Switching switch off
await switch.set_off()

# Accessing switch via 'do'
await switch.do('on')
await switch.do('off')

# Accessing state
print(switch.state)

# Requesting state via KNX GROUP WRITE
await switch.sync()
```


