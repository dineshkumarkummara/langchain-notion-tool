"""Write tool implementation for Notion."""

from __future__ import annotations

import logging
from typing import Any, Mapping

from langchain_core.callbacks import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, ValidationError, model_validator

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


class NotionPageParent(BaseModel):
    """Parent reference for new Notion pages."""

    page_id: str | None = Field(default=None, description="Parent page identifier.")
    database_id: str | None = Field(
        default=None, description="Parent database identifier when creating database rows."
    )

    @model_validator(mode="after")
    def _validate_choice(self) -> "NotionPageParent":
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
    def _validate_mode(self) -> "NotionUpdateInstruction":
        if self.mode not in {"append", "replace"}:
            raise ValueError("mode must be either 'append' or 'replace'.")
        return self


class NotionWriteInput(BaseModel):
    """Inputs accepted by the Notion write tool."""

    title: str | None = Field(
        default=None,
        description="Title for the page. Required when creating under a page parent unless properties are provided.",
    )
    parent: NotionPageParent | None = Field(
        default=None,
        description="Parent reference. Required for create operations when update is not provided.",
    )
    blocks: list[Mapping[str, Any]] | None = Field(
        default=None,
        description="Optional list of Notion block payloads to include in the page.",
    )
    update: NotionUpdateInstruction | None = Field(
        default=None,
        description="Optional update instructions. Not yet supported for this revision.",
    )
    properties: Mapping[str, Any] | None = Field(
        default=None,
        description="Optional properties payload, required when writing to a database parent.",
    )
    is_dry_run: bool = Field(
        default=False,
        description="When true, render a preview summary without calling the Notion API.",
    )

    @model_validator(mode="after")
    def _validate_operation(self) -> "NotionWriteInput":
        if self.update is None and self.parent is None:
            raise ValueError("A parent is required when update instructions are not provided.")
        if self.update is not None and self.parent is not None:
            raise ValueError("Provide either parent for create or update instructions, not both.")
        if self.update is not None:
            # Update support is added in a subsequent iteration.
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
    page_id: str | None = Field(default=None, description="Identifier of the affected page.")
    url: str | None = Field(default=None, description="URL for the affected Notion page.")
    summary: str = Field(description="Human-readable summary of the performed action.")


class NotionWriteTool(BaseTool):
    """LangChain tool that creates or updates Notion content."""

    name = "notion_write"
    description = (
        "Create a new Notion page or update an existing one with structured blocks. "
        "Requires parent information for create operations."
    )
    args_schema: type[NotionWriteInput] = NotionWriteInput

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
        title: str | None = None,
        parent: Mapping[str, Any] | None = None,
        blocks: list[Mapping[str, Any]] | None = None,
        update: Mapping[str, Any] | None = None,
        properties: Mapping[str, Any] | None = None,
        is_dry_run: bool = False,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> dict[str, Any]:
        try:
            payload = self._coerce_payload(
                title=title,
                parent=parent,
                blocks=blocks,
                update=update,
                properties=properties,
                is_dry_run=is_dry_run,
            )
        except ValidationError as exc:  # pragma: no cover - handled by args_schema
            raise NotionConfigurationError(str(exc)) from exc

        result = self._execute_sync(payload)
        return result.model_dump()

    async def _arun(
        self,
        title: str | None = None,
        parent: Mapping[str, Any] | None = None,
        blocks: list[Mapping[str, Any]] | None = None,
        update: Mapping[str, Any] | None = None,
        properties: Mapping[str, Any] | None = None,
        is_dry_run: bool = False,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> dict[str, Any]:
        payload = self._coerce_payload(
            title=title,
            parent=parent,
            blocks=blocks,
            update=update,
            properties=properties,
            is_dry_run=is_dry_run,
        )
        result = await self._execute_async(payload)
        return result.model_dump()

    def _coerce_payload(
        self,
        *,
        title: str | None,
        parent: Mapping[str, Any] | None,
        blocks: list[Mapping[str, Any]] | None,
        update: Mapping[str, Any] | None,
        properties: Mapping[str, Any] | None,
        is_dry_run: bool,
    ) -> NotionWriteInput:
        parent_model = None
        if parent is not None:
            parent_model = NotionPageParent(**parent)
        update_model = None
        if update is not None:
            update_model = NotionUpdateInstruction(**update)
        return NotionWriteInput(
            title=title,
            parent=parent_model,
            blocks=blocks,
            update=update_model,
            properties=properties,
            is_dry_run=is_dry_run,
        )

    def _execute_sync(self, payload: NotionWriteInput) -> NotionWriteResult:
        if payload.update is not None:
            raise NotionConfigurationError(
                "Update operations are not supported yet; provide only parent for create operations."
            )
        logger.debug(
            "Creating Notion page (sync)",
            extra={
                "parent": payload.parent.describe() if payload.parent else None,
                "title": payload.title,
                "blocks_count": len(payload.blocks or []),
                "dry_run": payload.is_dry_run,
            },
        )
        create_payload = self._build_create_payload(payload)
        if payload.is_dry_run:
            summary = self._summarize_create(payload, create_payload)
            return NotionWriteResult(action="dry_run", page_id=None, url=None, summary=summary)

        response = self._client.pages.create(**create_payload)
        summary = self._summarize_create(payload, create_payload)
        return self._build_result(action="created", response=response, summary=summary)

    async def _execute_async(self, payload: NotionWriteInput) -> NotionWriteResult:
        if payload.update is not None:
            raise NotionConfigurationError(
                "Update operations are not supported yet; provide only parent for create operations."
            )
        logger.debug(
            "Creating Notion page (async)",
            extra={
                "parent": payload.parent.describe() if payload.parent else None,
                "title": payload.title,
                "blocks_count": len(payload.blocks or []),
                "dry_run": payload.is_dry_run,
            },
        )
        create_payload = self._build_create_payload(payload)
        if payload.is_dry_run:
            summary = self._summarize_create(payload, create_payload)
            return NotionWriteResult(action="dry_run", page_id=None, url=None, summary=summary)

        response = await self._async_client.pages.create(**create_payload)
        summary = self._summarize_create(payload, create_payload)
        return self._build_result(action="created", response=response, summary=summary)

    def _build_create_payload(self, payload: NotionWriteInput) -> Mapping[str, Any]:
        if payload.parent is None:
            raise NotionConfigurationError("Parent must be provided for create operations.")

        properties = dict(payload.properties or {})
        if payload.title and payload.parent.page_id:
            properties.setdefault(
                "title",
                [
                    {
                        "type": "text",
                        "text": {"content": payload.title},
                    }
                ],
            )
        api_payload: dict[str, Any] = {
            "parent": payload.parent.to_api_payload(),
            "properties": properties,
        }
        if payload.blocks:
            api_payload["children"] = list(payload.blocks)
        return api_payload

    def _summarize_create(
        self,
        payload: NotionWriteInput,
        create_payload: Mapping[str, Any],
    ) -> str:
        parent_desc = payload.parent.describe() if payload.parent else "parent not set"
        blocks_count = len(payload.blocks or [])
        return (
            f"Dry run: would create page under {parent_desc} with title '{payload.title or 'untitled'}'"
            f" and {blocks_count} block(s)."
        )

    def _build_result(
        self,
        *, action: str, response: Mapping[str, Any], summary: str
    ) -> NotionWriteResult:
        page_id = response.get("id")
        url = response.get("url")
        return NotionWriteResult(action=action, page_id=page_id, url=url, summary=summary)
