# MIT License
#
# Copyright (c) 2024 Dinesh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Configuration helpers for Notion client access."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Optional

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

# Accept both the intended environment variable names and the constant identifiers
# occasionally used in configuration samples.
_TOKEN_ENV_KEYS = (NOTION_API_TOKEN_ENV_VAR, "NOTION_API_TOKEN_ENV_VAR")
_DEFAULT_PARENT_KEYS = (
    NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR,
    "NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR",
)


class NotionClientSettings(BaseModel):
    """Validated configuration for accessing the Notion API."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    api_token: str = Field(
        ..., description="Notion integration token used for authentication."
    )
    default_parent_page_id: Optional[str] = Field(
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
    def _empty_parent_as_none(cls, value: Optional[str]) -> Optional[str]:
        if value == "":
            return None
        return value

    @classmethod
    def from_env(
        cls,
        env: Optional[Mapping[str, str]] = None,
    ) -> NotionClientSettings:
        """Load settings from environment variables."""

        source = env if env is not None else os.environ
        token = next(
            (
                value
                for key in _TOKEN_ENV_KEYS
                if (value := source.get(key)) is not None and value.strip()
            ),
            None,
        )
        if token is None:
            raise MissingNotionAPITokenError(
                "Missing Notion API token. Set the"
                f" {NOTION_API_TOKEN_ENV_VAR} environment variable."
            )
        default_parent = next(
            (
                value
                for key in _DEFAULT_PARENT_KEYS
                if (value := source.get(key)) is not None
            ),
            None,
        )
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
        api_token: Optional[str] = None,
        default_parent_page_id: Optional[str] = None,
        settings: Optional[NotionClientSettings] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> NotionClientSettings:
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
