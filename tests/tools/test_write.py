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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest
from langchain_core.tools import ToolException

from langchain_notion_tools.config import NotionClientSettings
from langchain_notion_tools.exceptions import NotionConfigurationError
from langchain_notion_tools.tools import write as write_module
from langchain_notion_tools.tools.write import NotionWriteTool


class DummyPagesAPI:
    def __init__(self) -> None:
        self.create_calls: list[Mapping[str, Any]] = []
        self.update_calls: list[Mapping[str, Any]] = []
        self.retrieve_calls: list[str] = []

    def create(self, **payload: Any) -> Mapping[str, Any]:
        self.create_calls.append(payload)
        return {
            "id": "page-created",
            "url": "https://notion.so/page-created",
        }

    def update(self, *, page_id: str, properties: Mapping[str, Any]) -> Mapping[str, Any]:
        record = {"page_id": page_id, "properties": properties}
        self.update_calls.append(record)
        return {"id": page_id, "url": f"https://notion.so/{page_id}"}

    def retrieve(self, *, page_id: str) -> Mapping[str, Any]:
        self.retrieve_calls.append(page_id)
        return {"id": page_id, "url": f"https://notion.so/{page_id}"}


class DummyBlocksChildrenAPI:
    def __init__(self) -> None:
        self.append_calls: list[Mapping[str, Any]] = []

    def append(self, **payload: Any) -> Mapping[str, Any]:
        self.append_calls.append(payload)
        return {"results": payload.get("children", [])}


class DummyBlocksAPI:
    def __init__(self) -> None:
        self.children = DummyBlocksChildrenAPI()


class DummyAsyncPagesAPI(DummyPagesAPI):
    async def create(self, **payload: Any) -> Mapping[str, Any]:
        return super().create(**payload)

    async def update(self, *, page_id: str, properties: Mapping[str, Any]) -> Mapping[str, Any]:
        return super().update(page_id=page_id, properties=properties)

    async def retrieve(self, *, page_id: str) -> Mapping[str, Any]:
        return super().retrieve(page_id=page_id)


class DummyAsyncBlocksChildrenAPI(DummyBlocksChildrenAPI):
    async def append(self, **payload: Any) -> Mapping[str, Any]:
        return super().append(**payload)


class DummyAsyncBlocksAPI:
    def __init__(self) -> None:
        self.children = DummyAsyncBlocksChildrenAPI()


class DummyClient:
    def __init__(self) -> None:
        self.pages = DummyPagesAPI()
        self.blocks = DummyBlocksAPI()


class DummyAsyncClient:
    def __init__(self) -> None:
        self.pages = DummyAsyncPagesAPI()
        self.blocks = DummyAsyncBlocksAPI()


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
    assert (
        result["summary"]
        == "Created page under page parent-1 with title 'Test Page' (1 block(s); properties: title)."
    )
    payload = write_tool._client.pages.create_calls[0]
    assert payload["parent"] == {"type": "page_id", "page_id": "parent-1"}
    assert payload["properties"]["title"]["title"][0]["text"]["content"] == "Test Page"
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
    assert (
        result["summary"]
        == "Dry run: would create page under page parent-1 with title 'Plan' (0 block(s); properties: title)."
    )
    assert write_tool._client.pages.create_calls == []


def test_update_not_supported_yet(write_tool: NotionWriteTool) -> None:
    with pytest.raises(NotionConfigurationError):
        write_tool._run(update={"page_id": "page-1", "mode": "append"})


