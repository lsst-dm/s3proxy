"""Configuration definition."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from safir.logging import LogLevel, Profile

__all__ = ["Config", "config"]


class Config(BaseSettings):
    """Configuration for s3proxy."""

    name: str = Field("s3proxy", title="Name of application")

    path_prefix: str = Field("/s3proxy", title="URL prefix for application")

    profile: Profile = Field(
        Profile.development, title="Application logging profile"
    )

    log_level: LogLevel = Field(
        LogLevel.INFO, title="Log level of the application's logger"
    )

    accept_mimetypes: list[str] = Field(
        [
            "text/csv",
            "image/gif",
            "text/html",
            "image/jpeg",
            "text/javascript",
            "application/json",
            "audio/mpeg",
            "video/mp4",
            "video/mpeg",
            "audio/ogg",
            "video/ogg",
            "application/ogg",
            "image/png",
            "application/pdf",
            "image/svg+xml",
            "image/tiff",
            "text/plain",
            "audio/wav",
            "audio/webm",
            "video/webm",
            "image/webp",
        ],
        title="List of acceptable MIME types viewable directly in browsers",
    )

    also_allow_mimetypes: list[str] = Field(
        [], title="Additional allowed MIME types beyond default list"
    )

    disallow_mimetypes: list[str] = Field(
        [], title="MIME types to exclude, even if allowed by other lists"
    )

    stream_chunk_size: int = Field(
        262144,
        title="Chunk size in bytes when streaming object contents",
        ge=4096,
    )

    cache_max_age: int = Field(
        0,
        title=(
            "If greater than zero, send Cache-Control: public, max-age=N "
            "for image MIME types"
        ),
        ge=0,
    )

    @property
    def allowed_mimetypes(self) -> set[str]:
        """Resolved set of MIME types that may be served directly."""
        return (
            set(self.accept_mimetypes) | set(self.also_allow_mimetypes)
        ) - set(self.disallow_mimetypes)

    def cache_control_for(self, mimetype: str) -> str | None:
        """Return a Cache-Control header value for cacheable image types."""
        if self.cache_max_age <= 0:
            return None
        if not mimetype.startswith("image/"):
            return None
        return f"public, max-age={self.cache_max_age}"

    model_config = SettingsConfigDict(
        env_prefix="S3PROXY_", case_sensitive=False
    )


config = Config()
"""Configuration for s3proxy."""
