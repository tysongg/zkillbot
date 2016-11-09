import asyncio

from config import *
import zkill

if __name__ == '__main__':

    queue = zkill.RedisQ(redisq_url)

    task = asyncio.ensure_future(queue.get_kill_async())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(task)