"""MIME type guessing for S3 object keys."""

from __future__ import annotations

import mimetypes

from .config import Config, config

__all__ = ["guess_object_mimetype"]


def guess_object_mimetype(key: str, cfg: Config | None = None) -> str | None:
    """Guess the MIME type of an S3 object from its key.

    Uses the standard library guesser, then configured fallbacks for
    extensionless basenames and unrecognized suffixes.
    """
    settings = cfg or config

    mimetype, _encoding = mimetypes.guess_type(key)
    if mimetype is not None:
        return mimetype

    for suffix, mapped in sorted(
        settings.suffix_mimetypes.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if key.endswith(suffix):
            return mapped

    basename = key.rsplit("/", 1)[-1]
    return settings.extensionless_mimetypes.get(basename)
