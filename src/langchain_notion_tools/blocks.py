"""Helper utilities for working with Notion block payloads."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping, MutableMapping

from .exceptions import NotionConfigurationError

__all__ = [
    "MAX_BLOCKS",
    "MAX_TOTAL_TEXT_LENGTH",
    "ALLOWED_BLOCK_TYPES",
    "paragraph",
    "heading_1",
    "heading_2",
    "heading_3",
    "bulleted_list_item",
    "numbered_list_item",
    "to_do",
    "toggle",
    "callout",
    "quote",
    "code",
    "sanitize_blocks",
    "from_text",
]

MAX_BLOCKS = 50
MAX_TOTAL_TEXT_LENGTH = 4000

ALLOWED_BLOCK_TYPES = {
    "paragraph",
    "heading_1",
    "heading_2",
    "heading_3",
    "bulleted_list_item",
    "numbered_list_item",
    "to_do",
    "toggle",
    "callout",
    "quote",
    "code",
}


def _text_object(content: str) -> dict[str, Any]:
    return {
        "type": "text",
        "text": {"content": content},
    }


def _rich_text(text: str | Iterable[str]) -> list[dict[str, Any]]:
    if isinstance(text, str):
        segments = [text]
    else:
        segments = list(text)
    return [_text_object(segment) for segment in segments]


def paragraph(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": _rich_text(text),
        },
    }


def heading_1(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": _rich_text(text),
        },
    }


def heading_2(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": _rich_text(text),
        },
    }


def heading_3(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": _rich_text(text),
        },
    }


def bulleted_list_item(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": _rich_text(text),
        },
    }


def numbered_list_item(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {
            "rich_text": _rich_text(text),
        },
    }


def to_do(text: str, *, checked: bool = False) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "checked": checked,
            "rich_text": _rich_text(text),
        },
    }


def toggle(text: str, *, children: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": _rich_text(text),
        },
    }
    if children:
        payload["toggle"]["children"] = children
    return payload


def callout(text: str, *, icon: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": _rich_text(text),
        },
    }
    if icon:
        payload["callout"]["icon"] = icon
    return payload


def quote(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "quote",
        "quote": {
            "rich_text": _rich_text(text),
        },
    }


def code(text: str, *, language: str = "plain text") -> dict[str, Any]:
    return {
        "object": "block",
        "type": "code",
        "code": {
            "language": language,
            "rich_text": _rich_text(text),
        },
    }


def _collect_rich_text(block: Mapping[str, Any]) -> list[MutableMapping[str, Any]]:
    block_type = block.get("type")
    if block_type not in ALLOWED_BLOCK_TYPES:
        return []
    container = block.get(block_type)
    if not isinstance(container, MutableMapping):
        return []
    rich_text = container.get("rich_text")
    if isinstance(rich_text, list):
        return [item for item in rich_text if isinstance(item, MutableMapping)]
    return []


def sanitize_blocks(
    blocks: Iterable[Mapping[str, Any]],
    *,
    allow_code_links: bool = False,
) -> list[dict[str, Any]]:
    """Validate and sanitize a sequence of Notion block payloads."""

    sanitized: list[dict[str, Any]] = []
    total_text_length = 0

    for index, block in enumerate(blocks):
        if index >= MAX_BLOCKS:
            raise NotionConfigurationError(
                f"Too many blocks provided. Maximum allowed is {MAX_BLOCKS}."
            )
        block_type = block.get("type")
        if block_type not in ALLOWED_BLOCK_TYPES:
            raise NotionConfigurationError(
                f"Block type '{block_type}' is not permitted. Allowed types: {sorted(ALLOWED_BLOCK_TYPES)}"
            )
        block_copy = deepcopy(block)
        rich_text_items = _collect_rich_text(block_copy)
        for item in rich_text_items:
            text = item.get("text")
            if isinstance(text, MutableMapping):
                content = text.get("content", "")
                if isinstance(content, str):
                    total_text_length += len(content)
                if block_type == "code" and not allow_code_links:
                    text.pop("link", None)
        if total_text_length > MAX_TOTAL_TEXT_LENGTH:
            raise NotionConfigurationError(
                "Total text length across blocks exceeds the permitted limit."
            )
        sanitized.append(block_copy)
    return sanitized


def from_text(text: str) -> list[dict[str, Any]]:
    """Convert a lightweight markdown-esque text into Notion blocks."""

    lines = text.strip().splitlines()
    blocks: list[dict[str, Any]] = []
    in_code = False
    code_language = "plain text"
    code_buffer: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip()
        if line.startswith("```"):
            if in_code:
                blocks.append(code("\n".join(code_buffer), language=code_language))
                code_buffer.clear()
                in_code = False
                code_language = "plain text"
            else:
                in_code = True
                code_language = line.strip("`") or "plain text"
            continue
        if in_code:
            code_buffer.append(line)
            continue
        if line.startswith("# "):
            blocks.append(heading_1(line[2:].strip()))
        elif line.startswith("## "):
            blocks.append(heading_2(line[3:].strip()))
        elif line.startswith("### "):
            blocks.append(heading_3(line[4:].strip()))
        elif line.startswith("- "):
            blocks.append(bulleted_list_item(line[2:].strip()))
        elif line.startswith("1. "):
            blocks.append(numbered_list_item(line[3:].strip()))
        elif line.startswith("> "):
            blocks.append(quote(line[2:].strip()))
        elif line:
            blocks.append(paragraph(line))
    if code_buffer:
        blocks.append(code("\n".join(code_buffer), language=code_language))
    return blocks