def test_append_update_mode(write_tool: NotionWriteTool) -> None:
    blocks = [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Hello"}}]}}]
    result = write_tool._run(update={"page_id": "page-42", "mode": "append"}, blocks=blocks)
    assert result["action"] == "updated"
    assert result["summary"] == "Appended 1 block(s) on page page-42."
    assert result["url"] == "https://notion.so/page-42"
    append_call = write_tool._client.blocks.children.append_calls[0]
    assert append_call["block_id"] == "page-42"
    assert append_call["children"][0]["paragraph"]["rich_text"][0]["text"]["content"] == "Hello"
    assert "replace" not in append_call
    assert write_tool._client.pages.retrieve_calls[-1] == "page-42"


def test_replace_update_mode_sets_replace_flag(write_tool: NotionWriteTool) -> None:
    result = write_tool._run(
        update={"page_id": "page-99", "mode": "replace"},
        blocks=[{"object": "block", "type": "quote", "quote": {"rich_text": [{"type": "text", "text": {"content": "Quote"}}]}}],
    )
    assert result["action"] == "updated"
    assert result["summary"] == "Replaced content with 1 block(s) on page page-99."
    assert result["url"] == "https://notion.so/page-99"
    append_call = write_tool._client.blocks.children.append_calls[-1]
    assert append_call["replace"] is True
    assert write_tool._client.pages.retrieve_calls[-1] == "page-99"


def test_update_properties_only(write_tool: NotionWriteTool) -> None:
    result = write_tool._run(
        update={"page_id": "page-props", "mode": "append"},
        properties={"Status": {"select": {"name": "Done"}}},
    )
    assert result["action"] == "updated"
    assert result["summary"] == "Updated properties (Status) on page page-props."
    assert result["url"] == "https://notion.so/page-props"
    update_call = write_tool._client.pages.update_calls[0]
    assert update_call["page_id"] == "page-props"
    assert update_call["properties"]["Status"]["select"]["name"] == "Done"
    assert write_tool._client.pages.retrieve_calls[-1] == "page-props"


def test_append_blocks_and_properties_summary(write_tool: NotionWriteTool) -> None:
    result = write_tool._run(
        update={"page_id": "page-both", "mode": "append"},
        blocks=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Body"}}]}}],
        properties={"Status": {"select": {"name": "In Progress"}}},
    )
    assert result["summary"] == "Appended 1 block(s) and updated properties (Status) on page page-both."
    assert result["url"] == "https://notion.so/page-both"
    assert write_tool._client.pages.retrieve_calls[-1] == "page-both"


def test_create_page_under_database(write_tool: NotionWriteTool) -> None:
    result = write_tool._run(
        parent={"database_id": "db-1"},
        properties={
            "Name": {
                "title": [
                    {"text": {"content": "Row"}},
                ]
            }
        },
    )
    assert result["action"] == "created"
    assert result["summary"] == "Created page under database db-1 with title 'untitled' (0 block(s); properties: Name)."


def test_code_block_links_removed(write_tool: NotionWriteTool) -> None:
    block = {
        "object": "block",
        "type": "code",
        "code": {
            "language": "python",
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": "print('hi')", "link": {"url": "https://example.com"}},
                }
            ],
        },
    }
    result = write_tool._run(update={"page_id": "page-code", "mode": "append"}, blocks=[block])
    assert result["action"] == "updated"
    assert result["summary"] == "Appended 1 block(s) on page page-code."
    assert result["url"] == "https://notion.so/page-code"
    append_call = write_tool._client.blocks.children.append_calls[-1]
    rich_text = append_call["children"][0]["code"]["rich_text"][0]["text"]
    assert "link" not in rich_text
    assert write_tool._client.pages.retrieve_calls[-1] == "page-code"

def test_update_properties_dry_run(write_tool: NotionWriteTool) -> None:
    result = write_tool._run(
        update={"page_id": "page-props-dry", "mode": "append"},
        properties={"Status": {"select": {"name": "Draft"}}},
        is_dry_run=True,
    )
    assert result["action"] == "dry_run"
    assert result["summary"] == "Dry run: would update properties (Status) on page page-props-dry."


def test_block_limit_enforced(write_tool: NotionWriteTool) -> None:
    blocks = [
        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": str(i)}}]}}
        for i in range(60)
    ]
    with pytest.raises(NotionConfigurationError):
        write_tool._run(update={"page_id": "page-many", "mode": "append"}, blocks=blocks)


def test_update_dry_run_summary(write_tool: NotionWriteTool) -> None:
    result = write_tool._run(
        update={"page_id": "page-dry", "mode": "append"},
        blocks=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Draft"}}]}}],
        is_dry_run=True,
    )
    assert result["action"] == "dry_run"
    assert result["summary"] == "Dry run: would append 1 block(s) on page page-dry."


def test_create_page_error_wrapped(write_tool: NotionWriteTool, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(**_: Any) -> None:
        raise RuntimeError("fail create")

    monkeypatch.setattr(write_tool._client.pages, "create", boom)
    with pytest.raises(ToolException) as excinfo:
        write_tool._run(title="Err", parent={"page_id": "p"})
    assert "Create page failed" in str(excinfo.value)


def test_update_blocks_error_wrapped(write_tool: NotionWriteTool, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(**_: Any) -> None:
        raise RuntimeError("fail blocks")

    monkeypatch.setattr(write_tool._client.blocks.children, "append", boom)
    with pytest.raises(ToolException) as excinfo:
        write_tool._run(update={"page_id": "page-x", "mode": "append"}, blocks=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}}])
    assert "Update page blocks failed" in str(excinfo.value)


