"""MIME type guessing for S3 object keys."""

from __future__ import annotations

import mimetypes

__all__ = ["guess_object_mimetype"]

# HiPS and similar surveys use extensionless metadata files (IVOA HiPS REC).
_EXTENSIONLESS_MIMETYPES: dict[str, str] = {
    "properties": "text/plain",
}

# Suffixes that Python's mimetypes module does not recognize.
_SUFFIX_MIMETYPES: tuple[tuple[str, str], ...] = (
    (".fits.fz", "image/fits"),
    (".vot", "application/xml"),
)


def guess_object_mimetype(key: str) -> str | None:
    """Guess the MIME type of an S3 object from its key.

    Uses the standard library guesser, then applies Rubin- and IVOA-aware
    fallbacks for extensionless HiPS metadata files and common astronomy
    suffixes.
    """
    mimetype, _encoding = mimetypes.guess_type(key)
    if mimetype is not None:
        return mimetype

    for suffix, mapped in _SUFFIX_MIMETYPES:
        if key.endswith(suffix):
            return mapped

    basename = key.rsplit("/", 1)[-1]
    return _EXTENSIONLESS_MIMETYPES.get(basename)
