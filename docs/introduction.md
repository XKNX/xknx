---
layout: default
---

# [](#header-1)Introduction

# [](#header-2)Simple Example:

XKNX is using [asyncio](https://www.python.org/dev/peps/pep-3156/) for single-threaded concurrent code using coroutines.

This allows concurrency in a thread safe manner. 

```python
import asyncio
from xknx import XKNX

async def main():
    xknx = XKNX()
    await xknx.start()

    # USING THE XKNX OBJECT, e.g. for 
    # controlling lights, dimmers, shutters

    await xknx.stop()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

# [](#header-2)Explanation En Dé­tail:

```python
async def main():
```

`main()` function. The `async` qualifier markes the function asy an asyncio function. See [asyncio](https://www.python.org/dev/peps/pep-3156/) documentation for details.
 

```python
    xknx = XKNX()
```

Initialization of XKNX object. Constructor may take several arguments like a reference to the asyncio-loop or various callbacks for device updates or telegram received. See [XKNX object documentation](/xknx) for details.

````python
    await xknx.start()
```

Asynchronous start of the XKNX object. `xknx.start()` will connect to a KNX/IP device and either build a tunnel or connect through Mulitcast UDP.

```python
    await xknx.stop()
```

Asynchronous stop of the XKNX object. `xknx.stop()` will disconnect from Tunnels - which is important bc most of the devices have a limited amount of channels. 

```
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

Boilerplate code, for starting an asynchonous function. See [asyncio](https://www.python.org/dev/peps/pep-3156/) documentation for details.


_Important Note:_ If you are using Python 3.5 you have to replace the `await` syntax with the `@asyncio.coroutine` syntax.



