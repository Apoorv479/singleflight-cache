from fastapi import FastAPI

from app.cache import TTLCache
from app.coalescer import SingleFlight
from app.service import RecommendationService


app = FastAPI(
    title="SingleFlight Cache",
    description=(
        "Concurrency-aware request coalescing "
        "for preventing duplicate backend work."
    ),
    version="1.0.0",
)


cache = TTLCache(ttl=10)
singleflight = SingleFlight()
service = RecommendationService()


async def get_recommendations(product_id: str):

    key = f"recommendations:{product_id}"

    # 1. Check cache first.
    cached = cache.get(key)

    if cached is not None:
        return {
            "source": "cache",
            "data": cached,
        }

    # 2. Define expensive operation.
    async def expensive_operation():

        result = await service.fetch_recommendations(
            product_id
        )

        # 3. Cache the result.
        cache.set(key, result)

        return result

    # 4. Coalesce concurrent requests.
    result = await singleflight.do(
        key,
        expensive_operation,
    )

    return {
        "source": "backend",
        "data": result,
    }


@app.get("/products/{product_id}/recommendations")
async def recommendations(product_id: str):

    return await get_recommendations(product_id)


@app.get("/metrics")
async def metrics():

    return {
        "backend_calls": service.backend_calls,
        "cache_entries": cache.size(),
        "in_flight_requests": singleflight.in_flight_count(),
    }


@app.post("/metrics/reset")
async def reset_metrics():

    service.reset_metrics()
    cache.clear()

    return {
        "status": "reset",
    }


@app.get("/health")
async def health():

    return {
        "status": "ok",
      }
