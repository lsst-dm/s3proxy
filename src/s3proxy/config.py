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

    disallow_mimetypes: list[str] | None = Field(
        [], title="MIME types to exclude, even if allowed by other lists"
    )

    model_config = SettingsConfigDict(
        env_prefix="S3PROXY_", case_sensitive=False
    )


config = Config()
"""Configuration for s3proxy."""
