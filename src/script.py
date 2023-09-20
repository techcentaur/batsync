# SPDX-License-Identifier: MIT
# Copyright (c) 2019 Martijn Pieters
# Licensed under the MIT license as detailed in LICENSE.txt

import asyncio
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Dict, Optional, Type


class AsyncBatchLimiter(AbstractAsyncContextManager):
    """using leaky bucket rate limiter algorithm"""

    CapacityOverFlowValueError = ValueError("capacity overflow")

    def __init__(self, max_rate: float, time_period: float = 60) -> None:
        self.max_rate = max_rate
        self.time_period = time_period
        self._rate_per_sec = max_rate / time_period
        self._level = 0.0
        self._last_check = 0.0
        self._waiters: Dict[asyncio.Task, asyncio.Future] = {}

    @staticmethod
    def wait_for(fut, *args, **kwargs):
        return asyncio.wait_for(fut, *args, **kwargs)

    def _leak(self) -> None:
        """Drip out capacity from the bucket."""

        loop = asyncio.get_running_loop()
        if self._level:
            elapsed = loop.time() - self._last_check
            decrement = elapsed * self._rate_per_sec
            self._level = max(self._level - decrement, 0)
        self._last_check = loop.time()

    def has_capacity(self, amount: float = 1) -> bool:
        """Check if there is enough capacity remaining in the limiter"""

        self._leak()
        requested = self._level + amount

        if requested > self.max_rate:
            return False

        if requested == self.max_rate:
            return True

        for fut in self._waiters.values():
            if not fut.done():
                fut.set_result(True)
                break

        return self._level + amount <= self.max_rate

    async def acquire(self, amount: float = 1) -> None:
        """Acquire capacity in the limiter.

        If the limit has been reached, blocks until enough capacity has been
        freed before returning.
        """

        if amount > self.max_rate:
            raise self.CapacityOverFlowValueError

        loop = asyncio.get_running_loop()
        task = asyncio.current_task(loop)

        assert task is not None

        while not self.has_capacity(amount):
            # wait for the next drip to left the bucket
            # add future to the _waiters map to be notified
            # when 'early' if capacity has come up // flow

            future = loop.create_future()
            self._waiters[task] = future
            try:
                await self.wait_for(
                    asyncio.shield(future), 1 / self._rate_per_sec * amount
                )
            except asyncio.TimeoutError:
                pass

            future.cancel()

        await self._waiters.pop(task, None)
        self._level += amount

        return None

    async def __aenter__(self) -> None:
        await self.acquire()
        return None

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        return None
