"""Search tool implementation for Notion."""

from __future__ import annotations

import logging
from typing import Any, Iterable, Mapping

import httpx
from langchain_core.callbacks import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain_core.tools import BaseTool, ToolExecutionError
from pydantic import BaseModel, Field, ValidationError, model_validator

from ..client import create_async_client, create_sync_client
from ..config import NotionClientSettings
from ..exceptions import NotionConfigurationError

try:  # pragma: no cover - notion-client always installed in runtime
    from notion_client.errors import APIResponseError
except ImportError:  # pragma: no cover - safety for docs builds
    APIResponseError = Exception  # type: ignore[misc,assignment]

__all__ = [
    "NotionSearchInput",
    "NotionSearchResult",
    "NotionSearchTool",
]

logger = logging.getLogger(__name__)


def _raise_tool_error(operation: str, error: Exception) -> None:
    if isinstance(error, ToolExecutionError):  # pragma: no cover - defensive
        raise
    if isinstance(error, NotionConfigurationError):  # pragma: no cover - upstream
        raise
    message = f"{operation} failed: {error}"
    if isinstance(error, APIResponseError):
        status = getattr(error, "status", None)
        code = getattr(error, "code", None)
        if code:
            message += f" (code {code})"
        if status:
            message += f" [status {status}]"
    raise ToolExecutionError(message) from error


def _rich_text_to_plain_text(items: Iterable[Mapping[str, Any]]) -> str:
    return " ".join(
        piece.get("plain_text", "").strip()
        for piece in items
        if isinstance(piece, Mapping) and piece.get("plain_text")
    ).strip()


def _extract_title(data: Mapping[str, Any]) -> str:
    if "title" in data and isinstance(data["title"], list):
        title = _rich_text_to_plain_text(data["title"])
        if title:
            return title

    properties = data.get("properties")
    if isinstance(properties, Mapping):
        for prop in properties.values():
            if not isinstance(prop, Mapping):
                continue
            prop_type = prop.get("type")
            if prop_type == "title" and isinstance(prop.get("title"), list):
                title = _rich_text_to_plain_text(prop["title"])
                if title:
                    return title
            if prop_type == "rich_text" and isinstance(prop.get("rich_text"), list):
                title = _rich_text_to_plain_text(prop["rich_text"])
                if title:
                    return title
    return data.get("id", "")


def _extract_preview(data: Mapping[str, Any]) -> str | None:
    if "preview" in data and isinstance(data["preview"], str):
        return data["preview"].strip() or None

    if "properties" in data and isinstance(data["properties"], Mapping):
        for prop in data["properties"].values():
            if not isinstance(prop, Mapping):
                continue
            prop_type = prop.get("type")
            if prop_type == "rich_text" and isinstance(prop.get("rich_text"), list):
                preview = _rich_text_to_plain_text(prop["rich_text"])
                if preview:
                    return preview
    return None


def _extract_parent_id(parent: Any) -> str | None:
    if not isinstance(parent, Mapping):
        return None
    parent_type = parent.get("type")
    if parent_type == "page_id":
        return parent.get("page_id")
    if parent_type == "database_id":
        return parent.get("database_id")
    return None


class NotionSearchResult(BaseModel):
    """Normalized representation of a Notion search hit."""

    title: str = Field(description="Best-effort extracted title for the Notion object.")
    object_type: str = Field(description="Notion object type such as 'page' or 'database'.")
    id: str = Field(description="Identifier of the result object.")
    url: str | None = Field(default=None, description="URL to open the result in Notion.")
    parent_id: str | None = Field(
        default=None,
        description="Parent page or database identifier when available.",
    )
    preview: str | None = Field(
        default=None, description="Short text preview extracted from the object."
    )


class NotionSearchInput(BaseModel):
    """Inputs accepted by the Notion search tool."""

    query: str | None = Field(
        default=None,
        description="Full-text query passed to the Notion search endpoint.",
    )
    page_id: str | None = Field(
        default=None,
        description="Identifier of a specific page to retrieve.",
    )
    database_id: str | None = Field(
        default=None,
        description="Identifier of a database to query.",
    )
    filter: Mapping[str, Any] | None = Field(
        default=None,
        description=(
            "Optional filter payload forwarded to Notion's search or database query APIs."
        ),
    )

    @model_validator(mode="after")
    def _validate_target(cls, values: "NotionSearchInput") -> "NotionSearchInput":
        targets = [values.query, values.page_id, values.database_id]
        provided = sum(1 for target in targets if target)
        if provided != 1:
            raise ValueError(
                "Provide exactly one of 'query', 'page_id', or 'database_id'."
            )
        if values.page_id and values.filter is not None:
            raise ValueError("Filters cannot be used when retrieving a single page.")
        return values


