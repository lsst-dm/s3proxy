"""Handlers for the app's external root, ``/s3proxy/``."""

from __future__ import annotations

import mimetypes
import time
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from lsst.resources import ResourcePath
from safir.dependencies.gafaelfawr import auth_logger_dependency
from safir.metadata import get_metadata
from starlette.concurrency import iterate_in_threadpool
from structlog.stdlib import BoundLogger

from ..config import config
from ..models import Index

__all__ = ["get_index", "get_s3", "external_router"]

external_router = APIRouter()
"""FastAPI router for all external handlers."""


@external_router.get(
    "/",
    description=(
        "Document the top-level API here. By default it only returns metadata"
        " about the application."
    ),
    response_model=Index,
    response_model_exclude_none=True,
    summary="Application metadata",
)
async def get_index(
    logger: Annotated[BoundLogger, Depends(auth_logger_dependency)],
) -> Index:
    """GET ``/s3proxy/`` (the app's external root).

    Customize this handler to return whatever the top-level resource of your
    application should return. For example, consider listing key API URLs.
    When doing so, also change or customize the response model in
    `s3proxy.models.Index`.

    By convention, the root of the external API includes a field called
    ``metadata`` that provides the same Safir-generated metadata as the
    internal root endpoint.
    """
    # There is no need to log simple requests since uvicorn will do this
    # automatically, but this is included as an example of how to use the
    # logger for more complex logging.
    logger.info("Request for application metadata")

    metadata = get_metadata(
        package_name="s3proxy",
        application_name=config.name,
    )
    return Index(metadata=metadata)


def _iter_object_chunks(
    resource_path: ResourcePath,
    chunk_size: int,
    logger: BoundLogger,
    path: str,
) -> Iterator[bytes]:
    """Read an object in chunks and log timing when the stream completes."""
    started = time.perf_counter()
    bytes_sent = 0
    try:
        with resource_path.open(mode="rb") as handle:
            while True:
                chunk = handle.read(chunk_size)
                if not chunk:
                    break
                bytes_sent += len(chunk)
                yield chunk
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000)
        logger.info(
            "s3 response",
            path=path,
            duration_ms=duration_ms,
            bytes_sent=bytes_sent,
        )


@external_router.get(
    "/s3/{bucket}/{key:path}",
    description=(
        "Return an S3 object's contents.  ``bucket`` can contain ``profile@``."
    ),
    summary="Object contents",
    response_model=None,
)
async def get_s3(
    bucket: str,
    key: str,
    logger: Annotated[BoundLogger, Depends(auth_logger_dependency)],
) -> StreamingResponse | JSONResponse:
    """GET ``/s3proxy/s3/{bucket}/{key:path}``.

    This returns the contents of an s3 object
    """
    logger.debug("s3 request", bucket=bucket, key=key)

    path = f"s3://{bucket}/{key}"
    mimetype, _encoding = mimetypes.guess_type(path)
    if mimetype is None or mimetype not in config.allowed_mimetypes:
        return JSONResponse(
            status_code=415,  # Unsupported Media Type
            content={
                "message": f"Media type {mimetype} is not browsable: {path}"
            },
        )

    resource_path = ResourcePath(path)
    headers: dict[str, str] = {}
    if cache_control := config.cache_control_for(mimetype):
        headers["Cache-Control"] = cache_control

    try:
        chunk_iter = _iter_object_chunks(
            resource_path,
            config.stream_chunk_size,
            logger,
            path,
        )
        first_chunk = next(chunk_iter)

        def body() -> Iterator[bytes]:
            yield first_chunk
            yield from chunk_iter

        return StreamingResponse(
            iterate_in_threadpool(body()),
            media_type=mimetype,
            headers=headers,
        )
    except FileNotFoundError:
        return JSONResponse(
            status_code=404, content={"message": f"Not found: {path}"}
        )
    except StopIteration:
        return StreamingResponse(
            iterate_in_threadpool(iter(())),
            media_type=mimetype,
            headers=headers,
        )
