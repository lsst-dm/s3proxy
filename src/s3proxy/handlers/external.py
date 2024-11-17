"""Handlers for the app's external root, ``/s3proxy/``."""

import mimetypes
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from lsst.resources import ResourcePath
from safir.dependencies.logger import logger_dependency
from safir.metadata import get_metadata
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
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
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


@external_router.get(
    "/s3/{bucket}/{key:path}",
    description=(
        "Return an S3 object's contents.  ``bucket`` can contain ``profile@``."
    ),
    summary="Object contents",
)
async def get_s3(
    bucket: str,
    key: str,
    logger: Annotated[BoundLogger, Depends(logger_dependency)],
) -> Response:
    """GET ``/s3proxy/s3/{bucket}/{key:path}``.

    This returns the contents of an s3 object
    """
    path = f"s3://{bucket}/{key}"
    rp = ResourcePath(path)
    mimetype, encoding = mimetypes.guess_type(path)
    if mimetype is None:
        mimetype = "application/octet-stream"
    try:
        return Response(content=rp.read(), media_type=mimetype)
    except FileNotFoundError:
        return JSONResponse(
            status_code=404, content={"message": f"Not found: {path}"}
        )
