"""Tool interfaces for Notion integration."""

from __future__ import annotations

from .search import NotionSearchInput, NotionSearchResult, NotionSearchTool
from .write import (
    NotionPageParent,
    NotionUpdateInstruction,
    NotionWriteInput,
    NotionWriteResult,
    NotionWriteTool,
)

__all__ = [
    "NotionSearchInput",
    "NotionSearchResult",
    "NotionSearchTool",
    "NotionPageParent",
    "NotionUpdateInstruction",
    "NotionWriteInput",
    "NotionWriteResult",
    "NotionWriteTool",
]
