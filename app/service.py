import asyncio
from typing import Any


class RecommendationService:
    """
    Simulates an expensive downstream service such as
    a database query or external API call.
    """

    def __init__(self):
        self.backend_calls = 0

    async def fetch_recommendations(
        self,
        product_id: str,
    ) -> dict[str, Any]:

        self.backend_calls += 1

        # Simulate expensive downstream work.
        await asyncio.sleep(0.2)

        return {
            "product_id": product_id,
            "recommendations": [
                "product-A",
                "product-B",
                "product-C",
            ],
            "backend_call_number": self.backend_calls,
        }

    def reset_metrics(self) -> None:
        self.backend_calls = 0
