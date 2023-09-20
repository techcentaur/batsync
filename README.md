# batsync
Efficient Rate Limited Batch Processing Async Manager

### logic

if you have list of 10k URLs to request, with (x,y,z) <- URLs needed to return response
and you want to do it async with rate limit use

```python
from batsync import BatSync

bs = BatSync(URLs: [[]], rate_limit: int, timeout: int, max_tries: int, max_workers: int)

async with bs:
    


```



#### usage
python3.8 onwards (asyncio.wait_for deprecated)


#### note
- if you want to "type define" in functions for future, you can do something like

```python
from typing import (Any, Awaitable, Generator, TypeVar, Union)

_T = TypeVar("_T")
_FutureLike = Union["asyncio.Future[_T]", Generator[Any, None, _T], Awaitable[_T]]


```