import asyncio
import bisect
import queue
from dataclasses import dataclass
from threading import Lock, Thread
from typing import Any, Dict, List, Optional


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


@dataclass
class ValueWithBlockNumber:
    value: Any
    block_number: int


class BlockToLiveDict:
    def __init__(self, retention_blocks: int = 100, cleanup_threshold: int = 100):
        self._retention_blocks = retention_blocks
        self._cleanup_threshold = cleanup_threshold
        self._data: Dict[Any, ValueWithBlockNumber] = {}
        self._block_numbers: List[int] = []
        self._block_to_keys: Dict[int, set] = {}
        self._current_block: int = 0
        self._lock = Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._insert_count: int = 0
        self._cleanup_queue = queue.Queue()
        self._cleanup_thread = Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def set(self, key: Any, value: Any):
        if not hasattr(value, 'block_number'):
            raise AttributeError(f"'{key}' object has no attribute 'block_number'")

        with self._lock:
            if key in self._data:
                old_block_number = self._data[key].block_number
                if old_block_number == value.block_number:
                    self._data[key].value = value
                    return

                self._block_to_keys[old_block_number].remove(key)
                if not self._block_to_keys[old_block_number]:
                    del self._block_to_keys[old_block_number]
                    self._block_numbers.remove(old_block_number)

            self._data[key] = ValueWithBlockNumber(value, value.block_number)

            if value.block_number not in self._block_to_keys:
                self._block_to_keys[value.block_number] = set()
                bisect.insort(self._block_numbers, value.block_number)
            self._block_to_keys[value.block_number].add(key)

            self._current_block = max(self._current_block, value.block_number)
            self._insert_count += 1

            if self._insert_count >= self._cleanup_threshold:
                self._cleanup_queue.put(True)
                self._insert_count = 0

    def get(self, key: Any) -> Optional[Any]:
        data = self._data.get(key)
        return data.value if data else None

    def _cleanup(self):
        with self._lock:
            cleanup_threshold = self._current_block - self._retention_blocks
            cleanup_index = bisect.bisect_right(self._block_numbers, cleanup_threshold)

            if cleanup_index > 0:
                blocks_to_remove = self._block_numbers[:cleanup_index]
                self._block_numbers = self._block_numbers[cleanup_index:]

                for block in blocks_to_remove:
                    keys_to_remove = self._block_to_keys.pop(block, set())
                    for key in keys_to_remove:
                        del self._data[key]

    def _cleanup_loop(self):
        while True:
            self._cleanup_queue.get()  # 等待清理信号
            self._cleanup()
            self._cleanup_queue.task_done()

    def get_current_block(self) -> int:
        return self._current_block

    def __del__(self):
        if hasattr(self, '_cleanup_thread'):
            self._cleanup_queue.put(None)  # 发送退出信号
            self._cleanup_thread.join(timeout=1)
