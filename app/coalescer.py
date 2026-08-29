import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class SingleFlight:
    """
    Prevents duplicate concurrent work for the same key.

    When multiple requests ask for the same resource while
    an operation is already running, only the first request
    executes the operation. Other requests wait for the same
    Future and receive the shared result.
    """

    def __init__(self):
        self._in_flight: dict[str, asyncio.Future[Any]] = {}
        self._lock = asyncio.Lock()

    async def do(
        self,
        key: str,
        fn: Callable[[], Awaitable[Any]],
    ) -> Any:

        async with self._lock:
            existing = self._in_flight.get(key)

            if existing is not None:
                future = existing
                is_leader = False
            else:
                future = asyncio.get_running_loop().create_future()
                self._in_flight[key] = future
                is_leader = True

        # Another request is already executing this operation.
        if not is_leader:
            return await future

        try:
            result = await fn()

            if not future.done():
                future.set_result(result)

            return result

        except Exception as exc:
            if not future.done():
                future.set_exception(exc)

            raise

        finally:
            async with self._lock:
                if self._in_flight.get(key) is future:
                    del self._in_flight[key]

    def in_flight_count(self) -> int:
        return len(self._in_flight)