def test_update_properties_error_wrapped(write_tool: NotionWriteTool, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*, page_id: str, properties: Mapping[str, Any]) -> None:  # type: ignore[override]
        raise RuntimeError(f"fail props {page_id}")

    monkeypatch.setattr(write_tool._client.pages, "update", boom)
    with pytest.raises(ToolException) as excinfo:
        write_tool._run(update={"page_id": "page-props", "mode": "append"}, properties={"Status": {"select": {"name": "Done"}}})
    assert "Update page properties failed" in str(excinfo.value)


def test_update_with_empty_properties_generates_no_changes_summary(
    write_tool: NotionWriteTool,
) -> None:
    result = write_tool._run(update={"page_id": "page-none", "mode": "append"}, properties={})
    assert result["summary"] == "No changes on page page-none."
    assert result["url"] == "https://notion.so/page-none"


def test_format_property_keys_variants() -> None:
    assert write_module._format_property_keys([]) == "no properties"
    assert write_module._format_property_keys(["A"]) == "properties: A"
    assert write_module._format_property_keys(["A", "B", "C", "D"]) == "properties: A, B, C, ..."


def test_write_raise_tool_error_includes_code_status() -> None:
    class BoomError(Exception):
        def __init__(self) -> None:
            super().__init__("boom")
            self.code = "invalid_request"
            self.status = 400

    with pytest.raises(ToolException) as excinfo:
        write_module._raise_tool_error("Create page", BoomError())
    message = str(excinfo.value)
    assert "code invalid_request" in message and "status 400" in message


def test_write_tool_settings_exposed(write_tool: NotionWriteTool) -> None:
    assert write_tool.settings.api_token == "token"


@pytest.mark.asyncio
async def test_async_create(write_tool: NotionWriteTool) -> None:
    result = await write_tool._arun(title="Async", parent={"page_id": "parent-async"})
    assert result["action"] == "created"
    assert result["url"] == "https://notion.so/page-created"
    async_calls = write_tool._async_client.pages.create_calls
    assert async_calls[0]["parent"] == {"type": "page_id", "page_id": "parent-async"}


@pytest.mark.asyncio
async def test_async_create_dry_run(write_tool: NotionWriteTool) -> None:
    result = await write_tool._arun(
        title="Async Dry",
        parent={"page_id": "parent-async-dry"},
        is_dry_run=True,
    )
    assert result["action"] == "dry_run"
    assert result["summary"].startswith("Dry run: would create page")


@pytest.mark.asyncio
async def test_async_append(write_tool: NotionWriteTool) -> None:
    result = await write_tool._arun(
        update={"page_id": "page-async", "mode": "append"},
        blocks=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}}],
    )
    assert result["action"] == "updated"
    assert result["url"] == "https://notion.so/page-async"
    append_calls = write_tool._async_client.blocks.children.append_calls
    assert append_calls[0]["block_id"] == "page-async"
    assert write_tool._async_client.pages.retrieve_calls[-1] == "page-async"


@pytest.mark.asyncio
async def test_async_create_error_wrapped(write_tool: NotionWriteTool, monkeypatch: pytest.MonkeyPatch) -> None:
    async def boom(**_: Any) -> None:
        raise RuntimeError("fail create async")

    monkeypatch.setattr(write_tool._async_client.pages, "create", boom)
    with pytest.raises(ToolException) as excinfo:
        await write_tool._arun(title="Err", parent={"page_id": "parent"})
    assert "Create page failed" in str(excinfo.value)


@pytest.mark.asyncio
async def test_async_update_error_wrapped(write_tool: NotionWriteTool, monkeypatch: pytest.MonkeyPatch) -> None:
    async def boom(**_: Any) -> None:
        raise RuntimeError("fail async append")

    monkeypatch.setattr(write_tool._async_client.blocks.children, "append", boom)
    with pytest.raises(ToolException) as excinfo:
        await write_tool._arun(
            update={"page_id": "page-async", "mode": "append"},
            blocks=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}}],
        )
    assert "Update page blocks failed" in str(excinfo.value)


@pytest.mark.asyncio
async def test_async_update_properties_error_wrapped(
    write_tool: NotionWriteTool, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def boom(*, page_id: str, properties: Mapping[str, Any]) -> None:  # type: ignore[override]
        raise RuntimeError(f"fail props {page_id}")

    monkeypatch.setattr(write_tool._async_client.pages, "update", boom)
    with pytest.raises(ToolException) as excinfo:
        await write_tool._arun(
            update={"page_id": "page-props", "mode": "append"},
            properties={"Status": {"select": {"name": "Done"}}},
        )
    assert "Update page properties failed" in str(excinfo.value)
