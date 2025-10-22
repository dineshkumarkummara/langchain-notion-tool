from __future__ import annotations

from typing import Any, Dict, Mapping

import pytest

from langchain_notion_tools.config import NotionClientSettings
from langchain_notion_tools.exceptions import NotionConfigurationError
from langchain_notion_tools.tools import NotionSearchTool


def _page_result() -> Dict[str, Any]:
    return {
        "object": "page",
        "id": "page-123",
        "url": "https://notion.so/page-123",
        "parent": {"type": "database_id", "database_id": "db-1"},
        "properties": {
            "Title": {
                "type": "title",
                "title": [
                    {"plain_text": "Sample Page"},
                ],
            },
            "Summary": {
                "type": "rich_text",
                "rich_text": [
                    {"plain_text": "This is a preview snippet."},
                ],
            },
        },
    }


def _database_result() -> Dict[str, Any]:
    return {
        "object": "page",
        "id": "row-1",
        "url": "https://notion.so/row-1",
        "parent": {"type": "database_id", "database_id": "db-1"},
        "properties": {
            "Name": {
                "type": "title",
                "title": [
                    {"plain_text": "Database Row"},
                ],
            },
        },
    }


class DummyPagesAPI:
    def __init__(self, store: Mapping[str, Mapping[str, Any]]) -> None:
        self.store = store
        self.calls: list[str] = []

    def retrieve(self, *, page_id: str) -> Mapping[str, Any]:
        self.calls.append(page_id)
        return self.store[page_id]


class DummyDatabasesAPI:
    def __init__(self, result: Mapping[str, Any]) -> None:
        self.result = result
        self.calls: list[Mapping[str, Any]] = []

    def query(self, *, database_id: str, **kwargs: Any) -> Mapping[str, Any]:
        call = {"database_id": database_id, **kwargs}
        self.calls.append(call)
        return self.result


class DummySearchAPI:
    def __init__(self, result: Mapping[str, Any]) -> None:
        self.result = result
        self.calls: list[Mapping[str, Any]] = []

    def __call__(self, **kwargs: Any) -> Mapping[str, Any]:
        self.calls.append(kwargs)
        return self.result


class DummyAsyncPagesAPI(DummyPagesAPI):
    async def retrieve(self, *, page_id: str) -> Mapping[str, Any]:
        return super().retrieve(page_id=page_id)


class DummyAsyncDatabasesAPI(DummyDatabasesAPI):
    async def query(self, *, database_id: str, **kwargs: Any) -> Mapping[str, Any]:
        return super().query(database_id=database_id, **kwargs)


class DummyAsyncSearchAPI(DummySearchAPI):
    async def __call__(self, **kwargs: Any) -> Mapping[str, Any]:
        return super().__call__(**kwargs)


class DummyClient:
    def __init__(self, *, search_result: Mapping[str, Any], database_result: Mapping[str, Any]) -> None:
        self.pages = DummyPagesAPI({"page-123": _page_result()})
        self.databases = DummyDatabasesAPI(database_result)
        self.search = DummySearchAPI(search_result)


class DummyAsyncClient:
    def __init__(self, *, search_result: Mapping[str, Any], database_result: Mapping[str, Any]) -> None:
        self.pages = DummyAsyncPagesAPI({"page-123": _page_result()})
        self.databases = DummyAsyncDatabasesAPI(database_result)
        self.search = DummyAsyncSearchAPI(search_result)


@pytest.fixture
def settings() -> NotionClientSettings:
    return NotionClientSettings(api_token="token")


@pytest.fixture
def search_tool(settings: NotionClientSettings) -> NotionSearchTool:
    search_payload = {"results": [_page_result()]}
    database_payload = {"results": [_database_result()]}
    client = DummyClient(search_result=search_payload, database_result=database_payload)
    async_client = DummyAsyncClient(
        search_result=search_payload,
        database_result=database_payload,
    )
    return NotionSearchTool(
        settings=settings,
        client=client,
        async_client=async_client,
    )


def test_query_mode_returns_normalized_results(search_tool: NotionSearchTool) -> None:
    output = search_tool._run(query="doc", filter={"property": "Status"})
    assert len(output) == 1
    result = output[0]
    assert result["title"] == "Sample Page"
    assert result["object_type"] == "page"
    assert result["parent_id"] == "db-1"
    assert "preview" in result and "preview" in result["preview"]
    # Ensure filter was forwarded to Notion search API
    assert search_tool._client.search.calls[0] == {"query": "doc", "filter": {"property": "Status"}}


def test_database_mode_queries_database(search_tool: NotionSearchTool) -> None:
    output = search_tool._run(database_id="db-1", filter={"property": "Status"})
    assert len(output) == 1
    result = output[0]
    assert result["title"] == "Database Row"
    assert search_tool._client.databases.calls[0] == {
        "database_id": "db-1",
        "filter": {"property": "Status"},
    }


def test_page_mode_retrieves_single_page(search_tool: NotionSearchTool) -> None:
    output = search_tool._run(page_id="page-123")
    assert len(output) == 1
    result = output[0]
    assert result["id"] == "page-123"
    assert search_tool._client.pages.calls == ["page-123"]


def test_invalid_arguments_raise_configuration_error(search_tool: NotionSearchTool) -> None:
    with pytest.raises(NotionConfigurationError):
        search_tool._run()
    with pytest.raises(NotionConfigurationError):
        search_tool._run(query="a", page_id="page-123")
    with pytest.raises(NotionConfigurationError):
        search_tool._run(page_id="page-123", filter={"status": "Done"})


@pytest.mark.asyncio
async def test_async_query(search_tool: NotionSearchTool) -> None:
    results = await search_tool._arun(query="async")
    assert results[0]["title"] == "Sample Page"
    assert search_tool._async_client.search.calls[0] == {"query": "async"}