class NotionSearchTool(BaseTool):
    """LangChain tool that exposes Notion search capabilities."""

    name = "notion_search"
    description = (
        "Search Notion for pages or databases, or retrieve a specific page or database."
        " Provide a full-text query, page_id, or database_id."
    )
    args_schema: type[NotionSearchInput] = NotionSearchInput

    def __init__(
        self,
        *,
        api_token: str | None = None,
        default_parent_page_id: str | None = None,
        settings: NotionClientSettings | None = None,
        client: Any | None = None,
        async_client: Any | None = None,
        env: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._settings = NotionClientSettings.resolve(
            api_token=api_token,
            default_parent_page_id=default_parent_page_id,
            settings=settings,
            env=env,
        )
        self._client = client or create_sync_client(settings=self._settings)
        self._async_client = async_client or create_async_client(settings=self._settings)

    @property
    def settings(self) -> NotionClientSettings:
        return self._settings

    def _run(
        self,
        query: str | None = None,
        page_id: str | None = None,
        database_id: str | None = None,
        filter: Mapping[str, Any] | None = None,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> list[dict[str, Any]]:
        try:
            payload = NotionSearchInput(
                query=query,
                page_id=page_id,
                database_id=database_id,
                filter=filter,
            )
        except ValidationError as exc:  # pragma: no cover - guarded by args_schema
            raise NotionConfigurationError(str(exc)) from exc

        results = self._search_sync(payload)
        return [result.model_dump() for result in results]

    async def _arun(
        self,
        query: str | None = None,
        page_id: str | None = None,
        database_id: str | None = None,
        filter: Mapping[str, Any] | None = None,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> list[dict[str, Any]]:
        payload = NotionSearchInput(
            query=query,
            page_id=page_id,
            database_id=database_id,
            filter=filter,
        )
        results = await self._search_async(payload)
        return [result.model_dump() for result in results]

    def _search_sync(self, payload: NotionSearchInput) -> list[NotionSearchResult]:
        client = self._client
        logger.debug(
            "Running Notion search (sync)",
            extra={
                "mode": self._identify_mode(payload),
                "query": payload.query,
                "page_id": payload.page_id,
                "database_id": payload.database_id,
            },
        )
        if payload.page_id:
            try:
                page = client.pages.retrieve(page_id=payload.page_id)
            except (APIResponseError, httpx.HTTPError, Exception) as exc:  # noqa: BLE001
                _raise_tool_error("Retrieve page", exc)
            return [self._normalize_result(page)]
        if payload.database_id:
            params: dict[str, Any] = {}
            if payload.filter is not None:
                params["filter"] = payload.filter
            try:
                response = client.databases.query(
                    database_id=payload.database_id,
                    **params,
                )
            except (APIResponseError, httpx.HTTPError, Exception) as exc:  # noqa: BLE001
                _raise_tool_error("Query database", exc)
            items = response.get("results", []) if isinstance(response, Mapping) else []
            return [self._normalize_result(item) for item in items]

        params = {"query": payload.query}
        if payload.filter is not None:
            params["filter"] = payload.filter
        try:
            response = client.search(**params)
        except (APIResponseError, httpx.HTTPError, Exception) as exc:  # noqa: BLE001
            _raise_tool_error("Search", exc)
        items = response.get("results", []) if isinstance(response, Mapping) else []
        return [self._normalize_result(item) for item in items]

    async def _search_async(self, payload: NotionSearchInput) -> list[NotionSearchResult]:
        client = self._async_client
        logger.debug(
            "Running Notion search (async)",
            extra={
                "mode": self._identify_mode(payload),
                "query": payload.query,
                "page_id": payload.page_id,
                "database_id": payload.database_id,
            },
        )
        if payload.page_id:
            try:
                page = await client.pages.retrieve(page_id=payload.page_id)
            except (APIResponseError, httpx.HTTPError, Exception) as exc:  # noqa: BLE001
                _raise_tool_error("Retrieve page", exc)
            return [self._normalize_result(page)]
        if payload.database_id:
            params: dict[str, Any] = {}
            if payload.filter is not None:
                params["filter"] = payload.filter
            try:
                response = await client.databases.query(
                    database_id=payload.database_id,
                    **params,
                )
            except (APIResponseError, httpx.HTTPError, Exception) as exc:  # noqa: BLE001
                _raise_tool_error("Query database", exc)
            items = response.get("results", []) if isinstance(response, Mapping) else []
            return [self._normalize_result(item) for item in items]

        params = {"query": payload.query}
        if payload.filter is not None:
            params["filter"] = payload.filter
        try:
            response = await client.search(**params)
        except (APIResponseError, httpx.HTTPError, Exception) as exc:  # noqa: BLE001
            _raise_tool_error("Search", exc)
        items = response.get("results", []) if isinstance(response, Mapping) else []
        return [self._normalize_result(item) for item in items]

    def _normalize_result(self, item: Mapping[str, Any]) -> NotionSearchResult:
        object_type = item.get("object", "unknown")
        identifier = item.get("id", "")
        title = _extract_title(item)
        preview = _extract_preview(item)
        url = item.get("url")
        parent_id = _extract_parent_id(item.get("parent"))
        return NotionSearchResult(
            title=title,
            object_type=object_type,
            id=identifier,
            url=url,
            parent_id=parent_id,
            preview=preview,
        )

    @staticmethod
    def _identify_mode(payload: NotionSearchInput) -> str:
        if payload.page_id:
            return "page"
        if payload.database_id:
            return "database"
        return "search"
