import asyncio
import bisect
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple


class TimeToLiveDict:
    def __init__(self, ttl=60):
        self._ttl = ttl
        self._dict = {}
        self._timers = {}
        self._lock = Lock()
        self._loop = asyncio.get_event_loop()

    def set(self, key, value):
        async def async_set():
            if key in self._timers:
                self._timers[key].cancel()

            self._dict[key] = value
            self._timers[key] = self._loop.create_task(self._delete_after(key, self._ttl))

        with self._lock:
            self._loop.call_soon_threadsafe(lambda: self._loop.create_task(async_set()))

    def get(self, key):
        with self._lock:
            return self._dict.get(key)

    async def _delete_after(self, key, delay):
        await asyncio.sleep(delay)
        with self._lock:
            if key in self._dict:
                del self._dict[key]
                del self._timers[key]

    def set_ttl(self, key, ttl):
        async def async_set_ttl():
            if key in self._timers:
                self._timers[key].cancel()
                self._timers[key] = self._loop.create_task(self._delete_after(key, ttl))

        with self._lock:
            self._loop.call_soon_threadsafe(lambda: self._loop.create_task(async_set_ttl()))


class BlockToLiveDict:
    def __init__(self, retention_blocks: int = 100, cleanup_threshold: int = 100):
        self._retention_blocks = retention_blocks
        self._cleanup_threshold = cleanup_threshold
        self._data: Dict[Any, Tuple[Any, int]] = {}
        self._block_numbers: List[int] = []
        self._current_block: int = 0
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._insert_count: int = 0

    def set(self, key: Any, value: Any):
        asyncio.create_task(self._async_set(key, value, value.block_number))

    async def _async_set(self, key: Any, value: Any, block_number: int):
        async with self._lock:
            if key in self._data:
                old_block_number = self._data[key][1]
                self._block_numbers.remove(old_block_number)

            self._data[key] = (value, block_number)
            bisect.insort(self._block_numbers, block_number)

            self._current_block = max(self._current_block, block_number)
            self._insert_count += 1

            if self._insert_count >= self._cleanup_threshold:
                if self._cleanup_task is None or self._cleanup_task.done():
                    self._cleanup_task = asyncio.create_task(self._cleanup())
                self._insert_count = 0

    def get(self, key: Any) -> Optional[Any]:
        data = self._data.get(key)
        return data if data else None

    async def _cleanup(self):
        async with self._lock:
            cleanup_threshold = self._current_block - self._retention_blocks
            cleanup_index = bisect.bisect_right(self._block_numbers, cleanup_threshold)

            if cleanup_index > 0:
                blocks_to_remove = self._block_numbers[:cleanup_index]
                self._block_numbers = self._block_numbers[cleanup_index:]

                keys_to_remove = [key for key, data in self._data.items() if data[1] in blocks_to_remove]

                for key in keys_to_remove:
                    del self._data[key]

    def get_current_block(self) -> int:
        return self._current_block
