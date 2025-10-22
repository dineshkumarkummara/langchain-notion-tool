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
