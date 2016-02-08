XKNX
====

A Wrapper around KNX/UDP protocol written in python.

This program only works with KNX/IP router.

Sample Configuration
--------------------

```yaml
devices:
    1.1.0: IP Router
    1.1.1: Pushbutton interface
    1.1.2: Switching actuator

    1.1.255: ETS

groups:
    1: Livingroom/Switch 1
    2: Livingroom/Switch 2
    3: Livingroom/Switch 3
    4: Livingroom/Switch 4

    65: Livingroom/Light 1
    66: Livingroom/Light 2
```

Sample Program
--------------

```python
#!/usr/bin/python3

from knx import Telegram,Multicast,BinaryInput,BinaryOutput
from knx import NameResolver,nameresolver_

def callback(telegram):

    if (telegram.group == nameresolver_.group_id("Livingroom/Switch 1") ):
        binaryinput = BinaryInput(telegram)

        if binaryinput.is_on():
            BinaryOutput("Livingroom/Light 1").set_on()

        elif binaryinput.is_off():
            BinaryOutput("Livingroom/Light 1").set_off()

    if (telegram.group == nameresolver_.group_id("Livingroom/Switch 2") ):
        binaryinput = BinaryInput(telegram)

        if binaryinput.is_on():
            BinaryOutput("Livingroom/Light 2").set_on()

        elif binaryinput.is_off():
            BinaryOutput("Livingroom/Light 2").set_off()


nameresolver_.init()
Multicast().recv(callback)
```
