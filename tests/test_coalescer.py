import asyncio

import pytest

from app.coalescer import SingleFlight


@pytest.mark.asyncio
async def test_singleflight_deduplicates_concurrent_requests():

    singleflight = SingleFlight()

    calls = 0

    async def expensive_operation():

        nonlocal calls

        calls += 1

        await asyncio.sleep(0.1)

        return "result"

    tasks = [
        singleflight.do(
            "same-key",
            expensive_operation,
        )
        for _ in range(100)
    ]

    results = await asyncio.gather(*tasks)

    assert calls == 1
    assert len(results) == 100
    assert all(result == "result" for result in results)


@pytest.mark.asyncio
async def test_different_keys_execute_independently():

    singleflight = SingleFlight()

    calls = 0

    async def expensive_operation():

        nonlocal calls

        calls += 1

        await asyncio.sleep(0.05)

        return "result"

    results = await asyncio.gather(
        singleflight.do("key-1", expensive_operation),
        singleflight.do("key-2", expensive_operation),
    )

    assert calls == 2
    assert results == ["result", "result"]


@pytest.mark.asyncio
async def test_in_flight_requests_are_removed():

    singleflight = SingleFlight()

    async def operation():

        await asyncio.sleep(0.05)

        return "done"

    result = await singleflight.do(
        "test-key",
        operation,
    )

    assert result == "done"
    assert singleflight.in_flight_count() == 0
