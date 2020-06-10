---
layout: default
---

# [](#header-1)Introduction

# [](#header-2)Simple Example:

XKNX is using [asyncio](https://www.python.org/dev/peps/pep-3156/) for single-threaded concurrent code using coroutines.

This allows concurrency in a thread safe manner. 

```python
import anyio
from xknx import XKNX

async def main():
    async with XKNX().run() as xknx:

        # USING THE XKNX OBJECT, e.g. for 
        # controlling lights, dimmers, shutters

anyio.run(main)
```

# [](#header-2)Explanation En Dé­tail:

```python
async def main():
```

`main()` function. The `async` qualifier markes `main` as an async function. See [asyncio](https://www.python.org/dev/peps/pep-3156/) and [anyio](https://anyio.readthedocs.io/) documentation for details.
 

```python
    async with XKNX().run() as xknx:
        pass
```

Initialization of XKNX object. The constructor may take several arguments like various callbacks for device updates or telegram received. See [XKNX object documentation](/xknx) for details.

For Python beginners: this construct is called an "asynchronous context manager". Within its scope (the indented code below it), "xknx" is your active connection. It is automatically stopped in a controlled manner when your code leaves the "async with" block, which is important as most devices have a limited amount of channels. 

````python
    await xknx.start()
```

Asynchronous start of the XKNX object. `xknx.start()` will connect to a KNX/IP device and either build a tunnel or connect through Mulitcast UDP.

This is a legacy method. Consider using an async context manager instead.

```python
    await xknx.stop()
```

Asynchronous stop of the XKNX object. `xknx.stop()` will disconnect from Tunnels - which is important bc most of the devices have a limited amount of channels. 

This is a legacy method. Consider using an async context manager instead.

```
anyio.run(main)
```

Boilerplate code, for starting an asynchonous function. See [anyio](https://anyio.readthedocs.io/) documentation for details.

