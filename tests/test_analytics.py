import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    # Use lifespan context manager so startup events (Redis init) trigger automatically
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        # Trigger startup handlers explicitly if using lifespan context
        async with app.router.lifespan_context(app):
            response = await ac.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_analytics_cache_flow():
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        async with app.router.lifespan_context(app):
            # First request - loads database or existing cache
            res1 = await ac.get("/analytics/summary")
            assert res1.status_code == 200
            assert "source" in res1.json()

            # Second request - must hit Redis cache
            res2 = await ac.get("/analytics/summary")
            assert res2.status_code == 200
            assert res2.json()["source"] == "cache"