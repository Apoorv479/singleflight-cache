import asyncio

import pytest

from app.cache import TTLCache
from app.coalescer import SingleFlight
from app.service import RecommendationService


@pytest.mark.asyncio
async def test_concurrent_requests_trigger_one_backend_call():

    cache = TTLCache(ttl=10)
    singleflight = SingleFlight()
    service = RecommendationService()

    async def request():

        key = "recommendations:123"

        cached = cache.get(key)

        if cached is not None:
            return cached

        async def operation():

            result = await service.fetch_recommendations("123")

            cache.set(key, result)

            return result

        return await singleflight.do(
            key,
            operation,
        )

    results = await asyncio.gather(
        *[request() for _ in range(100)]
    )

    assert len(results) == 100

    # Critical assertion:
    # 100 concurrent requests should result
    # in exactly one expensive backend call.
    assert service.backend_calls == 1


@pytest.mark.asyncio
async def test_cached_request_does_not_hit_backend():

    cache = TTLCache(ttl=10)
    singleflight = SingleFlight()
    service = RecommendationService()

    key = "recommendations:123"

    async def request():

        cached = cache.get(key)

        if cached is not None:
            return cached

        async def operation():

            result = await service.fetch_recommendations("123")
            cache.set(key, result)

            return result

        return await singleflight.do(
            key,
            operation,
        )

    # First request hits backend.
    await request()

    # Second request should use cache.
    await request()

    assert service.backend_calls == 1
