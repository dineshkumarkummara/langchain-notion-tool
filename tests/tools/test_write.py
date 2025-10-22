from __future__ import annotations

from typing import Any, Dict, Mapping

import pytest

from langchain_notion_tools.config import NotionClientSettings
from langchain_notion_tools.exceptions import NotionConfigurationError
from langchain_notion_tools.tools.write import (
    NotionPageParent,
    NotionWriteInput,
    NotionWriteResult,
    NotionWriteTool,
)


class DummyPagesAPI:
    def __init__(self) -> None:
        self.create_calls: list[Mapping[str, Any]] = []

    def create(self, **payload: Any) -> Mapping[str, Any]:
        self.create_calls.append(payload)
        return {
            "id": "page-created",
            "url": "https://notion.so/page-created",
        }


class DummyAsyncPagesAPI(DummyPagesAPI):
    async def create(self, **payload: Any) -> Mapping[str, Any]:
        return super().create(**payload)


class DummyClient:
    def __init__(self) -> None:
        self.pages = DummyPagesAPI()


class DummyAsyncClient:
    def __init__(self) -> None:
        self.pages = DummyAsyncPagesAPI()


@pytest.fixture
def settings() -> NotionClientSettings:
    return NotionClientSettings(api_token="token")


@pytest.fixture
def write_tool(settings: NotionClientSettings) -> NotionWriteTool:
    return NotionWriteTool(settings=settings, client=DummyClient(), async_client=DummyAsyncClient())


def test_create_page_under_parent_page(write_tool: NotionWriteTool) -> None:
    parent = {"page_id": "parent-1"}
    blocks = [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}}]
    result = write_tool._run(title="Test Page", parent=parent, blocks=blocks)
    assert result["action"] == "created"
    assert result["page_id"] == "page-created"
    payload = write_tool._client.pages.create_calls[0]
    assert payload["parent"] == {"type": "page_id", "page_id": "parent-1"}
    assert payload["properties"]["title"][0]["text"]["content"] == "Test Page"
    assert payload["children"] == blocks


def test_create_page_requires_parent(write_tool: NotionWriteTool) -> None:
    with pytest.raises(NotionConfigurationError):
        write_tool._run(title="Only Title")


def test_database_parent_requires_properties(write_tool: NotionWriteTool) -> None:
    with pytest.raises(NotionConfigurationError):
        write_tool._run(parent={"database_id": "db-1"})


def test_dry_run_returns_summary(write_tool: NotionWriteTool) -> None:
    result = write_tool._run(
        title="Plan",
        parent={"page_id": "parent-1"},
        is_dry_run=True,
    )
    assert result["action"] == "dry_run"
    assert "Dry run" in result["summary"]
    assert write_tool._client.pages.create_calls == []


def test_update_not_supported_yet(write_tool: NotionWriteTool) -> None:
    with pytest.raises(NotionConfigurationError):
        write_tool._run(update={"page_id": "page-1", "mode": "append"})


@pytest.mark.asyncio
async def test_async_create(write_tool: NotionWriteTool) -> None:
    result = await write_tool._arun(title="Async", parent={"page_id": "parent-async"})
    assert result["action"] == "created"
    async_calls = write_tool._async_client.pages.create_calls
    assert async_calls[0]["parent"] == {"type": "page_id", "page_id": "parent-async"}
