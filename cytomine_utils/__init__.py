"""Cytomine Utils."""

import time as _time

from ._utils import *

__version__ = "0.0.0"


async def _connect(timeout: int = 3):
    import asyncio
    import concurrent

    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    task = loop.run_in_executor(executor, connect)
    await asyncio.wait([task], timeout=timeout)
