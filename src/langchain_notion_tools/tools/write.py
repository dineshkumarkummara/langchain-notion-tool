"""Write tool implementation for Notion."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, Optional, cast

from langchain_core.callbacks import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field, ValidationError, model_validator

from ..blocks import sanitize_blocks
from ..client import create_async_client, create_sync_client
from ..config import NotionClientSettings
from ..exceptions import NotionConfigurationError

__all__ = [
    "NotionPageParent",
    "NotionUpdateInstruction",
    "NotionWriteInput",
    "NotionWriteResult",
    "NotionWriteTool",
]

logger = logging.getLogger(__name__)
tool_error_cls = cast(type[Exception], ToolException)


def _format_property_keys(keys: Sequence[str]) -> str:
    if not keys:
        return "no properties"
    preview = ", ".join(keys[:3])
    if len(keys) > 3:
        preview += ", ..."
    return f"properties: {preview}"


def _raise_tool_error(operation: str, error: Exception) -> None:
    message = f"{operation} failed: {error}"
    status = getattr(error, "status", None)
    code = getattr(error, "code", None)
    if code:
        message += f" (code {code})"
    if status:
        message += f" [status {status}]"
    raise tool_error_cls(message) from error


class NotionPageParent(BaseModel):
    """Parent reference for new Notion pages."""

    page_id: Optional[str] = Field(default=None, description="Parent page identifier.")
    database_id: Optional[str] = Field(
        default=None, description="Parent database identifier when creating database rows."
    )

    @model_validator(mode="after")
    def _validate_choice(self) -> NotionPageParent:
        provided = [value for value in (self.page_id, self.database_id) if value]
        if len(provided) != 1:
            raise ValueError("Provide exactly one of 'page_id' or 'database_id' for parent.")
        return self

    def to_api_payload(self) -> Mapping[str, str]:
        if self.page_id:
            return {"type": "page_id", "page_id": self.page_id}
        if self.database_id:
            return {"type": "database_id", "database_id": self.database_id}
        raise NotionConfigurationError("Parent reference is not configured correctly.")

    def describe(self) -> str:
        if self.page_id:
            return f"page {self.page_id}"
        if self.database_id:
            return f"database {self.database_id}"
        return "unknown parent"


class NotionUpdateInstruction(BaseModel):
    """Update instructions for appending or replacing content on an existing page."""

    page_id: str = Field(description="Identifier of the page to update.")
    mode: str = Field(description="Update mode, expected to be 'append' or 'replace'.")

    @model_validator(mode="after")
    def _validate_mode(self) -> NotionUpdateInstruction:
        if self.mode not in {"append", "replace"}:
            raise ValueError("mode must be either 'append' or 'replace'.")
        return self


class NotionWriteInput(BaseModel):
    """Inputs accepted by the Notion write tool."""

    title: Optional[str] = Field(
        default=None,
        description="Title for the page. Required when creating under a page parent unless properties are provided.",
    )
    parent: Optional[NotionPageParent] = Field(
        default=None,
        description="Parent reference. Required for create operations when update is not provided.",
    )
    blocks: Optional[list[dict[str, object]]] = Field(
        default=None,
        description="Optional list of Notion block payloads to include in the page.",
    )
    update: Optional[NotionUpdateInstruction] = Field(
        default=None,
        description="Optional update instructions. Not yet supported for this revision.",
    )
    properties: Optional[dict[str, object]] = Field(
        default=None,
        description="Optional properties payload, required when writing to a database parent.",
    )
    is_dry_run: bool = Field(
        default=False,
        description="When true, render a preview summary without calling the Notion API.",
    )

    @model_validator(mode="after")
    def _validate_operation(self) -> NotionWriteInput:
        if self.update is None and self.parent is None:
            raise ValueError("A parent is required when update instructions are not provided.")
        if self.update is not None and self.parent is not None:
            raise ValueError("Provide either parent for create or update instructions, not both.")
        if self.update is not None:
            if self.blocks is None and self.properties is None:
                raise ValueError("Provide blocks and/or properties when using update instructions.")
            return self
        if self.parent is not None and self.parent.database_id and self.properties is None:
            raise ValueError("properties must be provided when parent is a database.")
        if self.parent is not None and self.parent.page_id and not self.title and self.properties is None:
            raise ValueError(
                "title or properties must be provided when creating under a page parent."
            )
        return self


class NotionWriteResult(BaseModel):
    """Structured output from the Notion write tool."""

    action: str = Field(description="Indicates whether the tool created, updated, or previewed content.")
    page_id: Optional[str] = Field(default=None, description="Identifier of the affected page.")
    url: Optional[str] = Field(default=None, description="URL for the affected Notion page.")
    summary: str = Field(description="Human-readable summary of the performed action.")


class NotionWriteTool(BaseTool):
    """LangChain tool that creates or updates Notion content."""

    name: str = "notion_write"
    description: str = (
        "Create a new Notion page or update an existing one with structured blocks. "
        "Requires parent information for create operations."
    )
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
        kwargs.setdefault("args_schema", NotionWriteInput)
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
        title: Optional[str] = None,
        parent: Optional[Mapping[str, Any]] = None,
        blocks: Optional[list[Mapping[str, Any]]] = None,
        update: Optional[Mapping[str, Any]] = None,
        properties: Optional[Mapping[str, Any]] = None,
        is_dry_run: bool = False,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> dict[str, Any]:
        blocks_list = [dict(block) for block in blocks] if blocks else None
        update_dict = dict(update) if update is not None else None
        properties_dict = dict(properties) if properties is not None else None

        try:
            payload = NotionWriteInput(
                title=title,
                parent=parent,
                blocks=blocks_list,
                update=update_dict,
                properties=properties_dict,
                is_dry_run=is_dry_run,
            )
        except ValidationError as exc:  # pragma: no cover - handled by args_schema
            raise NotionConfigurationError(str(exc)) from exc
        result = self._execute_sync(payload)
        return result.model_dump()

    async def _arun(
        self,
        title: Optional[str] = None,
        parent: Optional[Mapping[str, Any]] = None,
        blocks: Optional[list[Mapping[str, Any]]] = None,
        update: Optional[Mapping[str, Any]] = None,
        properties: Optional[Mapping[str, Any]] = None,
        is_dry_run: bool = False,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> dict[str, Any]:
        blocks_list = [dict(block) for block in blocks] if blocks else None
        update_dict = dict(update) if update is not None else None
        properties_dict = dict(properties) if properties is not None else None

        payload = NotionWriteInput(
            title=title,
            parent=parent,
            blocks=blocks_list,
            update=update_dict,
            properties=properties_dict,
            is_dry_run=is_dry_run,
        )
        result = await self._execute_async(payload)
        return result.model_dump()

    def _execute_sync(self, payload: NotionWriteInput) -> NotionWriteResult:
        if payload.update is not None:
            return self._handle_update_sync(payload)
        sanitized_blocks = self._sanitize_blocks(
            [cast(dict[str, Any], dict(block)) for block in payload.blocks]
            if payload.blocks
            else None
        )
        logger.debug(
            "Creating Notion page (sync)",
            extra={
                "parent": payload.parent.describe() if payload.parent else None,
                "title": payload.title,
                "blocks_count": len(sanitized_blocks),
                "dry_run": payload.is_dry_run,
            },
        )
        create_payload, property_keys = self._build_create_payload(payload, sanitized_blocks)
        if payload.is_dry_run:
            summary = self._summarize_create(
                payload,
                sanitized_blocks,
                property_keys,
                dry_run=True,
            )
            return NotionWriteResult(action="dry_run", page_id=None, url=None, summary=summary)

        try:
            response = self._client.pages.create(**create_payload)
        except Exception as exc:  # noqa: BLE001
            _raise_tool_error("Create page", exc)
        if not isinstance(response, Mapping):
            _raise_tool_error("Create page", TypeError("unexpected payload"))
        response_mapping = cast(Mapping[str, Any], response)
        summary = self._summarize_create(
            payload,
            sanitized_blocks,
            property_keys,
            dry_run=False,
        )
        return self._build_result(action="created", response=response_mapping, summary=summary)

    async def _execute_async(self, payload: NotionWriteInput) -> NotionWriteResult:
        if payload.update is not None:
            return await self._handle_update_async(payload)
        sanitized_blocks = self._sanitize_blocks(
            [cast(dict[str, Any], dict(block)) for block in payload.blocks]
            if payload.blocks
            else None
        )
        logger.debug(
            "Creating Notion page (async)",
            extra={
                "parent": payload.parent.describe() if payload.parent else None,
                "title": payload.title,
                "blocks_count": len(sanitized_blocks),
                "dry_run": payload.is_dry_run,
            },
        )
        create_payload, property_keys = self._build_create_payload(payload, sanitized_blocks)
        if payload.is_dry_run:
            summary = self._summarize_create(
                payload,
                sanitized_blocks,
                property_keys,
                dry_run=True,
            )
            return NotionWriteResult(action="dry_run", page_id=None, url=None, summary=summary)

        try:
            response = await self._async_client.pages.create(**create_payload)
        except Exception as exc:  # noqa: BLE001
            _raise_tool_error("Create page", exc)
        if not isinstance(response, Mapping):
            _raise_tool_error("Create page", TypeError("unexpected payload"))
        response_mapping = cast(Mapping[str, Any], response)
        summary = self._summarize_create(
            payload,
            sanitized_blocks,
            property_keys,
            dry_run=False,
        )
        return self._build_result(action="created", response=response_mapping, summary=summary)

    def _sanitize_blocks(
        self,
        blocks: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        if not blocks:
            return []
        return sanitize_blocks(blocks)

    def _build_create_payload(
        self,
        payload: NotionWriteInput,
        blocks: list[dict[str, Any]],
    ) -> tuple[Mapping[str, Any], list[str]]:
        if payload.parent is None:
            raise NotionConfigurationError("Parent must be provided for create operations.")

        properties_input = cast(Optional[dict[str, Any]], payload.properties)
        properties = dict(properties_input or {})
        if payload.title and payload.parent.page_id:
            properties.setdefault(
                "title",
                {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": payload.title},
                        }
                    ]
                },
            )
        property_keys = sorted(properties.keys())

        api_payload: dict[str, Any] = {
            "parent": payload.parent.to_api_payload(),
            "properties": properties,
        }
        if blocks:
            api_payload["children"] = blocks
        return api_payload, property_keys

    def _summarize_create(
        self,
        payload: NotionWriteInput,
        blocks: list[dict[str, Any]],
        property_keys: Sequence[str],
        *,
        dry_run: bool,
    ) -> str:
        parent_desc = payload.parent.describe() if payload.parent else "parent not set"
        blocks_count = len(blocks)
        action_phrase = "would create" if dry_run else "Created"
        prefix = "Dry run: " if dry_run else ""
        title = payload.title or "untitled"
        blocks_fragment = f"{blocks_count} block(s)"
        properties_fragment = _format_property_keys(property_keys)
        return (
            f"{prefix}{action_phrase} page under {parent_desc} with title '{title}'"
            f" ({blocks_fragment}; {properties_fragment})."
        )

    def _handle_update_sync(self, payload: NotionWriteInput) -> NotionWriteResult:
        assert payload.update is not None
        sanitized_blocks = self._sanitize_blocks(
            [cast(dict[str, Any], dict(block)) for block in payload.blocks]
            if payload.blocks
            else None
        )
        summary = self._summarize_update(payload, sanitized_blocks, dry_run=payload.is_dry_run)
        if payload.is_dry_run:
            return NotionWriteResult(
                action="dry_run",
                page_id=payload.update.page_id,
                url=None,
                summary=summary,
            )
        self._apply_update_sync(payload, sanitized_blocks)
        url = self._retrieve_page_url_sync(payload.update.page_id)
        return NotionWriteResult(
            action="updated",
            page_id=payload.update.page_id,
            url=url,
            summary=summary,
        )

    async def _handle_update_async(self, payload: NotionWriteInput) -> NotionWriteResult:
        assert payload.update is not None
        sanitized_blocks = self._sanitize_blocks(
            [cast(dict[str, Any], dict(block)) for block in payload.blocks]
            if payload.blocks
            else None
        )
        summary = self._summarize_update(payload, sanitized_blocks, dry_run=payload.is_dry_run)
        if payload.is_dry_run:
            return NotionWriteResult(
                action="dry_run",
                page_id=payload.update.page_id,
                url=None,
                summary=summary,
            )
        await self._apply_update_async(payload, sanitized_blocks)
        url = await self._retrieve_page_url_async(payload.update.page_id)
        return NotionWriteResult(
            action="updated",
            page_id=payload.update.page_id,
            url=url,
            summary=summary,
        )

    def _apply_update_sync(
        self,
        payload: NotionWriteInput,
        blocks: list[dict[str, Any]],
    ) -> None:
        assert payload.update is not None
        if payload.properties:
            try:
                self._client.pages.update(
                    page_id=payload.update.page_id,
                    properties=cast(dict[str, Any], payload.properties),
                )
            except Exception as exc:  # noqa: BLE001
                _raise_tool_error("Update page properties", exc)
        if blocks:
            params: dict[str, Any] = {
                "block_id": payload.update.page_id,
                "children": blocks,
            }
            if payload.update.mode == "replace":
                params["replace"] = True
            try:
                self._client.blocks.children.append(**params)
            except Exception as exc:  # noqa: BLE001
                _raise_tool_error("Update page blocks", exc)

    async def _apply_update_async(
        self,
        payload: NotionWriteInput,
        blocks: list[dict[str, Any]],
    ) -> None:
        assert payload.update is not None
        if payload.properties:
            try:
                await self._async_client.pages.update(
                    page_id=payload.update.page_id,
                    properties=cast(dict[str, Any], payload.properties),
                )
            except Exception as exc:  # noqa: BLE001
                _raise_tool_error("Update page properties", exc)
        if blocks:
            params: dict[str, Any] = {
                "block_id": payload.update.page_id,
                "children": blocks,
            }
            if payload.update.mode == "replace":
                params["replace"] = True
            try:
                await self._async_client.blocks.children.append(**params)
            except Exception as exc:  # noqa: BLE001
                _raise_tool_error("Update page blocks", exc)

    def _summarize_update(
        self,
        payload: NotionWriteInput,
        blocks: list[dict[str, Any]],
        *,
        dry_run: bool,
    ) -> str:
        assert payload.update is not None
        block_count = len(blocks)
        mode = payload.update.mode
        property_keys = sorted((payload.properties or {}).keys())
        properties_fragment = (
            f"properties ({', '.join(property_keys)})" if property_keys else "properties"
        )

        if block_count:
            if mode == "replace":
                future_phrase = f"replace content with {block_count} block(s)"
                past_phrase = f"Replaced content with {block_count} block(s)"
            else:
                future_phrase = f"append {block_count} block(s)"
                past_phrase = f"Appended {block_count} block(s)"
            if property_keys:
                future_phrase += f" and update {properties_fragment}"
                past_phrase += f" and updated {properties_fragment}"
        else:
            if property_keys:
                future_phrase = f"update {properties_fragment}"
                past_phrase = f"Updated {properties_fragment}"
            else:
                future_phrase = "make no changes"
                past_phrase = "No changes"

        if dry_run:
            return f"Dry run: would {future_phrase} on page {payload.update.page_id}."
        return f"{past_phrase} on page {payload.update.page_id}."

    def _retrieve_page_url_sync(self, page_id: str) -> Optional[str]:
        try:
            response = self._client.pages.retrieve(page_id=page_id)
        except Exception as exc:  # noqa: BLE001
            _raise_tool_error("Retrieve page", exc)
        if isinstance(response, Mapping):
            url = response.get("url")
            if isinstance(url, str):
                return url
        return None

    async def _retrieve_page_url_async(self, page_id: str) -> Optional[str]:
        try:
            response = await self._async_client.pages.retrieve(page_id=page_id)
        except Exception as exc:  # noqa: BLE001
            _raise_tool_error("Retrieve page", exc)
        if isinstance(response, Mapping):
            url = response.get("url")
            if isinstance(url, str):
                return url
        return None

    def _build_result(
        self,
        *, action: str, response: Mapping[str, Any], summary: str
    ) -> NotionWriteResult:
        page_id = response.get("id")
        url = response.get("url")
        return NotionWriteResult(action=action, page_id=page_id, url=url, summary=summary)
