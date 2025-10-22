"""Toolkit factory for Notion tools."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Optional

from .client import NotionClientBundle, create_client_bundle
from .config import NotionClientSettings
from .tools import NotionSearchTool, NotionWriteTool

__all__ = ["NotionToolkit", "create_toolkit"]


@dataclass
class NotionToolkit:
    """Container bundling preconfigured Notion tools."""

    settings: NotionClientSettings
    bundle: NotionClientBundle
    search: NotionSearchTool
    write: NotionWriteTool

    @property
    def tools(self) -> Sequence[NotionSearchTool | NotionWriteTool]:
        return (self.search, self.write)


def create_toolkit(
    *,
    api_token: Optional[str] = None,
    default_parent_page_id: Optional[str] = None,
    settings: Optional[NotionClientSettings] = None,
    env: Optional[Mapping[str, str]] = None,
) -> NotionToolkit:
    """Build a NotionToolkit with shared clients for both tools."""

    resolved_settings = NotionClientSettings.resolve(
        api_token=api_token,
        default_parent_page_id=default_parent_page_id,
        settings=settings,
        env=env,
    )
    bundle = create_client_bundle(settings=resolved_settings)
    search = NotionSearchTool(settings=resolved_settings, client=bundle.client, async_client=bundle.async_client)
    write = NotionWriteTool(settings=resolved_settings, client=bundle.client, async_client=bundle.async_client)
    return NotionToolkit(settings=resolved_settings, bundle=bundle, search=search, write=write)
