import asyncio
import time

from app.cache import TTLCache
from app.coalescer import SingleFlight
from app.service import RecommendationService


CONCURRENT_REQUESTS = [10, 50, 100, 500]


async def baseline_benchmark(requests: int):
    """
    Baseline implementation.

    Every request directly executes the expensive
    backend operation.
    """

    service = RecommendationService()

    async def request():
        return await service.fetch_recommendations("123")

    start = time.perf_counter()

    await asyncio.gather(
        *[request() for _ in range(requests)]
    )

    elapsed = time.perf_counter() - start

    return {
        "requests": requests,
        "backend_calls": service.backend_calls,
        "time": elapsed,
    }


async def singleflight_benchmark(requests: int):
    """
    SingleFlight implementation.

    Concurrent requests for the same key share
    one in-flight backend operation.
    """

    service = RecommendationService()
    singleflight = SingleFlight()

    # Cache is intentionally disabled for this benchmark.
    # We want to measure request coalescing itself.
    cache = TTLCache(ttl=10)

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

    start = time.perf_counter()

    await asyncio.gather(
        *[request() for _ in range(requests)]
    )

    elapsed = time.perf_counter() - start

    return {
        "requests": requests,
        "backend_calls": service.backend_calls,
        "time": elapsed,
    }


def print_result(name: str, result: dict):
    print(
        f"{name:<15} | "
        f"Requests: {result['requests']:<4} | "
        f"Backend calls: {result['backend_calls']:<4} | "
        f"Time: {result['time']:.4f}s"
    )


async def main():

    print()
    print("=" * 75)
    print("SingleFlight Cache Performance Benchmark")
    print("=" * 75)
    print()

    for requests in CONCURRENT_REQUESTS:

        baseline = await baseline_benchmark(requests)

        optimized = await singleflight_benchmark(requests)

        backend_reduction = (
            1
            - optimized["backend_calls"]
            / baseline["backend_calls"]
        ) * 100

        speedup = (
            baseline["time"] / optimized["time"]
            if optimized["time"] > 0
            else 0
        )

        print(f"\nConcurrent requests: {requests}")
        print("-" * 75)

        print_result("Baseline", baseline)
        print_result("SingleFlight", optimized)

        print(
            f"Backend reduction : "
            f"{backend_reduction:.2f}%"
        )

        print(
            f"Execution speedup : "
            f"{speedup:.2f}x"
        )


if __name__ == "__main__":
    asyncio.run(main())
