"""LangChain tools for Notion integration."""

from __future__ import annotations

from .client import (
    NotionClientBundle,
    create_async_client,
    create_client_bundle,
    create_sync_client,
)
from .config import (
    NOTION_API_TOKEN_ENV_VAR,
    NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR,
    NotionClientSettings,
    redact_token,
)
from .exceptions import (
    MissingNotionAPITokenError,
    NotionConfigurationError,
    NotionIntegrationError,
)
from .tools import NotionSearchInput, NotionSearchResult, NotionSearchTool

__all__ = [
    "__version__",
    "NotionClientBundle",
    "NotionClientSettings",
    "NotionConfigurationError",
    "NotionIntegrationError",
    "MissingNotionAPITokenError",
    "NOTION_API_TOKEN_ENV_VAR",
    "NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR",
    "create_async_client",
    "create_client_bundle",
    "create_sync_client",
    "NotionSearchInput",
    "NotionSearchResult",
    "NotionSearchTool",
    "redact_token",
]

__version__ = "0.1.0"
