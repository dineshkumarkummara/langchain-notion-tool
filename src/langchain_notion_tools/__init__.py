"""LangChain tools for Notion integration."""

from __future__ import annotations

from .blocks import (
    ALLOWED_BLOCK_TYPES,
    MAX_BLOCKS,
    MAX_TOTAL_TEXT_LENGTH,
    bulleted_list_item,
    callout,
    code,
    from_text,
    heading_1,
    heading_2,
    heading_3,
    numbered_list_item,
    paragraph,
    quote,
    sanitize_blocks,
    to_do,
    toggle,
)
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
    NotionAPIToolError,
    NotionConfigurationError,
    NotionIntegrationError,
)
from .toolkit import NotionToolkit, create_toolkit
from .tools import (
    NotionPageParent,
    NotionSearchInput,
    NotionSearchResult,
    NotionSearchTool,
    NotionUpdateInstruction,
    NotionWriteInput,
    NotionWriteResult,
    NotionWriteTool,
)

__all__ = [
    "__version__",
    "NotionClientBundle",
    "NotionClientSettings",
    "NotionConfigurationError",
    "NotionIntegrationError",
    "NotionAPIToolError",
    "MissingNotionAPITokenError",
    "NOTION_API_TOKEN_ENV_VAR",
    "NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR",
    "create_async_client",
    "create_client_bundle",
    "create_sync_client",
    "ALLOWED_BLOCK_TYPES",
    "MAX_BLOCKS",
    "MAX_TOTAL_TEXT_LENGTH",
    "bulleted_list_item",
    "callout",
    "code",
    "from_text",
    "heading_1",
    "heading_2",
    "heading_3",
    "NotionPageParent",
    "NotionSearchInput",
    "NotionSearchResult",
    "NotionSearchTool",
    "NotionUpdateInstruction",
    "NotionWriteInput",
    "NotionWriteResult",
    "NotionWriteTool",
    "numbered_list_item",
    "paragraph",
    "quote",
    "redact_token",
    "sanitize_blocks",
    "to_do",
    "toggle",
    "NotionToolkit",
    "create_toolkit",
]

__version__ = "0.1.0"
