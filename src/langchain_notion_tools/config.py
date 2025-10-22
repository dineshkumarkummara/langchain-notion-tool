"""Configuration helpers for Notion client access."""

from __future__ import annotations

import os
from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .exceptions import MissingNotionAPITokenError, NotionConfigurationError

__all__ = [
    "NOTION_API_TOKEN_ENV_VAR",
    "NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR",
    "NotionClientSettings",
    "redact_token",
]

NOTION_API_TOKEN_ENV_VAR = "NOTION_API_TOKEN"
NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR = "NOTION_DEFAULT_PARENT_PAGE_ID"


class NotionClientSettings(BaseModel):
    """Validated configuration for accessing the Notion API."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    api_token: str = Field(
        ..., description="Notion integration token used for authentication."
    )
    default_parent_page_id: str | None = Field(
        default=None,
        description="Optional fallback parent page ID used when creating pages.",
    )
    client_timeout: float = Field(
        default=30.0,
        ge=1.0,
        description="Timeout (seconds) applied to Notion HTTP requests.",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts for transient Notion API errors.",
    )

    @field_validator("api_token")
    @classmethod
    def _ensure_token_present(cls, value: str) -> str:
        if not value:
            raise MissingNotionAPITokenError(
                "Notion API token is required. Provide it explicitly or set"
                f" the {NOTION_API_TOKEN_ENV_VAR} environment variable."
            )
        return value

    @field_validator("default_parent_page_id")
    @classmethod
    def _empty_parent_as_none(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
    ) -> "NotionClientSettings":
        """Load settings from environment variables."""

        source = env if env is not None else os.environ
        token = source.get(NOTION_API_TOKEN_ENV_VAR)
        if token is None or not token.strip():
            raise MissingNotionAPITokenError(
                "Missing Notion API token. Set the"
                f" {NOTION_API_TOKEN_ENV_VAR} environment variable."
            )
        default_parent = source.get(NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR)
        try:
            timeout = float(source.get("NOTION_API_TIMEOUT", "30"))
        except ValueError as exc:  # pragma: no cover - env validation
            raise NotionConfigurationError("NOTION_API_TIMEOUT must be numeric.") from exc
        try:
            retries = int(source.get("NOTION_API_MAX_RETRIES", "3"))
        except ValueError as exc:  # pragma: no cover - env validation
            raise NotionConfigurationError("NOTION_API_MAX_RETRIES must be an integer.") from exc
        return cls(
            api_token=token,
            default_parent_page_id=default_parent,
            client_timeout=timeout,
            max_retries=retries,
        )

    @classmethod
    def resolve(
        cls,
        *,
        api_token: str | None = None,
        default_parent_page_id: str | None = None,
        settings: "NotionClientSettings" | None = None,
        env: Mapping[str, str] | None = None,
    ) -> "NotionClientSettings":
        """Resolve settings from explicit values, existing settings, or env."""

        base = settings
        if base is None:
            if api_token is not None:
                base = cls(
                    api_token=api_token,
                    default_parent_page_id=default_parent_page_id,
                )
            else:
                base = cls.from_env(env=env)
        if api_token is not None:
            base = base.model_copy(update={"api_token": api_token})
        if default_parent_page_id is not None:
            base = base.model_copy(
                update={"default_parent_page_id": default_parent_page_id}
            )
        return base

    def require_parent(self) -> str:
        """Return the default parent page ID or raise an error if missing."""

        if self.default_parent_page_id is None:
            raise NotionConfigurationError(
                "A parent page or database ID is required but missing."
            )
        return self.default_parent_page_id


def redact_token(token: str) -> str:
    """Redact a token value for safe logging."""

    stripped = token.strip()
    if not stripped:
        return ""
    if len(stripped) <= 4:
        return "*" * len(stripped)
    hidden = "*" * (len(stripped) - 4)
    return f"{hidden}{stripped[-4:]}"
