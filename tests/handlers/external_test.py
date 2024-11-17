"""Tests for the s3proxy.handlers.external module and routes."""

from __future__ import annotations

import pytest
from botocore.exceptions import NoCredentialsError
from httpx import AsyncClient

from s3proxy.config import config


@pytest.mark.asyncio
async def test_get_index(client: AsyncClient) -> None:
    """Test ``GET /s3proxy/``."""
    response = await client.get(
        "/s3proxy/", headers={"X-Auth-Request-User": "test"}
    )
    assert response.status_code == 200
    data = response.json()
    metadata = data["metadata"]
    assert metadata["name"] == config.name
    assert isinstance(metadata["version"], str)
    assert isinstance(metadata["description"], str)
    assert isinstance(metadata["repository_url"], str)
    assert isinstance(metadata["documentation_url"], str)


@pytest.mark.asyncio
async def test_get_s3(client: AsyncClient) -> None:
    """Test ``GET /s3proxy/s3``."""
    with pytest.raises(NoCredentialsError):
        await client.get(
            "/s3proxy/s3/bucket/key", headers={"X-Auth-Request-User": "test"}
        )
