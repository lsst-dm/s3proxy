"""Tests for s3proxy.mimetype."""

from __future__ import annotations

from s3proxy.mimetype import guess_object_mimetype


def test_guess_object_mimetype_properties() -> None:
    """HiPS properties files have no extension but are plain text."""
    assert (
        guess_object_mimetype(
            "LSSTCam/runs/DRP/DP2/cosmost2/color_gri/properties"
        )
        == "text/plain"
    )


def test_guess_object_mimetype_fits() -> None:
    """FITS files are recognized for HiPS MOC and metadata."""
    assert guess_object_mimetype("Moc.fits") == "image/fits"
    assert guess_object_mimetype("metadata.fits") == "image/fits"


def test_guess_object_mimetype_compressed_fits() -> None:
    """Compressed FITS uses a fallback suffix mapping."""
    assert guess_object_mimetype("image.fits.fz") == "image/fits"


def test_guess_object_mimetype_votable() -> None:
    """VOTable files use an XML MIME type."""
    assert guess_object_mimetype("metadata.vot") == "application/xml"


def test_guess_object_mimetype_unknown() -> None:
    """Unrecognized keys remain unknown."""
    assert guess_object_mimetype("bucket/key") is None
    assert guess_object_mimetype("data.parquet") is None
