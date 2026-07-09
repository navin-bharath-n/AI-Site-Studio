"""
Unit tests for template marketplace routes.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.models.template import Template


@pytest.mark.asyncio
async def test_read_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_templates_empty(client: AsyncClient):
    response = await client.get("/api/v1/templates")
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0
