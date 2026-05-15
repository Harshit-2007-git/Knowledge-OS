"""
Tests for the health check endpoint.
"""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Health endpoint should return 200 with app info."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
