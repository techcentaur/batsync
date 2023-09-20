import asyncio
from aiohttp import ClientSession
import pandas as pd

import os
from src.script import AsyncBatchLimiter

class BaseBatch:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def fetch_data(
        self, urls, session, retry_queue, response_queue, coin_id, data_type, limiter
    ):
        try:
            async with limiter:
                async with session.get(url) as response:
                    if response.status == 429:
                        await retry_queue.put((url, coin_id, data_type))
                    else:
                        data = await response.json()
                        await response_queue.put((coin_id, data_type, data))
        except Exception as e:
            L.error(f"An unknown error occurred for url: {url}  error: {e}")

    async def response_handler(self, response_queue):
        while True:
            coin_id, data_type, data = await response_queue.get()
            if coin_id is None:  # Stop signal
                break

            self.merge_data(coin_id)

    def merge_data(self, coin_id):
        pass

    async def run_batch_job(self):
        async with ClientSession() as session:
            retry_queue = asyncio.Queue()
            response_queue = asyncio.Queue()

            asyncio.create_task(self.response_handler(response_queue))

            limiter = AsyncLimiter(500, 60)

            tasks = []
            for coin_id in self.coin_list:
                pass


            await asyncio.gather(*tasks)

            await response_queue.put((None, None, None))
