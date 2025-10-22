"""Custom exceptions for langchain-notion-tools."""

from __future__ import annotations

__all__ = [
    "NotionIntegrationError",
    "NotionConfigurationError",
    "MissingNotionAPITokenError",
]


class NotionIntegrationError(Exception):
    """Base exception for langchain-notion-tools."""


class NotionConfigurationError(NotionIntegrationError):
    """Raised when the Notion integration is misconfigured."""


class MissingNotionAPITokenError(NotionConfigurationError):
    """Raised when the Notion API token is required but missing."""


class NotionAPIToolError(NotionIntegrationError):
    """Raised when the Notion API returns an error that should surface in tool output."""

    def __init__(self, message: str, *, status: int | None = None, code: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code

