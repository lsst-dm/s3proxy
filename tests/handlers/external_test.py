"""Tests for the s3proxy.handlers.external module and routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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
    """An allowed MIME type passes filtering and reaches the S3 backend."""
    # ``key.txt`` resolves to ``text/plain``, which is in the default
    # ``accept_mimetypes`` list, so the request proceeds to the S3 backend
    # and fails on missing credentials rather than being filtered out.
    with pytest.raises(NoCredentialsError):
        await client.get(
            "/s3proxy/s3/bucket/key.txt",
            headers={"X-Auth-Request-User": "test"},
        )


@pytest.mark.asyncio
async def test_get_s3_unknown_mimetype(client: AsyncClient) -> None:
    """A key with no guessable MIME type is rejected with 415."""
    response = await client.get(
        "/s3proxy/s3/bucket/key", headers={"X-Auth-Request-User": "test"}
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_get_s3_disallowed_mimetype(client: AsyncClient) -> None:
    """A known-but-not-allowed MIME type is rejected with 415."""
    # ``.exe`` maps to a MIME type that is not in ``accept_mimetypes``.
    response = await client.get(
        "/s3proxy/s3/bucket/installer.exe",
        headers={"X-Auth-Request-User": "test"},
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_get_s3_streams_png(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Allowed image objects are streamed to the client."""
    monkeypatch.setattr(config, "cache_max_age", 3600)

    mock_handle = MagicMock()
    mock_handle.read.side_effect = [b"tile-bytes", b""]

    mock_rp = MagicMock()
    mock_rp.open.return_value.__enter__.return_value = mock_handle
    mock_rp.open.return_value.__exit__.return_value = None

    with patch("s3proxy.handlers.external.ResourcePath", return_value=mock_rp):
        response = await client.get(
            "/s3proxy/s3/bucket/tile.png",
            headers={"X-Auth-Request-User": "test"},
        )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=3600"
    assert await response.aread() == b"tile-bytes"
    mock_rp.open.assert_called_once_with(mode="rb")


@pytest.mark.asyncio
async def test_get_s3_missing_object_returns_404(client: AsyncClient) -> None:
    """Missing S3 objects return 404 without starting a response body."""
    mock_rp = MagicMock()
    mock_rp.open.return_value.__enter__.side_effect = FileNotFoundError()

    with patch("s3proxy.handlers.external.ResourcePath", return_value=mock_rp):
        response = await client.get(
            "/s3proxy/s3/bucket/missing.png",
            headers={"X-Auth-Request-User": "test"},
        )

    assert response.status_code == 404
    assert "Not found" in response.json()["message"]

